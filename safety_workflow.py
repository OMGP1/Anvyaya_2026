"""Human-reviewed dictionary coding and recorded recipient follow-up.

No licensed terms are bundled, no external model is called and no report is sent.
The HTTP caller owns authentication, the write lock and the transaction.
"""
import copy
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher
import hashlib
import re
import secrets


DICTIONARY_KINDS = ('Synthetic', 'MedDRA', 'WHODrug')
STOP_WORDS = {'a', 'an', 'the', 'and', 'after', 'reported', 'report', 'of', 'with', 'for'}


def _named(core, principal):
    if not isinstance(principal, dict) or not principal.get('user_id'):
        raise core.ApiError(403, 'Use an individual account for attributable dictionary or coding review.')
    return core.actor_id(principal)


def dictionary_metadata(dictionary):
    return {key: value for key, value in dictionary.items() if key != 'terms'}


def _coding_access(core, principal, study_id=None, review=False):
    if review:
        core.authorized(principal, 'report', study_id)
    else:
        core.authorized(principal, study_id=study_id)
        if not {'safety', 'report'}.intersection(principal.get('permissions', [])):
            raise core.ApiError(403, 'Safety workflow access is required.')


def list_dictionary_metadata(core, conn, principal):
    if 'settings' in principal.get('permissions', []):
        core.authorized(principal, 'settings')
    else:
        _coding_access(core, principal)
    return [dictionary_metadata(dictionary) for dictionary in core.rows(conn, 'dictionaries')]


def _ae_dictionary(core, conn, ident):
    dictionary = core.get(conn, 'dictionaries', ident)
    if dictionary['kind'] not in {'Synthetic', 'MedDRA'}:
        raise core.ApiError(400, 'WHODrug describes medicinal products and cannot code an adverse-event term here.')
    return dictionary


def _tokens(value):
    return [token for token in re.findall(r'\w+', value.casefold()) if token not in STOP_WORDS]


def suggest(core, conn, principal, event_id, dictionary_id):
    event = core.get(conn, 'events', event_id)
    _coding_access(core, principal, event['study_id'])
    dictionary = _ae_dictionary(core, conn, dictionary_id)
    source_tokens = _tokens(event['term'])
    source = ' '.join(source_tokens)
    candidates = []
    if source_tokens:
        source_set = set(source_tokens)
        for term in dictionary['terms']:
            candidate_tokens = _tokens(term['label'])
            candidate = ' '.join(candidate_tokens)
            if not candidate:
                continue
            overlap = len(source_set.intersection(candidate_tokens)) / len(source_set.union(candidate_tokens))
            score = 1.0 if source == candidate else 0.7 * overlap + 0.3 * SequenceMatcher(None, source, candidate, autojunk=False).ratio()
            if score >= 0.2:
                candidates.append({'code': term['code'], 'label': term['label'], 'lexical_similarity': round(score, 4)})
    candidates.sort(key=lambda term: (-term['lexical_similarity'], term['code']))
    return {'event_id': event_id, 'verbatim_term': event['term'], 'dictionary': dictionary_metadata(dictionary),
            'candidates': candidates[:5], 'abstained': not candidates, 'threshold': 0.2,
            'method': 'Deterministic lexical similarity; not clinical confidence or causality assessment.',
            'requires_human_review': True}


def _timestamp(core, data, key, allow_future=False):
    try:
        value = datetime.fromisoformat(core.text_field(data, key, 50).replace('Z', '+00:00'))
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError()
        value = value.astimezone(timezone.utc)
        if not allow_future and value > core.utcnow() + timedelta(seconds=30):
            raise ValueError()
        return value
    except (ValueError, OverflowError):
        raise core.ApiError(400, f'{key.replace("_", " ")} must be a timezone-aware timestamp' + ('.' if allow_future else ' that is not in the future.'))


def _parse(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)


def _eligible_assignee(core, user, study_id):
    return (user.get('active') is True and 'report' in core.ROLES[user['role']]['permissions']
            and (user.get('scope') is None or study_id in user['scope']))


def list_assignees(core, conn, principal, study_id):
    core.authorized(principal, 'report', study_id)
    core.get(conn, 'studies', study_id)
    return [{'id': user['id'], 'name': user['name'], 'role': user['role']}
            for user in core.rows(conn, 'users') if _eligible_assignee(core, user, study_id)]


