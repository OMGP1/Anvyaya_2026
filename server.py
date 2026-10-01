"""Anvaya CTMS — synthetic SIH 26046 demonstration. Python standard library only."""
import argparse
import base64
import sys
import accounts
import documents
import exchange
import safety_workflow
import study_operations
import csv
import hashlib
import hmac
from html import escape as html_escape
import io
import json
import mimetypes
import os
from pathlib import Path
import random
import re
import secrets
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent
DB = Path(os.environ.get('CTMS_DB', ROOT / 'data' / 'ctms.sqlite'))
PASSWORD = os.environ.get('CTMS_DEMO_PASSWORD', 'Demo#26046')
DEMO_LOGIN = os.environ.get('CTMS_DEMO_LOGIN', 'true').lower() == 'true'
SECURE_COOKIE = os.environ.get('CTMS_SECURE_COOKIE', 'false').lower() == 'true'
CORE = sys.modules[__name__]
LOCK = threading.RLock()
SESSIONS = {}
ATTEMPTS = {}
ROLES = {
    'admin': {'label': 'Research administrator', 'name': 'Aditi Sharma', 'scope': None, 'permissions': ['enrol', 'safety', 'report', 'query', 'visit', 'withdraw', 'study', 'settings', 'export', 'audit', 'users', 'document', 'review', 'amend', 'import', 'operations']},
    'pi': {'label': 'Principal investigator', 'name': 'Kavya Rao', 'scope': ['AIIA-001', 'AIIA-002'], 'permissions': ['enrol', 'safety', 'report', 'query', 'visit', 'withdraw', 'export', 'audit', 'document', 'amend', 'import', 'operations']},
    'coordinator': {'label': 'Study coordinator', 'name': 'Neha Singh', 'scope': ['AIIA-001', 'AIIA-002', 'AIIA-003'], 'permissions': ['enrol', 'safety', 'query', 'visit', 'withdraw', 'document', 'import', 'operations']},
    'monitor': {'label': 'Clinical monitor', 'name': 'Arjun Patel', 'scope': ['AIIA-001', 'AIIA-003', 'AIIA-005'], 'permissions': ['query', 'export', 'audit', 'operations']},
    'ethics': {'label': 'Ethics committee', 'name': 'IEC reviewer', 'scope': None, 'permissions': ['audit', 'review']},
    'pv': {'label': 'Pharmacovigilance officer', 'name': 'Meera Iyer', 'scope': None, 'permissions': ['safety', 'report']},
    'leadership': {'label': 'Institutional leadership', 'name': 'Research director', 'scope': None, 'permissions': []},
    'regulator': {'label': 'Read-only regulator', 'name': 'Audit observer', 'scope': None, 'permissions': ['export', 'audit']},
}


def utcnow():
    return datetime.now(timezone.utc)


def stamp(dt=None):
    return (dt or utcnow()).isoformat(timespec='seconds').replace('+00:00', 'Z')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


