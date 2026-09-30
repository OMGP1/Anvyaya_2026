"""Controlled synthetic CSV intake and inspectable export checks, not an EDC connector."""
import csv
import hashlib
import io
import json
import re
import secrets

FIELDS = ['external_id', 'age', 'sex', 'prakriti', 'consent_version', 'consent_language', 'consent_confirmed']


def summary(job):
    return {k: v for k, v in job.items() if k != 'rows'}


def validate_row(core, raw):
    if not re.fullmatch(r'[A-Za-z0-9._-]{1,80}', raw.get('external_id', '')):
        raise core.ApiError(400, 'External ID must contain 1–80 letters, digits, dots, underscores or hyphens.')
    if not re.fullmatch(r'[0-9]{1,3}', raw.get('age', '')):
        raise core.ApiError(400, 'Age must be a whole number.')
    payload = {**raw, 'age': int(raw['age'])}
    core.number(payload, 'age', 18, 100)
    core.choice(payload, 'sex', ['F', 'M', 'U'])
    core.choice(payload, 'prakriti', ['Vata-Pitta', 'Pitta-Kapha', 'Vata-Kapha', 'Balanced', 'Not assessed'])
    core.choice(payload, 'consent_language', ['English', 'Hindi', 'Marathi'])
    core.text_field(payload, 'consent_version', 30)
    if raw.get('consent_confirmed', '').lower() != 'true':
        raise core.ApiError(400, 'Consent must be explicitly confirmed as true.')
    payload['consent'] = True
    return payload


def preview(core, conn, actor, data):
    sid = core.text_field(data, 'study_id', 80)
    core.authorized(actor, 'import', sid)
    core.authorized(actor, 'enrol', sid)
    study = core.get(conn, 'studies', sid)
    source = core.text_field(data, 'source_name', 100)
    if data.get('synthetic') is not True:
        raise core.ApiError(400, 'This intake accepts synthetic demonstration records only.')
    core.text_field(data, 'csv_text', 100_000)
    text = data['csv_text']
    if len(text) > 100_000:
        raise core.ApiError(400, 'CSV text must be under 100 KB.')
    mapping = data.get('mapping') if 'mapping' in data else {key: key for key in FIELDS}
    if not isinstance(mapping, dict) or set(mapping) != set(FIELDS) or not all(isinstance(v, str) for v in mapping.values()) or len(set(mapping.values())) != len(FIELDS):
        raise core.ApiError(400, 'Map each required target field to one unique source column.')
    try:
        reader = csv.DictReader(io.StringIO(text.lstrip('\ufeff')), strict=True)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames) or not set(mapping.values()) <= set(reader.fieldnames):
            raise core.ApiError(400, 'CSV headers must be unique and include all mapped fields.')
        incoming = list(reader)
    except csv.Error:
        raise core.ApiError(400, 'Malformed CSV input.')
    if not 1 <= len(incoming) <= 100:
        raise core.ApiError(400, 'Import 1–100 rows per review batch.')
    existing = {p['provenance']['key']: p for p in core.rows(conn, 'participants') if p.get('provenance')}
    seen, staged = set(), []
    for index, row in enumerate(incoming, 2):
        item = {'line': index, 'status': 'Ready', 'error': '', 'external_id': ''}
        try:
            if None in row or any(v is None for v in row.values()):
                raise core.ApiError(400, 'Row has a different number of columns from the header.')
            raw = {key: row[value].strip() for key, value in mapping.items()}
            item['external_id'] = raw['external_id']
            payload = validate_row(core, raw)
            key = hashlib.sha256(core.canonical([source.casefold(), sid, raw['external_id']]).encode()).hexdigest()
            digest = hashlib.sha256(core.canonical(raw).encode()).hexdigest()
            if key in seen:
                raise core.ApiError(400, 'Duplicate external ID in this file.')
            seen.add(key)
            if raw['consent_version'] != study.get('consent_version', study['protocol']):
                raise core.ApiError(409, 'Consent version does not match the current study version.')
            if key in existing:
                if existing[key]['provenance']['row_sha256'] != digest:
                    raise core.ApiError(409, 'Source ID already imported with different values; reconcile the source before retrying.')
                item.update(status='Already imported', participant_id=existing[key]['id'])
            item.update(payload=payload, key=key, row_sha256=digest)
        except core.ApiError as error:
            item.update(status='Rejected', error=error.message)
        staged.append(item)
    job = {'id': 'IMP-' + secrets.token_hex(5).upper(), 'study_id': sid, 'source_name': source,
           'source_sha256': hashlib.sha256(text.encode()).hexdigest(), 'mapping': mapping,
           'created_at': core.stamp(), 'created_by': core.actor_id(actor), 'status': 'Preview',
           'rows': staged, 'total': len(staged), 'ready': sum(r['status'] == 'Ready' for r in staged),
           'rejected': sum(r['status'] == 'Rejected' for r in staged),
           'duplicates': sum(r['status'] == 'Already imported' for r in staged), 'synthetic': True}
    core.save(conn, 'imports', job)
    core.audit(conn, actor, 'IMPORT_PREVIEWED', job['id'], sid, after=summary(job), reason='Source mapped and validated; no participants inserted')
    return {'record': job}