def list_obligations(core, conn, principal):
    if principal.get('role') == 'leadership':
        return []
    scope = principal.get('scope')
    now = core.utcnow()
    result = []
    for obligation in core.rows(conn, 'obligations'):
        if scope is not None and obligation['study_id'] not in scope:
            continue
        result.append({**obligation, 'overdue': obligation['status'] != 'Acknowledged' and _parse(obligation['due_at']) < now})
    return result


def mutate(core, conn, principal, path, data):
    if path == '/api/dictionaries':
        actor = _named(core, principal)
        core.authorized(principal, 'settings')
        name = core.text_field(data, 'name', 120)
        version = core.text_field(data, 'version', 40)
        kind = core.choice(data, 'kind', DICTIONARY_KINDS)
        if kind != 'Synthetic' and data.get('licence_confirmed') is not True:
            raise core.ApiError(400, 'Confirm your institution has permission to use this supplied dictionary release.')
        if any(dictionary['name'].casefold() == name.casefold() and dictionary['version'].casefold() == version.casefold() and dictionary['kind'] == kind
               for dictionary in core.rows(conn, 'dictionaries')):
            raise core.ApiError(409, 'That immutable dictionary release is already imported. Use a new version.')
        supplied = data.get('terms')
        if not isinstance(supplied, list) or not 1 <= len(supplied) <= 2000:
            raise core.ApiError(400, 'Supply between 1 and 2,000 dictionary terms.')
        terms = []
        codes = set()
        for term in supplied:
            if not isinstance(term, dict):
                raise core.ApiError(400, 'Each dictionary term must have a code and label.')
            code = core.text_field(term, 'code', 80)
            label = core.text_field(term, 'label', 200)
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]*', code) or any(ord(char) < 32 for char in label):
                raise core.ApiError(400, 'Use a valid dictionary code and a plain text label.')
            if code in codes:
                raise core.ApiError(400, 'Dictionary codes must be unique within a release.')
            codes.add(code)
            terms.append({'code': code, 'label': label})
        terms.sort(key=lambda term: term['code'])
        dictionary = {'id': 'DICT-' + secrets.token_hex(6).upper(), 'name': name, 'version': version, 'kind': kind,
                      'terms': terms, 'term_count': len(terms), 'sha256': hashlib.sha256(core.canonical(terms).encode()).hexdigest(),
                      'licence_confirmed': kind != 'Synthetic', 'licence_verification': 'User declaration; not independently verified' if kind != 'Synthetic' else 'Synthetic terms only',
                      'imported_by': actor, 'imported_at': core.stamp()}
        core.save(conn, 'dictionaries', dictionary)
        metadata = dictionary_metadata(dictionary)
        core.audit(conn, actor, 'DICTIONARY_IMPORTED', dictionary['id'], after=metadata, reason='User-supplied immutable terminology release; no bundled licensed terms')
        return {'record': metadata}

    match = re.fullmatch(r'/api/safety/([A-Za-z0-9-]+)/coding', path)
    if match:
        actor = _named(core, principal)
        event = core.get(conn, 'events', match[1])
        _coding_access(core, principal, event['study_id'], review=True)
        dictionary = _ae_dictionary(core, conn, core.text_field(data, 'dictionary_id', 80))
        code = core.text_field(data, 'code', 80)
        term = next((term for term in dictionary['terms'] if term['code'] == code), None)
        if term is None:
            raise core.ApiError(400, 'Choose a code present in the selected dictionary release.')
        reason = core.text_field(data, 'reason', 1000)
        before = copy.deepcopy(event)
        if event.get('coded_term'):
            history = list(event.get('coding_history', []))
            history.append(copy.deepcopy(event['coded_term']))
            event['coding_history'] = history
        event['coded_term'] = {'dictionary_id': dictionary['id'], 'name': dictionary['name'], 'kind': dictionary['kind'],
                               'version': dictionary['version'], 'code': code, 'label': term['label'],
                               'reviewer': actor, 'reviewed_at': core.stamp()}
        event['coding'] = ('Reviewed synthetic coding' if dictionary['kind'] == 'Synthetic' else 'MedDRA coding recorded') + ' · ' + dictionary['version']
        core.save(conn, 'events', event)
        core.audit(conn, actor, 'SAFETY_CODING_REVIEWED', event['id'], event['study_id'], before, event, reason)
        return {'record': event}

    match = re.fullmatch(r'/api/safety/([A-Za-z0-9-]+)/obligations', path)
    if match:
        event = core.get(conn, 'events', match[1])
        core.authorized(principal, 'report', event['study_id'])
        recipient = ' '.join(core.text_field(data, 'recipient', 160).split())
        phase = core.choice(data, 'phase', ('initial', 'analysis'))
        if any(obligation['event_id'] == event['id'] and obligation['recipient'].casefold() == recipient.casefold() and obligation['phase'] == phase
               for obligation in core.rows(conn, 'obligations')):
            raise core.ApiError(409, 'A reporting obligation for this recipient and phase already exists.')
        assignee = core.get(conn, 'users', core.text_field(data, 'assignee_id', 80))
        if not _eligible_assignee(core, assignee, event['study_id']):
            raise core.ApiError(400, 'Assign an active named reporting user with access to this study.')
        due = _timestamp(core, data, 'due_at', allow_future=True)
        if due < _parse(event['occurred_at']):
            raise core.ApiError(400, 'The reporting deadline cannot precede event occurrence.')
        reason = core.text_field(data, 'reason', 1000)
        obligation = {'id': 'OBL-' + secrets.token_hex(6).upper(), 'event_id': event['id'], 'study_id': event['study_id'],
                      'recipient': recipient, 'phase': phase, 'assignee_id': assignee['id'], 'assignee_name': assignee['name'],
                      'due_at': core.stamp(due), 'rule_basis': reason, 'status': 'Awaiting dispatch',
                      'created_at': core.stamp(), 'created_by': core.actor_id(principal), 'escalations': [],
                      'delivery_mode': 'Manually recorded external dispatch and receipt; this application does not send reports'}
        core.save(conn, 'obligations', obligation)
        core.audit(conn, core.actor_id(principal), 'SAFETY_OBLIGATION_CREATED', obligation['id'], event['study_id'], after=obligation, reason=reason)
        return {'record': obligation}

    match = re.fullmatch(r'/api/obligations/(OBL-[A-Za-z0-9-]+)/(dispatch|receipt|escalate)', path)
    if match:
        obligation = core.get(conn, 'obligations', match[1])
        core.authorized(principal, 'report', obligation['study_id'])
        event = core.get(conn, 'events', obligation['event_id'])
        action = match[2]
        reason = core.text_field(data, 'reason', 1000)
        before = copy.deepcopy(obligation)
        actor = core.actor_id(principal)
        if action == 'dispatch':
            if obligation['status'] != 'Awaiting dispatch':
                raise core.ApiError(409, 'Dispatch is already recorded for this reporting obligation.')
            sent = _timestamp(core, data, 'sent_at')
            if sent < _parse(event['occurred_at']):
                raise core.ApiError(400, 'Dispatch cannot precede event occurrence.')
            reference = core.text_field(data, 'reference', 160)
            obligation.update(status='Awaiting receipt', sent_at=core.stamp(sent), dispatch_reference=reference,
                              dispatch_entered_at=core.stamp(), dispatch_recorded_by=actor)
        elif action == 'receipt':
            if obligation['status'] != 'Awaiting receipt':
                raise core.ApiError(409, 'Record dispatch first; an acknowledged receipt cannot be recorded twice.')
            received = _timestamp(core, data, 'received_at')
            if received < _parse(obligation['sent_at']):
                raise core.ApiError(400, 'Receipt cannot precede the recorded dispatch.')
            reference = core.text_field(data, 'reference', 160)
            obligation.update(status='Acknowledged', received_at=core.stamp(received), receipt_reference=reference,
                              receipt_entered_at=core.stamp(), receipt_recorded_by=actor)
        else:
            if obligation['status'] == 'Acknowledged':
                raise core.ApiError(409, 'An acknowledged obligation has no pending follow-up to escalate.')
            obligation['escalations'].append({'at': core.stamp(), 'actor': actor, 'reason': reason})
        core.save(conn, 'obligations', obligation)
        core.audit(conn, actor, 'SAFETY_OBLIGATION_' + action.upper() + '_RECORDED', obligation['id'], obligation['study_id'], before, obligation, reason)
        return {'record': obligation}

    return None
