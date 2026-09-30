"""Versioned evidence, independent review and recorded reconsent workflows.

The caller owns authentication, its write lock and the SQLite transaction.
File contents are never included in audit payloads or list responses.
"""
import base64
import binascii
import copy
import hashlib
import re
import secrets


MAX_FILE_BYTES = 512 * 1024
KINDS = ('Protocol', 'Consent', 'IEC')
LANGUAGES = ('English', 'Hindi', 'Marathi')


def _named(core, principal):
    if not isinstance(principal, dict) or not principal.get('user_id'):
        raise core.ApiError(403, 'Sign in with an individual account for attributable document review.')
    return core.actor_id(principal)


def metadata(document):
    return {key: value for key, value in document.items() if key != 'content_base64'}


def _can_read(core, principal, study_id):
    core.authorized(principal, study_id=study_id)
    if principal.get('role') == 'leadership':
        raise core.ApiError(403, 'Document access requires a study operations or review role.')


def list_documents(core, conn, principal):
    """Return metadata for documents visible within the current assignment."""
    if principal.get('role') == 'leadership':
        return []
    scope = principal.get('scope')
    return [metadata(document) for document in core.rows(conn, 'documents')
            if scope is None or document['study_id'] in scope]


def get_document(core, conn, principal, ident):
    document = core.get(conn, 'documents', ident)
    _can_read(core, principal, document['study_id'])
    return document