@contextmanager
def connect():
    conn = sqlite3.connect(DB, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def rows(conn, table):
    return [json.loads(r['data']) for r in conn.execute(f'SELECT data FROM {table}')]


def get(conn, table, ident):
    row = conn.execute(f'SELECT data FROM {table} WHERE id=?', (ident,)).fetchone()
    if not row:
        raise ApiError(404, 'Record not found.')
    return json.loads(row['data'])


def save(conn, table, record):
    conn.execute(f'INSERT INTO {table}(id,data) VALUES (?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data', (record['id'], canonical(record)))


def role_info(role):
    return role if isinstance(role, dict) else ROLES[role]


def role_key(role):
    return role['role'] if isinstance(role, dict) else role


def actor_id(role):
    if isinstance(role, dict):
        return role.get('user_id') or 'demo:' + role['role']
    return role


def audit(conn, actor, action, entity, study_id=None, before=None, after=None, reason=''):
    previous = conn.execute('SELECT hash FROM audit ORDER BY seq DESC LIMIT 1').fetchone()
    prev = previous['hash'] if previous else '0' * 64
    payload = {'timestamp': stamp(), 'actor': actor_id(actor), 'action': action, 'entity': entity, 'study_id': study_id, 'before': before, 'after': after, 'reason': reason}
    if isinstance(actor, dict):
        payload.update(actor_name=actor['name'], actor_role=actor['role'])
    digest = hashlib.sha256((prev + canonical(payload)).encode()).hexdigest()
    conn.execute('INSERT INTO audit(payload,prev,hash) VALUES (?,?,?)', (canonical(payload), prev, digest))


def verify_audit(conn):
    previous = '0' * 64
    count = 0
    for row in conn.execute('SELECT * FROM audit ORDER BY seq'):
        if row['prev'] != previous or hashlib.sha256((previous + row['payload']).encode()).hexdigest() != row['hash']:
            return {'valid': False, 'entries': count, 'failed_at': row['seq']}
        previous = row['hash']
        count += 1
    return {'valid': True, 'entries': count, 'head': previous, 'checked_at': stamp()}


def initialize():
    DB.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        for table in ['studies', 'participants', 'events', 'queries', 'visits', 'settings', 'users', 'documents', 'amendments', 'imports', 'obligations', 'dictionaries', 'sites', 'monitoring_visits', 'deviations']:
            conn.execute(f'CREATE TABLE IF NOT EXISTS {table}(id TEXT PRIMARY KEY, data TEXT NOT NULL)')
        conn.executescript('''CREATE TABLE IF NOT EXISTS audit(seq INTEGER PRIMARY KEY AUTOINCREMENT,payload TEXT NOT NULL,prev TEXT NOT NULL,hash TEXT NOT NULL);
        CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit BEGIN SELECT RAISE(ABORT,'Audit records are append-only'); END;
        CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit BEGIN SELECT RAISE(ABORT,'Audit records are append-only'); END;''')
        if not rows(conn, 'users') and os.environ.get('CTMS_ADMIN_PASSWORD'):
            accounts.create(CORE, conn, {'username': os.environ.get('CTMS_ADMIN_USERNAME', 'admin'), 'name': 'Workspace administrator', 'role': 'admin', 'scope': None, 'password': os.environ['CTMS_ADMIN_PASSWORD']}, 'system:bootstrap')
        if not DEMO_LOGIN and not any(u['active'] and u['role'] == 'admin' for u in rows(conn, 'users')):
            raise RuntimeError('Set CTMS_ADMIN_PASSWORD (12+ characters) to bootstrap named access when demonstration login is disabled.')
        if conn.execute('SELECT count(*) FROM studies').fetchone()[0]:
            study_operations.seed(CORE, conn)
            return
        now = utcnow()
        rng = random.Random(26046)
        spec = [
            ('Sandhivata care study', 'Joint health', 'Compound formulation', 'Guduchi-based investigational formulation', 60, 38, 'Recruiting', 85, True),
            ('Madhumeha lifestyle study', 'Metabolic health', 'Whole-system regimen', 'Diet, movement and protocol-defined regimen', 50, 24, 'Recruiting', 8, False),
            ('Panchakarma recovery study', 'Musculoskeletal health', 'Procedure', 'Protocol-defined Panchakarma programme', 40, 17, 'Recruiting', 120, False),
            ('Sleep & wellbeing study', 'Sleep health', 'Single-herb formulation', 'Investigational single-herb preparation', 35, 0, 'Setup', 60, False),
            ('Prakriti cohort', 'Observational research', 'Observational', 'No assigned intervention', 30, 12, 'Recruiting', 150, False),
            ('Digestive health follow-up', 'Digestive health', 'Compound formulation', 'Protocol-defined formulation', 25, 9, 'Follow-up', 45, False),
        ]
        for i, (title, condition, kind, formulation, target, count, status, expiry, ndct) in enumerate(spec, 1):
            sid = f'AIIA-{i:03}'
            study = {'id': sid, 'title': title, 'condition': condition, 'type': kind, 'formulation': formulation, 'batch': f'DEMO-BATCH-{i:02}', 'target': target, 'status': status, 'site': ['Delhi', 'Goa', 'Jaipur'][i % 3], 'pi': ['Dr. Kavya Rao', 'Dr. Meera Iyer', 'Dr. Arjun Patel'][i % 3], 'ctri': f'DEMO-CTRI-2026-{i:04}' if i != 4 else '', 'registered_at': (now - timedelta(days=100)).date().isoformat() if i != 4 else '', 'iec_expiry': (now + timedelta(days=expiry)).date().isoformat(), 'iec_reference': f'DEMO-IEC-{i:03}', 'protocol': '2.1', 'ndct': ndct, 'safety_hours': 24, 'start': (now - timedelta(days=60)).date().isoformat(), 'end': (now + timedelta(days=60)).date().isoformat(), 'created_at': stamp(now - timedelta(days=100))}
            study.update(consent_version='2.1', iec_approved_at=(now - timedelta(days=90)).date().isoformat(), revision=1)
            save(conn, 'studies', study)
            for j in range(1, count + 1):
                pid = f'SYN-{i:02}-{j:03}'
                enrolled = now - timedelta(days=rng.randint(1, 55))
                participant = {'id': pid, 'study_id': sid, 'age': rng.randint(22, 67), 'sex': rng.choice(['F', 'M']), 'prakriti': rng.choice(['Vata-Pitta', 'Pitta-Kapha', 'Vata-Kapha', 'Balanced']), 'status': 'Enrolled', 'consent': True, 'consent_version': '2.1', 'consent_language': rng.choice(['English', 'Hindi']), 'consent_at': stamp(enrolled - timedelta(hours=1)), 'consent_recorder': 'seed', 'enrolled_at': stamp(enrolled), 'site': study['site']}
                save(conn, 'participants', participant)
                for visit in range(1, 3):
                    due = enrolled + timedelta(days=visit * 14)
                    complete = due < now and rng.random() > .12
                    save(conn, 'visits', {'id': f'{pid}-V{visit}', 'study_id': sid, 'participant_id': pid, 'name': f'Follow-up {visit}', 'due': due.date().isoformat(), 'completed_at': stamp(due) if complete else None})
            audit(conn, 'system:synthetic-seed', 'STUDY_SEEDED', sid, sid, after={'title': title, 'participants': count}, reason='Fictional demonstration dataset; no clinical evidence')
        for i, (pid, term, serious, ago, submitted) in enumerate([
            ('SYN-01-003', 'Hospitalisation after reported dizziness', True, 19, False),
            ('SYN-02-004', 'Unplanned hospital admission', True, 30, False),
            ('SYN-01-010', 'Reported nausea', False, 8, False),
            ('SYN-03-006', 'Reported skin irritation', False, 45, True),
            ('SYN-01-021', 'Hospitalisation under evaluation', True, 72, True),
        ], 1):
            p = get(conn, 'participants', pid)
            occurrence = now - timedelta(hours=ago)
            event = {'id': f'AE-{i:04}', 'study_id': p['study_id'], 'participant_id': pid, 'term': term, 'narrative': 'Synthetic report for workflow demonstration. Causality has not been established.', 'serious': serious, 'seriousness': 'Hospitalisation' if serious else 'Non-serious', 'severity': 'Moderate', 'occurred_at': stamp(occurrence), 'awareness_at': stamp(occurrence + timedelta(hours=1)), 'created_at': stamp(occurrence + timedelta(hours=2)), 'status': 'Initial report recorded' if submitted else 'Awaiting review', 'reported_at': stamp(occurrence + timedelta(hours=6)) if submitted else None, 'report_reference': f'DEMO-ACK-{i}' if submitted else '', 'analysis_at': None, 'coding': 'Pending licensed dictionary review'}
            save(conn, 'events', event)
            audit(conn, 'system:synthetic-seed', 'SAFETY_SEEDED', event['id'], p['study_id'], after=event)
        for i in range(1, 13):
            sid = ['AIIA-001', 'AIIA-002', 'AIIA-003', 'AIIA-005'][i % 4]
            save(conn, 'queries', {'id': f'DQ-{i:03}', 'study_id': sid, 'field': ['Visit date', 'Batch reference', 'Baseline assessment', 'Consent version'][i % 4], 'message': ['Confirm source visit date', 'Verify formulation batch against log', 'Complete missing baseline assessment', 'Reconcile consent version with protocol'][i % 4], 'status': 'Open', 'opened_at': stamp(now - timedelta(days=i)), 'resolution': ''})
        save(conn, 'settings', {'id': 'alerts', 'enrolment_threshold': 70, 'iec_days': 30, 'query_days': 7})
        study_operations.seed(CORE, conn, examples=True)


class ApiError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


def text_field(data, key, limit=250, required=True):
    value = data.get(key, '')
    if not isinstance(value, str) or len(value.strip()) > limit or (required and not value.strip()):
        raise ApiError(400, f'Provide a valid {key.replace("_", " ")} (maximum {limit} characters).')
    return value.strip()


def choice(data, key, options):
    value = text_field(data, key)
    if value not in options:
        raise ApiError(400, f'Invalid {key.replace("_", " ")}.')
    return value


def date_time(data, key):
    try:
        value = datetime.fromisoformat(text_field(data, key).replace('Z', '+00:00'))
        if value.tzinfo is None or value > utcnow() + timedelta(seconds=30):
            raise ValueError()
        return value
    except ValueError:
        raise ApiError(400, f'{key.replace("_", " ")} must be a timezone-aware timestamp that is not in the future.')


def number(data, key, low, high):
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ApiError(400, f'{key} must be an integer between {low} and {high}.')
    return value


def calendar_date(data, key, required=True):
    value = text_field(data, key, 10, required)
    if not value:
        return ''
    try:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            raise ValueError()
        datetime.strptime(value, '%Y-%m-%d')
    except ValueError:
        raise ApiError(400, f'{key.replace("_", " ")} must be a valid YYYY-MM-DD date.')
    return value


def study_readiness(study):
    """One set of recorded-evidence gates for activation and enrolment."""
    today = utcnow().date().isoformat()
    checks = []

    def add(key, label, passed, detail, error):
        checks.append({'key': key, 'label': label, 'passed': bool(passed), 'detail': detail, 'error': error})

    def recorded(value):
        return bool(value and value.strip().lower() not in {'pending', 'pending approval', 'not assigned'})

    registry = study.get('ctri', '')
    registered = study.get('registered_at', '')
    add('registration', 'Prospective registration', recorded(registry) and not registry.upper().startswith('REF') and registered and registered <= today,
        f'{registry or "Registration missing"} · {registered or "date missing"}',
        'prospective CTRI registration is required; record a registration reference and a date no later than today.')
    approved = study.get('iec_approved_at', '')
    expiry = study.get('iec_expiry', '')
    # Existing active demo records predate approval-date capture; retain their
    # original reference/expiry gate. Every newly activated study needs both dates.
    legacy_approval = 'iec_approved_at' not in study and study['status'] != 'Setup'
    ethics_ok = recorded(study.get('iec_reference')) and expiry and expiry >= today and (legacy_approval or (approved and approved <= today and approved <= expiry))
    add('ethics', 'Current IEC approval', ethics_ok,
        f'{study.get("iec_reference") or "Approval reference missing"} · {approved or ("approval date not captured in earlier demo" if legacy_approval else "approval date missing")} · until {expiry or "date missing"}',
        'current IEC approval requires a reference, an effective approval date and an expiry date no earlier than today.')
    consent = study.get('consent_version', study.get('protocol', ''))
    add('versions', 'Protocol and consent versions', recorded(study.get('protocol')) and recorded(consent),
        f'Protocol {study.get("protocol") or "missing"} · consent {consent or "missing"}',
        'record the current protocol and consent versions.')
    add('investigator', 'Responsible investigator', recorded(study.get('pi')),
        study.get('pi') or 'No investigator recorded', 'record the responsible investigator.')
    needs_batch = study['type'] in {'Compound formulation', 'Single-herb formulation'}
    add('product', 'Intervention context', recorded(study.get('formulation')) and (not needs_batch or recorded(study.get('batch'))),
        f'{study["type"]} · batch {study.get("batch") or "not recorded"}' if needs_batch else f'{study["type"]} · no product batch gate',
        'record the intervention and a batch reference for formulation studies.')
    add('period', 'Study period open', study['start'] <= today <= study['end'],
        f'{study["start"]} to {study["end"]}', 'the current date must fall within the recorded study period.')
    return {'ready': all(c['passed'] for c in checks), 'passed': sum(c['passed'] for c in checks), 'total': len(checks), 'checks': checks}


def authorized(role, permission=None, study_id=None):
    info = role_info(role)
    if permission and permission not in info['permissions']:
        raise ApiError(403, 'Your role does not permit this action.')
    if study_id and info['scope'] is not None and study_id not in info['scope']:
        raise ApiError(403, 'This study is outside your assigned scope.')


def scoped(records, role, study=False):
    scope = role_info(role)['scope']
    return [r for r in records if scope is None or r['id' if study else 'study_id'] in scope]


def event_deadlines(event, study):
    result = dict(event)
    if event['serious']:
        base = datetime.fromisoformat(event['occurred_at'].replace('Z', '+00:00'))
        result['initial_due'] = stamp(base + timedelta(hours=24 if study['ndct'] else study['safety_hours']))
        result['analysis_due'] = stamp(base + timedelta(days=14)) if study['ndct'] else None
        result['rule'] = 'NDCT 42(1) / 25(x) • demo applicability' if study['ndct'] else f'Protocol SOP • {study["safety_hours"]}h internal target'
    else:
        result.update(initial_due=None, analysis_due=None, rule='Routine AE review per protocol')
    return result


def snapshot(conn, role):
    if isinstance(role, str):
        role = {**ROLES[role], 'role': role, 'user_id': None, 'demo': True}
    studies = scoped(rows(conn, 'studies'), role, True)
    participants = scoped(rows(conn, 'participants'), role)
    study_map = {s['id']: s for s in studies}
    visits = scoped(rows(conn, 'visits'), role)
    queries = scoped(rows(conn, 'queries'), role)
    events = [event_deadlines(e, get(conn, 'studies', e['study_id'])) for e in scoped(rows(conn, 'events'), role)]
    settings = get(conn, 'settings', 'alerts')
    today = utcnow().date()
    alerts = []
    for s in studies:
        s['readiness'] = study_readiness(s)
        s['revision'] = s.get('revision', 0)
        s['consent_version'] = s.get('consent_version', s['protocol'])
        s['enrolled'] = sum(p['study_id'] == s['id'] for p in participants)
        s['active_participants'] = sum(p['study_id'] == s['id'] and p['status'] == 'Enrolled' for p in participants)
        s['progress'] = round(s['enrolled'] / s['target'] * 100)
        duration = max(1, (datetime.fromisoformat(s['end']).date() - datetime.fromisoformat(s['start']).date()).days)
        elapsed = max(0, (today - datetime.fromisoformat(s['start']).date()).days)
        s['expected'] = min(s['target'], round(s['target'] * elapsed / duration))
        s['pace'] = round(s['enrolled'] / s['expected'] * 100) if s['expected'] else 100
        s['iec_days'] = (datetime.fromisoformat(s['iec_expiry']).date() - today).days if s['iec_expiry'] else None
        s['risk'] = 'Attention' if not s['readiness']['ready'] or (s['iec_days'] is not None and s['iec_days'] <= settings['iec_days']) or (s['status'] == 'Recruiting' and s['pace'] < settings['enrolment_threshold']) else 'On track'
        if not s['ctri']:
            alerts.append({'level': 'warning', 'title': 'Registration required before enrolment', 'detail': s['title'], 'study_id': s['id'], 'page': 'compliance'})
        if s['iec_days'] is not None and s['iec_days'] <= settings['iec_days']:
            alerts.append({'level': 'danger' if s['iec_days'] < 0 else 'warning', 'title': f'IEC approval {"expired" if s["iec_days"] < 0 else "expires in " + str(s["iec_days"]) + " days"}', 'detail': s['title'], 'study_id': s['id'], 'page': 'compliance'})
        if s['status'] == 'Recruiting' and s['pace'] < settings['enrolment_threshold']:
            alerts.append({'level': 'warning', 'title': 'Recruitment behind planned pace', 'detail': f'{s["title"]} · {s["enrolled"]} of {s["expected"]} expected', 'study_id': s['id'], 'page': 'studies'})
    for e in events:
        for field, reported, label in [('initial_due', 'reported_at', 'Initial safety report'), ('analysis_due', 'analysis_at', 'Analysed safety report')]:
            if e[field] and not e[reported]:
                hours = (datetime.fromisoformat(e[field].replace('Z', '+00:00')) - utcnow()).total_seconds() / 3600
                if hours <= 24:
                    alerts.insert(0, {'level': 'danger', 'title': f'{label} {"overdue" if hours < 0 else "due in " + str(round(hours)) + "h"}', 'detail': f'{e["id"]} · {e["rule"]}', 'study_id': e['study_id'], 'page': 'safety'})
    participant_map = {p['id']: p for p in participants}
    for query in queries:
        age = (today - datetime.fromisoformat(query['opened_at'][:10]).date()).days
        if query['status'] == 'Open' and age >= settings['query_days']:
            alerts.append({'level': 'warning', 'title': f'Data query open {age} days',
                           'detail': 'Scoped query requires review' if role_key(role) == 'leadership' else query['id'] + ' · ' + query['field'],
                           'study_id': query['study_id'], 'page': 'queries',
                           'rule': f'Open query age ≥ {settings["query_days"]} days', 'owner': 'Data review team'})
    for visit in visits:
        participant = participant_map[visit['participant_id']]
        visit['cancelled'] = bool(not visit['completed_at'] and participant.get('withdrawn_at') and visit['due'] >= participant['withdrawn_at'][:10])
        visit['consent_active'] = participant['consent'] and not participant.get('reconsent_required') and participant['consent_version'] == study_map[participant['study_id']].get('consent_version', study_map[participant['study_id']]['protocol'])
    due = [v for v in visits if v['due'] <= today.isoformat() and not v['cancelled']]
    complete = [v for v in due if v['completed_at']]
    trend = []
    for week in range(7, -1, -1):
        day = today - timedelta(days=week * 7)
        trend.append({'date': day.isoformat(), 'actual': sum(p['enrolled_at'][:10] <= day.isoformat() for p in participants)})
    kpis = {'studies': len(studies), 'active_studies': sum(s['status'] == 'Recruiting' for s in studies), 'enrolled': len(participants), 'target': sum(s['target'] for s in studies), 'open_queries': sum(q['status'] == 'Open' for q in queries), 'serious_pending': sum(e['serious'] and not e['reported_at'] for e in events), 'visit_compliance': round(len(complete) / len(due) * 100) if due else None, 'visits_due': len(due), 'visits_complete': len(complete), 'consented': sum(p['consent'] for p in participants)}
    safety_counts = {'total': len(events), 'serious': sum(e['serious'] for e in events), 'initial_pending': kpis['serious_pending']}
    result = {'studies': studies, 'participants': participants, 'visits': visits, 'queries': queries, 'events': events, 'alerts': alerts, 'settings': settings, 'kpis': kpis, 'trend': trend, 'safety_counts': safety_counts, 'server_time': stamp(), 'synthetic': True}
    result['obligations'] = safety_workflow.list_obligations(CORE, conn, role)
    result['dictionaries'] = safety_workflow.list_dictionary_metadata(CORE, conn, role) if {'safety', 'report', 'settings'}.intersection(role['permissions']) else []
    for obligation in result['obligations']:
        if obligation['overdue']:
            alerts.insert(0, {'level': 'danger', 'title': 'Recipient follow-up overdue', 'detail': obligation['event_id'] + ' · ' + obligation['recipient'], 'study_id': obligation['study_id'], 'page': 'safety'})
    result['users'] = [accounts.public(u) for u in rows(conn, 'users')] if 'users' in role_info(role)['permissions'] else []
    result['documents'] = documents.list_documents(CORE, conn, role) if role_key(role) != 'leadership' else []
    result['amendments'] = scoped(rows(conn, 'amendments'), role) if role_key(role) != 'leadership' else []
    result['imports'] = [exchange.summary(j) for j in scoped(rows(conn, 'imports'), role)] if 'import' in role_info(role)['permissions'] else []
    operations = study_operations.snapshot(CORE, conn, role, studies, participants, events, settings)
    alerts.extend(operations.pop('operation_alerts'))
    result.update(operations)
    if role_key(role) == 'leadership':
        result.update(participants=[], visits=[], queries=[], events=[])
    elif role_key(role) == 'ethics':
        result['visits'] = []
        result['queries'] = []
    return result


def bundle(conn, role, study_id=None):
    participants = scoped(rows(conn, 'participants'), role)
    studies = scoped(rows(conn, 'studies'), role, True)
    if study_id:
        authorized(role, study_id=study_id)
        studies = [s for s in studies if s['id'] == study_id]
        participants = [p for p in participants if p['study_id'] == study_id]
        if not studies:
            raise ApiError(404, 'Study not found.')
    resources = []
    base = 'https://anvaya.example/fhir/'
    for s in studies:
        resources.append({'resourceType': 'ResearchStudy', 'id': s['id'], 'identifier': [{'system': 'https://anvaya.example/studies', 'value': s['id']}], 'title': s['title'], 'status': {'Recruiting': 'active', 'Setup': 'in-review', 'Follow-up': 'closed-to-accrual', 'Completed': 'completed'}[s['status']], 'description': 'SYNTHETIC DEMONSTRATION. Not an actual registered clinical study.', 'period': {'start': s['start'], 'end': s['end']}})
    for p in participants:
        resources.append({'resourceType': 'Patient', 'id': p['id'], 'identifier': [{'system': 'https://anvaya.example/synthetic-subjects', 'value': p['id']}]})
        resources.append({'resourceType': 'ResearchSubject', 'id': 'RS-' + p['id'], 'status': 'on-study' if p['status'] == 'Enrolled' else 'withdrawn', 'study': {'reference': base + 'ResearchStudy/' + p['study_id']}, 'individual': {'reference': base + 'Patient/' + p['id']}, 'consent': {'reference': base + 'Consent/C-' + p['id']}, 'period': {'start': p['enrolled_at']}})
        resources.append({'resourceType': 'Consent', 'id': 'C-' + p['id'], 'status': 'active' if p['consent'] else 'inactive', 'scope': {'coding': [{'system': 'http://terminology.hl7.org/CodeSystem/consentscope', 'code': 'research'}]}, 'category': [{'coding': [{'system': 'http://loinc.org', 'code': '59284-0', 'display': 'Consent Document'}]}], 'patient': {'reference': base + 'Patient/' + p['id']}, 'dateTime': p['consent_at'], 'policyRule': {'text': 'Synthetic study consent record; not a validated electronic signature'}})
    for resource in resources:
        description = f'Synthetic demonstration. {resource["resourceType"]}: {resource["id"]}.'
        if resource['resourceType'] == 'ResearchStudy':
            description += f' {resource["title"]}. Status: {resource["status"]}.'
        elif resource['resourceType'] == 'ResearchSubject':
            description += f' Status: {resource["status"]}. Study: {resource["study"]["reference"]}. Participant: {resource["individual"]["reference"]}.'
        elif resource['resourceType'] == 'Consent':
            description += f' Status: {resource["status"]}. Recorded: {resource["dateTime"]}. Synthetic consent metadata; not a validated electronic signature.'
        resource['text'] = {'status': 'generated', 'div': '<div xmlns="http://www.w3.org/1999/xhtml"><p>' + html_escape(description) + '</p></div>'}
    return {'resourceType': 'Bundle', 'type': 'collection', 'timestamp': stamp(), 'entry': [{'fullUrl': base + r['resourceType'] + '/' + r['id'], 'resource': r} for r in resources]}


def csv_export(conn, role, domain):
    stream = io.StringIO()
    if domain == 'dm':
        fields = ['STUDYID', 'DOMAIN', 'USUBJID', 'SUBJID', 'SITEID', 'AGE', 'AGEU', 'SEX', 'RFICDTC']
        records = [dict(zip(fields, [p['study_id'], 'DM', p['id'], p['id'], p['site'], p['age'], 'YEARS', p['sex'], p['consent_at']])) for p in scoped(rows(conn, 'participants'), role)]
    else:
        fields = ['STUDYID', 'DOMAIN', 'USUBJID', 'AESEQ', 'AETERM', 'AESEV', 'AESER', 'AESTDTC']
        records = [dict(zip(fields, [e['study_id'], 'AE', e['participant_id'], i, e['term'], e['severity'].upper(), 'Y' if e['serious'] else 'N', e['occurred_at']])) for i, e in enumerate(scoped(rows(conn, 'events'), role), 1)]
    writer = csv.DictWriter(stream, fields)
    writer.writeheader()
    # Neutralise spreadsheet formulas in user-supplied text.
    for record in records:
        writer.writerow({k: "'" + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@')) else v for k, v in record.items()})
    return stream.getvalue().encode()


def response_data(value, content_type='application/json', headers=None):
    data = value if isinstance(value, bytes) else canonical(value).encode()
    values = {'Content-Type': content_type, 'Content-Length': str(len(data)), 'Cache-Control': 'no-store',
              'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'DENY', 'Referrer-Policy': 'same-origin',
              'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'",
              **(headers or {})}
    return data, values


class Handler(BaseHTTPRequestHandler):
    server_version = 'AnvayaDemo/1.0'

    def log_message(self, fmt, *args):
        if args and len(args) > 1 and str(args[1]) not in ('200', '304'):
            super().log_message(fmt, *args)

    def send(self, status, value, content_type='application/json', headers=None):
        data, values = response_data(value, content_type, headers)
        self.send_response(status)
        for key, val in values.items():
            self.send_header(key, val)
        self.end_headers()
        self.wfile.write(data)

    def session(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get('Cookie', ''))
        except Exception:
            raise ApiError(401, 'Please sign in.')
        token = cookie.get('ctms_session')
        session = SESSIONS.get(token.value if token else '')
        if not session or session['expires'] < time.time():
            raise ApiError(401, 'Please sign in.')
        if session.get('user_id'):
            with LOCK, connect() as conn:
                user = get(conn, 'users', session['user_id'])
            if not user['active'] or user['auth_version'] != session['auth_version']:
                raise ApiError(401, 'Your access changed. Sign in again.')
            session['principal'] = accounts.principal(CORE, user)
        elif not DEMO_LOGIN:
            raise ApiError(401, 'Demonstration sign-in is disabled.')
        return session

    def body(self):
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 800000:
                raise ValueError()
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError()
            return data
        except (ValueError, UnicodeDecodeError):
            raise ApiError(400, 'Expected a JSON object up to 800 KB.')

    def do_GET(self):
        try:
            url = urlparse(self.path)
            path = url.path
            if path == '/api/health':
                with connect() as conn:
                    conn.execute('SELECT id FROM studies LIMIT 1').fetchone()
                return self.send(200, {'status': 'ok', 'database': 'ok', 'synthetic': True})
            if path == '/api/config':
                return self.send(200, {'demo_login': DEMO_LOGIN})
            if path == '/api/roles':
                return self.send(200, {k: {'label': v['label'], 'name': v['name']} for k, v in ROLES.items()})
            if path.startswith('/api/'):
                with LOCK, connect() as conn:
                    session = self.session()
                    role = session['principal']
                    if path == '/api/me':
                        return self.send(200, {**role, 'csrf': session['csrf']})
                    if role.get('must_change_password'):
                        raise ApiError(403, 'Change your temporary password before opening the workspace.')
                    if path == '/api/users':
                        authorized(role, 'users')
                        return self.send(200, {'users': [accounts.public(u) for u in rows(conn, 'users')]})
                    if path == '/api/data':
                        return self.send(200, snapshot(conn, role))
                    if path == '/api/operations/inspection':
                        return self.send(200, study_operations.inspection(CORE, conn, role, parse_qs(url.query).get('study', [None])[0]))
                    safety_match = re.fullmatch(r'/api/safety/([A-Za-z0-9-]+)/(suggestions|assignees)', path)
                    if safety_match:
                        event_id, action = safety_match.groups()
                        if action == 'suggestions':
                            dictionary_id = parse_qs(url.query).get('dictionary_id', [''])[0]
                            return self.send(200, safety_workflow.suggest(CORE, conn, role, event_id, dictionary_id))
                        event = get(conn, 'events', event_id)
                        return self.send(200, {'assignees': safety_workflow.list_assignees(CORE, conn, role, event['study_id'])})
                    if path == '/api/exchange/check':
                        authorized(role, 'export')
                        return self.send(200, exchange.check_bundle(bundle(conn, role)))
                    if path.startswith('/api/imports/'):
                        job = get(conn, 'imports', path.rsplit('/', 1)[1])
                        authorized(role, 'import', job['study_id'])
                        return self.send(200, {'record': job})
                    if path.startswith('/api/documents/'):
                        doc = documents.get_document(CORE, conn, role, path.rsplit('/', 1)[1])
                        audit(conn, role, 'DOCUMENT_DOWNLOADED', doc['id'], doc['study_id'], reason='Recorded evidence downloaded')
                        conn.commit()
                        return self.send(200, base64.b64decode(doc['content_base64']), doc['media_type'], {'Content-Disposition': f'attachment; filename="{doc["filename"]}"'})
                    if path == '/api/audit':
                        authorized(role, 'audit')
                        entries = [{'seq': row['seq'], **json.loads(row['payload']), 'hash': row['hash'], 'prev': row['prev']} for row in conn.execute('SELECT * FROM audit ORDER BY seq DESC')]
                        entries = [r for r in entries if role_info(role)['scope'] is None or r['study_id'] in role_info(role)['scope']]
                        return self.send(200, {'entries': entries, 'verification': verify_audit(conn)})
                    if path.startswith('/api/export/'):
                        authorized(role, 'export')
                        kind = path.rsplit('/', 1)[1]
                        if kind == 'fhir':
                            data = json.dumps(bundle(conn, role, parse_qs(url.query).get('study', [None])[0]), indent=2).encode()
                            filename, mime = 'anvaya-synthetic-fhir-r4.json', 'application/fhir+json'
                        elif kind == 'provenance':
                            data = exchange.provenance_csv(CORE, conn, role)
                            filename, mime = 'source-provenance.csv', 'text/csv; charset=utf-8'
                        elif kind in ['dm', 'ae']:
                            data = csv_export(conn, role, kind)
                            filename, mime = f'{kind.upper()}-mapping-preview.csv', 'text/csv; charset=utf-8'
                        else:
                            raise ApiError(404, 'Unknown export format.')
                        audit(conn, role, 'DATA_EXPORTED', kind, reason='Synthetic demonstration export')
                        conn.commit()
                        return self.send(200, data, mime, {'Content-Disposition': f'attachment; filename="{filename}"'})
                raise ApiError(404, 'Endpoint not found.')
            allowed = {'/': 'index.html', '/index.html': 'index.html', '/app.js': 'app.js', '/workflows.js': 'workflows.js', '/operations.js': 'operations.js', '/safety.js': 'safety.js', '/style.css': 'style.css', '/favicon.svg': 'favicon.svg'}
            if path not in allowed:
                raise ApiError(404, 'Page not found.')
            file = ROOT / 'public' / allowed[path]
            return self.send(200, file.read_bytes(), mimetypes.guess_type(file.name)[0] or 'text/plain')
        except ApiError as e:
            self.send(e.status, {'error': e.message})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            print('GET error:', repr(e))
            self.send(500, {'error': 'An unexpected error occurred. See the local server log.'})

    def do_POST(self):
        try:
            path = urlparse(self.path).path
            data = self.body()
            origin = self.headers.get('Origin')
            if origin and urlparse(origin).netloc != self.headers.get('Host'):
                raise ApiError(403, 'Cross-origin request denied.')
            with LOCK:
                if path == '/api/login':
                    key = self.client_address[0]
                    attempts = [t for t in ATTEMPTS.get(key, []) if t > time.time() - 60]
                    login_name = data.get('username') if data.get('username') else data.get('role')
                    identity_key = ('identity', login_name.strip().lower() if isinstance(login_name, str) else 'invalid')
                    identity_attempts = [t for t in ATTEMPTS.get(identity_key, []) if t > time.time() - 60]
                    if len(attempts) >= 15 or len(identity_attempts) >= 15:
                        raise ApiError(429, 'Too many login attempts. Try again in one minute.')
                    with connect() as conn:
                        user = accounts.find(CORE, conn, data.get('username')) if data.get('username') else None
                        if data.get('username'):
                            valid = user and user['active'] and accounts.password_matches(data.get('password'), user['password_hash'])
                            if not valid and not user:
                                # Match password work to avoid fast username enumeration.
                                hashlib.pbkdf2_hmac('sha256', b'invalid', b'login-placeholder', accounts.ITERATIONS)
                            principal = accounts.principal(CORE, user) if valid else None
                        else:
                            role = data.get('role')
                            valid = DEMO_LOGIN and isinstance(role, str) and role in ROLES and isinstance(data.get('password'), str) and hmac.compare_digest(data['password'].encode(), PASSWORD.encode())
                            principal = {**ROLES[role], 'role': role, 'demo': True, 'user_id': None} if valid else None
                        if not valid:
                            ATTEMPTS[key] = attempts + [time.time()]
                            ATTEMPTS[identity_key] = identity_attempts + [time.time()]
                            raise ApiError(401, 'Incorrect credentials or inactive account.')
                        audit(conn, principal, 'SESSION_STARTED', actor_id(principal), reason='Named account sign-in' if user else 'Demonstration persona; shared credentials')
                    token = secrets.token_urlsafe(32)
                    SESSIONS[token] = {'principal': principal, 'user_id': user['id'] if user else None, 'auth_version': user['auth_version'] if user else 0, 'csrf': secrets.token_urlsafe(24), 'expires': time.time() + 8 * 3600}
                    for expired in [k for k, v in SESSIONS.items() if v['expires'] < time.time()]:
                        SESSIONS.pop(expired, None)
                    ATTEMPTS[key] = attempts
                    ATTEMPTS.pop(identity_key, None)
                    secure = '; Secure' if SECURE_COOKIE else ''
                    return self.send(200, {'ok': True}, headers={'Set-Cookie': f'ctms_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800{secure}'})
                session = self.session()
                if not hmac.compare_digest(self.headers.get('X-CSRF-Token', ''), session['csrf']):
                    raise ApiError(403, 'Invalid request token. Refresh and try again.')
                role = session['principal']
                if path == '/api/logout':
                    cookie = SimpleCookie(self.headers.get('Cookie', ''))
                    SESSIONS.pop(cookie['ctms_session'].value, None)
                    return self.send(200, {'ok': True}, headers={'Set-Cookie': 'ctms_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'})
                if path == '/api/account/password':
                    if not role.get('user_id'):
                        raise ApiError(403, 'Sign in with a named account to change a password.')
                    with connect() as conn:
                        user = get(conn, 'users', role['user_id'])
                        if not accounts.password_matches(data.get('current_password'), user['password_hash']):
                            raise ApiError(400, 'Current password is incorrect.')
                        password = accounts.validate_password(CORE, data)
                        if accounts.password_matches(password, user['password_hash']):
                            raise ApiError(400, 'Choose a different password.')
                        user.update(password_hash=accounts.password_hash(password), must_change_password=False, auth_version=user['auth_version']+1, revision=user['revision']+1)
                        save(conn, 'users', user)
                        audit(conn, role, 'PASSWORD_CHANGED', user['id'], reason='Password changed; other sessions revoked')
                    session['auth_version'] = user['auth_version']
                    return self.send(200, {'ok': True})
                if role.get('must_change_password'):
                    raise ApiError(403, 'Change your temporary password before opening the workspace.')
                with connect() as conn:
                    result = self.mutate(conn, role, path, data)
                self.send(200, {'ok': True, **result})
        except ApiError as e:
            self.send(e.status, {'error': e.message})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            print('POST error:', repr(e))
            self.send(500, {'error': 'Operation could not be completed; no changes were committed.'})

    def mutate(self, conn, role, path, data):
        result = accounts.mutate(CORE, conn, role, path, data)
        if result is not None:
            return result
        result = safety_workflow.mutate(CORE, conn, role, path, data)
        if result is not None:
            return result
        result = documents.mutate(CORE, conn, role, path, data)
        if result is not None:
            return result
        result = exchange.mutate(CORE, conn, role, path, data, self.mutate)
        if result is not None:
            return result
        result = study_operations.mutate(CORE, conn, role, path, data)
        if result is not None:
            return result
        match = re.fullmatch(r'/api/studies/([A-Za-z0-9-]+)/(setup|activate)', path)
        if match:
            sid, action = match.groups()
            authorized(role, 'study', sid)
            study = get(conn, 'studies', sid)
            if study['status'] != 'Setup':
                raise ApiError(409, 'Only setup studies can be changed here. Active-study amendments need a separate reviewed workflow.')
            revision = number(data, 'revision', 0, 1000000)
            if revision != study.get('revision', 0):
                raise ApiError(409, 'Study changed since you opened it. Close this form, refresh and review the latest version.')
            reason = text_field(data, 'reason', 500)
            before = dict(study)
            if action == 'setup':
                for key, limit in [('protocol', 30), ('consent_version', 30), ('formulation', 200), ('pi', 120), ('batch', 120), ('ctri', 120), ('iec_reference', 120)]:
                    study[key] = text_field(data, key, limit, required=key in {'protocol', 'consent_version', 'formulation'})
                for key in ['registered_at', 'iec_approved_at', 'iec_expiry', 'start', 'end']:
                    study[key] = calendar_date(data, key, required=key in {'start', 'end'})
                if study['end'] < study['start']:
                    raise ApiError(400, 'Study end must be on or after study start.')
                if study['iec_approved_at'] and study['iec_expiry'] and study['iec_expiry'] < study['iec_approved_at']:
                    raise ApiError(400, 'IEC expiry must be on or after IEC approval.')
            else:
                if data.get('reviewed') is not True:
                    raise ApiError(400, 'Confirm review of the recorded study readiness checks.')
                blockers = [c['error'] for c in study_readiness(study)['checks'] if not c['passed']]
                if blockers:
                    raise ApiError(409, 'Activation blocked: ' + ' '.join(blockers))
                study.update(status='Recruiting', activated_at=stamp(), activated_by=actor_id(role))
                study_operations.activate_primary(CORE, conn, role, study, reason)
            study.update(revision=revision + 1, updated_at=stamp())
            save(conn, 'studies', study)
            audit(conn, role, 'STUDY_SETUP_UPDATED' if action == 'setup' else 'STUDY_ACTIVATED', sid, sid, before, study, reason)
            return {'record': {**study, 'readiness': study_readiness(study)}}
        if path == '/api/enrolments':
            sid = text_field(data, 'study_id')
            authorized(role, 'enrol', sid)
            s = get(conn, 'studies', sid)
            for check in study_readiness(s)['checks']:
                if not check['passed']:
                    raise ApiError(409, 'Enrolment blocked: ' + check['error'])
            if s['status'] != 'Recruiting':
                raise ApiError(409, 'Enrolment blocked: study is not open for recruitment.')
            if sum(p['study_id'] == sid for p in rows(conn, 'participants')) >= s['target']:
                raise ApiError(409, 'Enrolment target reached. A reviewed amendment is needed to increase it.')
            if data.get('consent') is not True:
                raise ApiError(400, 'Document informed consent before enrolment.')
            version = text_field(data, 'consent_version', 30)
            current_consent = s.get('consent_version', s['protocol'])
            if version != current_consent:
                raise ApiError(409, f'Use current approved consent version {current_consent}.')
            site = study_operations.resolve_site(CORE, conn, role, sid, data.get('site_id'))
            p = {'id': 'SYN-' + secrets.token_hex(4).upper(), 'study_id': sid, 'site_id': site['id'], 'age': number(data, 'age', 18, 100), 'sex': choice(data, 'sex', ['F', 'M', 'U']), 'prakriti': choice(data, 'prakriti', ['Vata-Pitta', 'Pitta-Kapha', 'Vata-Kapha', 'Balanced', 'Not assessed']), 'status': 'Enrolled', 'consent': True, 'consent_version': version, 'consent_language': choice(data, 'consent_language', ['English', 'Hindi', 'Marathi']), 'consent_at': stamp(), 'consent_recorder': actor_id(role), 'enrolled_at': stamp(), 'site': site['city']}
            save(conn, 'participants', p)
            for n in [1, 2]:
                save(conn, 'visits', {'id': p['id'] + f'-V{n}', 'study_id': sid, 'participant_id': p['id'], 'name': f'Follow-up {n}', 'due': (utcnow() + timedelta(days=n * 14)).date().isoformat(), 'completed_at': None})
            audit(conn, role, 'PARTICIPANT_ENROLLED', p['id'], sid, after=p, reason='Consent and study activation gates passed')
            return {'record': p}
        if path == '/api/safety':
            p = get(conn, 'participants', text_field(data, 'participant_id'))
            authorized(role, 'safety', p['study_id'])
            occurred = date_time(data, 'occurred_at')
            awareness = date_time(data, 'awareness_at')
            if awareness < occurred:
                raise ApiError(400, 'Awareness time cannot precede occurrence time.')
            seriousness = choice(data, 'seriousness', ['Non-serious', 'Hospitalisation', 'Life-threatening', 'Death', 'Disability', 'Congenital anomaly', 'Other medically important event'])
            e = {'id': 'AE-' + secrets.token_hex(3).upper(), 'study_id': p['study_id'], 'participant_id': p['id'], 'term': text_field(data, 'term', 160), 'narrative': text_field(data, 'narrative', 2000), 'serious': seriousness != 'Non-serious', 'seriousness': seriousness, 'severity': choice(data, 'severity', ['Mild', 'Moderate', 'Severe']), 'occurred_at': stamp(occurred), 'awareness_at': stamp(awareness), 'created_at': stamp(), 'status': 'Awaiting review', 'reported_at': None, 'report_reference': '', 'analysis_at': None, 'coding': 'Pending licensed dictionary review'}
            save(conn, 'events', e)
            audit(conn, role, 'SAFETY_RECORDED', e['id'], e['study_id'], after=e, reason='Causality unassessed; verbatim report retained')
            return {'record': event_deadlines(e, get(conn, 'studies', e['study_id']))}
        match = re.fullmatch(r'/api/safety/([A-Za-z0-9-]+)/report', path)
        if match:
            e = get(conn, 'events', match[1])
            authorized(role, 'report', e['study_id'])
            phase = choice(data, 'phase', ['initial', 'analysis'])
            field = 'reported_at' if phase == 'initial' else 'analysis_at'
            if e[field]:
                raise ApiError(409, 'This reporting step is already recorded.')
            if phase == 'analysis' and not e['reported_at']:
                raise ApiError(409, 'Record the initial report first.')
            before = dict(e)
            e[field] = stamp()
            e['report_reference' if phase == 'initial' else 'analysis_reference'] = text_field(data, 'reference', 160)
            e['status'] = 'Initial report recorded' if phase == 'initial' else 'Analysis recorded'
            reason = text_field(data, 'reason', 500)
            save(conn, 'events', e)
            audit(conn, role, 'SAFETY_' + phase.upper() + '_RECORDED', e['id'], e['study_id'], before, e, reason)
            return {'record': e}
        match = re.fullmatch(r'/api/queries/(DQ-[A-Za-z0-9]+)/resolve', path)
        if match:
            q = get(conn, 'queries', match[1])
            authorized(role, 'query', q['study_id'])
            if q['status'] != 'Open':
                raise ApiError(409, 'Query already resolved.')
            before = dict(q)
            q.update(status='Resolved', resolution=text_field(data, 'resolution', 1000), resolved_at=stamp())
            save(conn, 'queries', q)
            audit(conn, role, 'QUERY_RESOLVED', q['id'], q['study_id'], before, q, q['resolution'])
            return {'record': q}
        match = re.fullmatch(r'/api/participants/(SYN-[A-Za-z0-9-]+)/withdraw', path)
        if match:
            p = get(conn, 'participants', match[1])
            authorized(role, 'withdraw', p['study_id'])
            if not p['consent']:
                raise ApiError(409, 'Consent is already withdrawn.')
            before = dict(p)
            reason = text_field(data, 'reason', 500)
            p.update(consent=False, status='Withdrawn', withdrawn_at=stamp())
            save(conn, 'participants', p)
            audit(conn, role, 'CONSENT_WITHDRAWN', p['id'], p['study_id'], before, p, reason)
            return {'record': p}
        match = re.fullmatch(r'/api/visits/([A-Za-z0-9-]+)/complete', path)
        if match:
            v = get(conn, 'visits', match[1])
            authorized(role, 'visit', v['study_id'])
            p = get(conn, 'participants', v['participant_id'])
            if not p['consent']:
                raise ApiError(409, 'Routine study visit blocked after consent withdrawal.')
            study = get(conn, 'studies', p['study_id'])
            if p.get('reconsent_required') or p['consent_version'] != study.get('consent_version', study['protocol']):
                raise ApiError(409, 'Record consent to the current approved version before a routine visit.')
            if v['completed_at']:
                raise ApiError(409, 'Visit already completed.')
            if v['due'] > utcnow().date().isoformat():
                raise ApiError(409, 'This demo only records visits on or after their scheduled date.')
            before = dict(v)
            reason = text_field(data, 'reason', 500)
            v['completed_at'] = stamp()
            save(conn, 'visits', v)
            audit(conn, role, 'VISIT_COMPLETED', v['id'], v['study_id'], before, v, reason)
            return {'record': v}
        if path == '/api/settings':
            authorized(role, 'settings')
            before = get(conn, 'settings', 'alerts')
            settings = {'id': 'alerts', 'enrolment_threshold': number(data, 'enrolment_threshold', 1, 100), 'iec_days': number(data, 'iec_days', 1, 180), 'query_days': number(data, 'query_days', 1, 90), 'monitoring_days': number({**data, 'monitoring_days': data.get('monitoring_days', before.get('monitoring_days', 14))}, 'monitoring_days', 1, 180), 'deviation_days': number({**data, 'deviation_days': data.get('deviation_days', before.get('deviation_days', 7))}, 'deviation_days', 1, 90)}
            save(conn, 'settings', settings)
            audit(conn, role, 'ALERT_SETTINGS_UPDATED', 'alerts', before=before, after=settings, reason='Configured operational thresholds; statutory deadlines unchanged')
            return {'record': settings}
        if path == '/api/studies':
            authorized(role, 'study')
            target = number(data, 'target', 1, 10000)
            s = {'id': 'AIIA-' + secrets.token_hex(3).upper(), 'title': text_field(data, 'title', 120), 'condition': text_field(data, 'condition', 100), 'type': choice(data, 'type', ['Observational', 'Compound formulation', 'Single-herb formulation', 'Procedure', 'Whole-system regimen']), 'formulation': text_field(data, 'formulation', 200), 'batch': 'Not assigned', 'target': target, 'status': 'Setup', 'site': choice(data, 'site', ['Delhi', 'Goa', 'Jaipur']), 'pi': 'Not assigned', 'ctri': '', 'registered_at': '', 'iec_expiry': utcnow().date().isoformat(), 'iec_reference': 'Pending approval', 'protocol': '1.0', 'ndct': False, 'safety_hours': 24, 'start': utcnow().date().isoformat(), 'end': (utcnow() + timedelta(days=120)).date().isoformat(), 'created_at': stamp()}
            s.update(consent_version='1.0', iec_approved_at='', iec_expiry='', revision=1)
            save(conn, 'studies', s)
            study_operations.ensure_site(CORE, conn, s, role)
            audit(conn, role, 'STUDY_CREATED', s['id'], s['id'], after=s, reason='Draft study; enrolment locked pending regulatory review')
            return {'record': s}
        raise ApiError(404, 'Endpoint not found.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT', 8000)))
    parser.add_argument('--host', default='127.0.0.1')
    args = parser.parse_args()
    initialize()
    print(f'Anvaya synthetic demo: http://{args.host}:{args.port}', flush=True)
    print('Local demonstration only. No real participant data or regulatory submissions.', flush=True)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