def mutate(core, conn, actor, path, data, enrol):
    if path == '/api/imports/preview':
        return preview(core, conn, actor, data)
    match = re.fullmatch(r'/api/imports/(IMP-[A-F0-9]+)/commit', path)
    if not match:
        return None
    job = core.get(conn, 'imports', match[1])
    core.authorized(actor, 'import', job['study_id'])
    core.authorized(actor, 'enrol', job['study_id'])
    if job['status'] == 'Committed':
        return {'record': job, 'idempotent': True}
    if job['rejected']:
        raise core.ApiError(409, 'Fix rejected source rows and preview the corrected file before committing.')
    if data.get('reviewed') is not True:
        raise core.ApiError(400, 'Confirm source and consent metadata review.')
    reason = core.text_field(data, 'reason', 500)
    existing = {p['provenance']['key']: p for p in core.rows(conn, 'participants') if p.get('provenance')}
    before = summary(job)
    inserted = 0
    for row in job['rows']:
        if row['key'] in existing:
            previous = existing[row['key']]
            if previous['provenance']['row_sha256'] != row['row_sha256']:
                raise core.ApiError(409, 'A source row changed since preview; create a new preview.')
            row.update(status='Already imported', participant_id=previous['id'])
            continue
        # Reuse the same enrolment handler: imports cannot bypass consent/readiness/capacity.
        participant = enrol(conn, actor, '/api/enrolments', {**row['payload'], 'study_id': job['study_id']})['record']
        original = dict(participant)
        participant['provenance'] = {'key': row['key'], 'external_id': row['external_id'],
                                     'source_name': job['source_name'], 'import_id': job['id'],
                                     'source_sha256': job['source_sha256'], 'row_sha256': row['row_sha256'],
                                     'imported_at': core.stamp(), 'synthetic': True}
        core.save(conn, 'participants', participant)
        core.audit(conn, actor, 'SOURCE_RECONCILED', participant['id'], job['study_id'], original, participant, reason)
        row.update(status='Imported', participant_id=participant['id'])
        inserted += 1
    job.update(status='Committed', committed_at=core.stamp(), committed_by=core.actor_id(actor), inserted=inserted)
    core.save(conn, 'imports', job)
    core.audit(conn, actor, 'IMPORT_COMMITTED', job['id'], job['study_id'], before, summary(job), reason)
    return {'record': job, 'idempotent': False}


def check_bundle(bundle):
    """Local consistency checks only; never labelled official profile validation."""
    entries = bundle.get('entry', [])
    urls = [e['fullUrl'] for e in entries]
    references = []

    def walk(value):
        if isinstance(value, dict):
            if 'reference' in value:
                references.append(value['reference'])
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(bundle)
    checks = [
        {'name': 'Research collection Bundle', 'passed': bundle.get('resourceType') == 'Bundle' and bundle.get('type') == 'collection'},
        {'name': 'Unique resource URLs', 'passed': len(urls) == len(set(urls))},
        {'name': 'All local references resolve', 'passed': all(r in urls for r in references)},
        {'name': 'Resources have IDs and types', 'passed': all(e['resource'].get('id') and e['resource'].get('resourceType') for e in entries)},
    ]
    return {'checks': checks, 'passed': all(c['passed'] for c in checks), 'resources': len(entries),
            'references': len(references), 'scope': 'Local structural and referential checks. Official FHIR profile validation and ABDM acceptance are separate.'}


def provenance_csv(core, conn, actor):
    stream = io.StringIO()
    fields = ['participant_id', 'study_id', 'source_name', 'external_id', 'import_id', 'source_sha256', 'row_sha256', 'imported_at']
    writer = csv.DictWriter(stream, fields)
    writer.writeheader()
    for p in core.scoped(core.rows(conn, 'participants'), actor):
        if not p.get('provenance'):
            continue
        row = {'participant_id': p['id'], 'study_id': p['study_id'], **{k: p['provenance'].get(k, '') for k in fields[2:]}}
        writer.writerow({k: "'" + v if str(v).lstrip().startswith(('=', '+', '-', '@')) else v for k, v in row.items()})
    return stream.getvalue().encode()