def _file(core, data):
    filename = core.text_field(data, 'filename', 120)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._ -]*\.(?:pdf|txt)', filename, re.I) or '..' in filename:
        raise core.ApiError(400, 'Use a safe PDF or TXT filename without folders or special characters.')
    encoded = data.get('content_base64')
    if not isinstance(encoded, str) or not encoded or len(encoded) > ((MAX_FILE_BYTES + 2) // 3) * 4:
        raise core.ApiError(400, 'Provide a non-empty PDF or UTF-8 text file no larger than 512 KiB.')
    try:
        content = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        raise core.ApiError(400, 'File content must be valid base64.')
    if not content or len(content) > MAX_FILE_BYTES:
        raise core.ApiError(400, 'File must contain between 1 byte and 512 KiB.')
    if filename.lower().endswith('.pdf'):
        if not re.match(br'%PDF-(?:1\.[0-7]|2\.0)(?:\r\n|\r|\n)', content) or not content.rstrip().endswith(b'%%EOF'):
            raise core.ApiError(400, 'PDF content must have a supported PDF header and end-of-file marker.')
        media_type = 'application/pdf'
    else:
        try:
            decoded = content.decode('utf-8')
        except UnicodeDecodeError:
            raise core.ApiError(400, 'TXT files must contain valid UTF-8 text.')
        if any(ord(char) < 32 and char not in '\t\r\n' for char in decoded) or '\x7f' in decoded or decoded.startswith('%PDF-'):
            raise core.ApiError(400, 'TXT files must contain text, without binary controls or PDF content.')
        media_type = 'text/plain; charset=utf-8'
    return filename, media_type, content


def _approved_documents(core, conn, principal, data, study_id):
    selected = {}
    for kind in KINDS:
        key = kind.lower() + '_document_id'
        document = core.get(conn, 'documents', core.text_field(data, key, 80))
        if document['study_id'] != study_id or document['kind'] != kind:
            raise core.ApiError(400, f'Select a {kind} document belonging to this study.')
        core.authorized(principal, study_id=document['study_id'])
        if document['status'] != 'Approved':
            raise core.ApiError(409, f'{kind} evidence must pass independent document review first.')
        selected[kind] = document
    return selected


def _amended_study(core, conn, principal, amendment, study):
    selected = _approved_documents(core, conn, principal, amendment, study['id'])
    updated = copy.deepcopy(study)
    updated.update(protocol=selected['Protocol']['version'], consent_version=selected['Consent']['version'])
    for key in ('iec_reference', 'iec_approved_at', 'iec_expiry', 'target'):
        updated[key] = amendment[key]
    updated['document_ids'] = {kind.lower(): selected[kind]['id'] for kind in KINDS}
    return updated


def mutate(core, conn, principal, path, data):
    """Handle one supported POST; return None for another module's endpoint."""
    if path == '/api/documents':
        actor = _named(core, principal)
        study_id = core.text_field(data, 'study_id', 80)
        core.authorized(principal, 'document', study_id)
        core.get(conn, 'studies', study_id)
        kind = core.choice(data, 'kind', KINDS)
        version = core.text_field(data, 'version', 30)
        if any(document['study_id'] == study_id and document['kind'] == kind and document['version'].casefold() == version.casefold()
               for document in core.rows(conn, 'documents')):
            raise core.ApiError(409, 'This document version already exists. Upload a new version to preserve the original.')
        filename, media_type, content = _file(core, data)
        document = {'id': 'DOC-' + secrets.token_hex(6).upper(), 'study_id': study_id,
                    'kind': kind, 'version': version, 'filename': filename, 'media_type': media_type,
                    'size': len(content), 'sha256': hashlib.sha256(content).hexdigest(),
                    'content_base64': base64.b64encode(content).decode('ascii'),
                    'status': 'Submitted', 'uploaded_at': core.stamp(), 'uploaded_by': actor}
        core.save(conn, 'documents', document)
        info = metadata(document)
        core.audit(conn, actor, 'DOCUMENT_SUBMITTED', document['id'], study_id, after=info,
                   reason='Versioned file evidence submitted for independent review; signature not validated')
        return {'record': info}

    match = re.fullmatch(r'/api/documents/(DOC-[A-Za-z0-9-]+)/review', path)
    if match:
        actor = _named(core, principal)
        document = core.get(conn, 'documents', match[1])
        core.authorized(principal, 'review', document['study_id'])
        if document['uploaded_by'] == actor:
            raise core.ApiError(403, 'A different individual account must review this document.')
        if document['status'] != 'Submitted':
            raise core.ApiError(409, 'This immutable document version has already been reviewed.')
        decision = core.choice(data, 'decision', ('Approved', 'Rejected'))
        reason = core.text_field(data, 'reason', 1000)
        before = metadata(document)
        document.update(status=decision, reviewed_at=core.stamp(), reviewed_by=actor, review_reason=reason)
        core.save(conn, 'documents', document)
        info = metadata(document)
        core.audit(conn, actor, 'DOCUMENT_' + decision.upper(), document['id'], document['study_id'], before, info, reason)
        return {'record': info}

    if path == '/api/amendments':
        actor = _named(core, principal)
        study_id = core.text_field(data, 'study_id', 80)
        core.authorized(principal, 'amend', study_id)
        study = core.get(conn, 'studies', study_id)
        if study['status'] not in {'Recruiting', 'Follow-up'}:
            raise core.ApiError(409, 'Amendments apply to recruiting or follow-up studies.')
        selected = _approved_documents(core, conn, principal, data, study_id)
        reference = core.text_field(data, 'iec_reference', 120)
        approved = core.calendar_date(data, 'iec_approved_at')
        expiry = core.calendar_date(data, 'iec_expiry')
        if expiry < approved:
            raise core.ApiError(400, 'IEC expiry must be on or after the approval date.')
        target = core.number(data, 'target', 1, 10000)
        enrolled = sum(participant['study_id'] == study_id for participant in core.rows(conn, 'participants'))
        if target < enrolled:
            raise core.ApiError(409, 'The amended target cannot be below the recorded enrolment count.')
        amendment = {'id': 'AMD-' + secrets.token_hex(6).upper(), 'study_id': study_id,
                     **{kind.lower() + '_document_id': selected[kind]['id'] for kind in KINDS},
                     'iec_reference': reference, 'iec_approved_at': approved, 'iec_expiry': expiry,
                     'target': target, 'reason': core.text_field(data, 'reason', 1000),
                     'study_revision': study.get('revision', 0), 'status': 'Submitted',
                     'submitted_at': core.stamp(), 'submitted_by': actor}
        updated = _amended_study(core, conn, principal, amendment, study)
        changed = any(updated[key] != study.get(key) for key in ('protocol', 'consent_version', 'iec_reference', 'iec_approved_at', 'iec_expiry', 'target'))
        if not changed:
            raise core.ApiError(409, 'The amendment must change a protocol, consent, IEC approval or enrolment target.')
        core.save(conn, 'amendments', amendment)
        core.audit(conn, actor, 'AMENDMENT_SUBMITTED', amendment['id'], study_id, after=amendment, reason=amendment['reason'])
        return {'record': amendment}

    match = re.fullmatch(r'/api/amendments/(AMD-[A-Za-z0-9-]+)/approve', path)
    if match:
        actor = _named(core, principal)
        amendment = core.get(conn, 'amendments', match[1])
        study_id = amendment['study_id']
        core.authorized(principal, 'review', study_id)
        if amendment['submitted_by'] == actor:
            raise core.ApiError(403, 'A different individual account must approve the amendment.')
        if amendment['status'] != 'Submitted':
            raise core.ApiError(409, 'This amendment has already been reviewed.')
        reason = core.text_field(data, 'reason', 1000)
        study = core.get(conn, 'studies', study_id)
        if study['status'] not in {'Recruiting', 'Follow-up'} or study.get('revision', 0) != amendment['study_revision']:
            raise core.ApiError(409, 'The study changed after submission. Submit a new amendment against its current revision.')
        participants = [participant for participant in core.rows(conn, 'participants') if participant['study_id'] == study_id]
        if amendment['target'] < len(participants):
            raise core.ApiError(409, 'Enrolment increased after submission; the amended target is now too low.')
        updated = _amended_study(core, conn, principal, amendment, study)
        blockers = [check['error'] for check in core.study_readiness(updated)['checks'] if not check['passed']]
        if blockers:
            raise core.ApiError(409, 'Amendment approval blocked: ' + ' '.join(blockers))
        updated.update(revision=study.get('revision', 0) + 1, updated_at=core.stamp(), last_amendment_id=amendment['id'])
        consent_changed = updated['consent_version'] != study.get('consent_version', study['protocol'])
        affected = []
        if consent_changed:
            for participant in participants:
                if participant['status'] != 'Enrolled' or participant.get('consent') is not True:
                    continue
                before_participant = copy.deepcopy(participant)
                participant.update(reconsent_required=True, required_consent_version=updated['consent_version'],
                                   reconsent_amendment_id=amendment['id'], reconsent_required_at=core.stamp())
                core.save(conn, 'participants', participant)
                core.audit(conn, actor, 'RECONSENT_REQUIRED', participant['id'], study_id,
                           before_participant, participant, 'Approved consent amendment ' + amendment['id'])
                affected.append(participant['id'])
        before_amendment = copy.deepcopy(amendment)
        amendment.update(status='Approved', reviewed_by=actor, reviewed_at=core.stamp(), review_reason=reason,
                         applied_revision=updated['revision'], reconsent_count=len(affected))
        core.save(conn, 'studies', updated)
        core.save(conn, 'amendments', amendment)
        core.audit(conn, actor, 'STUDY_AMENDED', study_id, study_id, study, updated, reason)
        core.audit(conn, actor, 'AMENDMENT_APPROVED', amendment['id'], study_id, before_amendment, amendment, reason)
        return {'record': amendment, 'study': updated, 'reconsent_count': len(affected)}

    match = re.fullmatch(r'/api/participants/([A-Za-z0-9-]+)/reconsent', path)
    if match:
        participant = core.get(conn, 'participants', match[1])
        study_id = participant['study_id']
        core.authorized(principal, 'enrol', study_id)
        if participant['status'] != 'Enrolled' or participant.get('consent') is not True:
            raise core.ApiError(409, 'Reconsent is unavailable for withdrawn or inactive participants.')
        if not participant.get('reconsent_required'):
            raise core.ApiError(409, 'This participant has no outstanding consent amendment.')
        study = core.get(conn, 'studies', study_id)
        version = core.text_field(data, 'consent_version', 30)
        if version != study.get('consent_version', study['protocol']):
            raise core.ApiError(409, 'Use the current approved consent version.')
        if data.get('consent') is not True:
            raise core.ApiError(400, 'Confirm that informed consent was obtained before recording reconsent.')
        language = core.choice(data, 'consent_language', LANGUAGES)
        reason = core.text_field(data, 'reason', 1000)
        before = copy.deepcopy(participant)
        history = list(participant.get('consent_history', []))
        history.append({key: participant.get(key) for key in ('consent', 'consent_version', 'consent_language', 'consent_at', 'consent_recorder')})
        actor = core.actor_id(principal)
        participant.update(consent_history=history, consent=True, consent_version=version,
                           consent_language=language, consent_at=core.stamp(), consent_recorder=actor,
                           reconsent_required=False, reconsented_at=core.stamp())
        participant.pop('required_consent_version', None)
        core.save(conn, 'participants', participant)
        core.audit(conn, actor, 'PARTICIPANT_RECONSENTED', participant['id'], study_id, before, participant, reason)
        return {'record': participant}

    return None
