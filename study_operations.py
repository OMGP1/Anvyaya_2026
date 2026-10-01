"""Multi-site operations, monitoring, deviations and explainable synthetic forecasts."""
import math
import re
import secrets
from datetime import datetime, timedelta


def ensure_site(core, conn, study, actor='system:operations-migration'):
    existing = [s for s in core.rows(conn, 'sites') if s['study_id'] == study['id']]
    if existing:
        return existing[0]
    site = {
        'id': 'SITE-' + study['id'],
        'study_id': study['id'],
        'code': 'PRIMARY',
        'name': study['site'] + ' research site',
        'city': study['site'],
        'investigator': study.get('pi', 'Not assigned'),
        'target': study['target'],
        'status': 'Setup' if study['status'] == 'Setup' else 'Active',
        'created_at': core.stamp(),
    }
    core.save(conn, 'sites', site)
    core.audit(conn, actor, 'PRIMARY_SITE_CREATED', site['id'], study['id'], after=site,
               reason='Primary site derived from recorded study metadata; no external site approval verified.')
    return site


def seed(core, conn, examples=False):
    studies = core.rows(conn, 'studies')
    if not studies:
        return
    primary = {s['id']: ensure_site(core, conn, s) for s in studies}
    settings = core.get(conn, 'settings', 'alerts')
    before = dict(settings)
    changed = False
    for key, value in [('monitoring_days', 14), ('deviation_days', 7)]:
        if key not in settings:
            settings[key] = value
            changed = True
    if changed:
        core.save(conn, 'settings', settings)
        core.audit(conn, 'system:operations-migration', 'ALERT_DEFAULTS_ADDED', 'alerts',
                   before=before, after=settings, reason='Add monitoring and deviation alert defaults; preserve existing settings.')
    if not examples:
        return
    if not core.rows(conn, 'monitoring_visits'):
        today = core.utcnow().date()
        records = [
            ('MON-001', 'AIIA-001', -9, 'Planned', 'Routine risk-based monitoring'),
            ('MON-002', 'AIIA-002', 8, 'Planned', 'Consent and source-record review'),
            ('MON-003', 'AIIA-003', -18, 'Completed', 'Initial site monitoring'),
        ]
        for ident, study_id, offset, status, scope in records:
            record = {'id': ident, 'study_id': study_id, 'site_id': primary[study_id]['id'],
                      'scheduled_date': (today + timedelta(days=offset)).isoformat(), 'scope': scope,
                      'monitor': 'Synthetic monitor', 'status': status, 'created_at': core.stamp()}
            if status == 'Completed':
                record.update(completed_at=core.stamp(), findings='Synthetic review completed; no clinical conclusion.')
            core.save(conn, 'monitoring_visits', record)
            core.audit(conn, 'system:synthetic-seed', 'MONITORING_SEEDED', ident, study_id, after=record)
    if not core.rows(conn, 'deviations'):
        today = core.utcnow().date()
        for ident, study_id, days, category, status, summary in [
            ('DEV-001', 'AIIA-001', 11, 'Major', 'Open', 'Synthetic visit-window deviation under review'),
            ('DEV-002', 'AIIA-002', 3, 'Minor', 'Open', 'Synthetic documentation timing deviation'),
            ('DEV-003', 'AIIA-003', 20, 'Minor', 'Closed', 'Synthetic source-note correction'),
        ]:
            record = {'id': ident, 'study_id': study_id, 'site_id': primary[study_id]['id'],
                      'participant_id': '', 'category': category, 'summary': summary,
                      'occurred_date': (today - timedelta(days=days)).isoformat(), 'owner': 'Study team',
                      'status': status, 'created_at': core.stamp()}
            if status == 'Closed':
                record.update(closed_at=core.stamp(), corrective_action='Synthetic correction reviewed and documented.')
            core.save(conn, 'deviations', record)
            core.audit(conn, 'system:synthetic-seed', 'DEVIATION_SEEDED', ident, study_id, after=record)


def activate_primary(core, conn, role, study, reason):
    site = core.get(conn, 'sites', 'SITE-' + study['id'])
    before = dict(site)
    site.update(status='Active', investigator=study['pi'], target=study['target'])
    core.save(conn, 'sites', site)
    core.audit(conn, role, 'PRIMARY_SITE_ACTIVATED', site['id'], study['id'], before, site, reason)


def _predictive(alpha, beta, days, remaining):
    """Exact negative-binomial mixture; log masses avoid underflow at count zero."""
    if days <= 0:
        return float(remaining <= 0), [0, 0]
    log_p = math.log(beta / (beta + days))
    log_q = math.log(days / (beta + days))
    mean = alpha * days / beta
    variance = mean * (1 + days / beta)
    # Bound work for pathological dates/targets; null quantiles remain explicit.
    limit = min(100000, max(remaining, math.ceil(mean + 15 * math.sqrt(variance)) + 100))
    mass_log, cumulative, below = alpha * log_p, 0.0, 0.0
    interval = [None, None]
    for count in range(limit + 1):
        mass = math.exp(mass_log)
        cumulative += mass
        if count < remaining:
            below += mass
        for i, quantile in enumerate((.05, .95)):
            if interval[i] is None and cumulative >= quantile:
                interval[i] = count
        if count >= remaining and interval[1] is not None:
            break
        mass_log += math.log(count + alpha) - math.log(count + 1) + log_q
    return max(0.0, min(1.0, 1 - below)), interval


def resolve_site(core, conn, role, study_id, site_id=None):
    core.authorized(role, study_id=study_id)
    sites = [s for s in core.rows(conn, 'sites') if s['study_id'] == study_id and s['status'] == 'Active']
    # Legacy enrolments and the existing CSV mapping resolve only to the primary site.
    site_id = site_id or 'SITE-' + study_id
    sites = [s for s in sites if s['id'] == site_id]
    if not sites:
        raise core.ApiError(409, 'Choose an active site assigned to this study.')
    return sites[0]


def _forecast(study, participants, today):
    enrolled = [p for p in participants if p['study_id'] == study['id'] and p['enrolled_at'][:10] <= today.isoformat()]
    remaining = max(0, study['target'] - len(enrolled))
    start = max(datetime.fromisoformat(study['start']).date(), today - timedelta(days=55))
    observed_days = max(1, (today - start).days + 1)
    recent = sum(start.isoformat() <= p['enrolled_at'][:10] <= today.isoformat() for p in enrolled)
    alpha, beta = .5 + recent, .5 + observed_days
    future_days = max(0, (datetime.fromisoformat(study['end']).date() - today).days)
    probability, interval = _predictive(alpha, beta, future_days, remaining)
    daily_rate = alpha / beta
    projected_days = math.ceil(remaining / daily_rate) if remaining else 0
    projected = (today + timedelta(days=projected_days)).isoformat() if projected_days <= 3650 else None
    percentage = round(probability * 100, 2)
    return {
        'study_id': study['id'], 'target': study['target'], 'enrolled': len(enrolled),
        'recent_enrolments': recent, 'observed_days': observed_days,
        'posterior_weekly_rate': round(daily_rate * 7, 2),
        'target_probability': percentage, 'target_probability_raw': probability,
        'projected_completion': projected, 'predictive_enrolments_90': interval,
        'trailing_weekly_rate': round(recent / observed_days * 7, 2),
        'planned_end': study['end'],
        'status': 'On track' if probability >= .5 else 'At risk' if probability >= .2 else 'Critical',
        'method': 'Gamma-Poisson synthetic operational forecast',
    }


def _batch_context(studies, participants, events):
    participant_study = {p['id']: p['study_id'] for p in participants}
    cases = {study['id']: set() for study in studies}
    serious = {study['id']: 0 for study in studies}
    for event in events:
        study_id = participant_study.get(event['participant_id'])
        if study_id in cases:
            cases[study_id].add(event['participant_id'])
            serious[study_id] += int(event['serious'])
    results = []
    for study in studies:
        if study['type'] not in {'Compound formulation', 'Single-herb formulation'} or not study.get('batch') or study['batch'] in {'Not assigned', 'Pending'}:
            continue
        results.append({'study_id': study['id'], 'batch': study['batch'], 'formulation': study['formulation'],
                        'participants_with_events': len(cases[study['id']]), 'serious_events': serious[study['id']],
                        'method': 'Study-level context only; individual exposure and event-batch attribution unverified'})
    return results


def snapshot(core, conn, role, studies, participants, events, settings):
    today = core.utcnow().date()
    sites = core.scoped(core.rows(conn, 'sites'), role)
    monitoring = core.scoped(core.rows(conn, 'monitoring_visits'), role)
    deviations = core.scoped(core.rows(conn, 'deviations'), role)
    alerts = []
    monitoring_days = settings.get('monitoring_days', 14)
    deviation_days = settings.get('deviation_days', 7)
    for visit in monitoring:
        days = (datetime.fromisoformat(visit['scheduled_date']).date() - today).days
        visit['days_until_due'] = days
        visit['overdue'] = visit['status'] == 'Planned' and days < 0
        if visit['status'] == 'Planned' and days <= monitoring_days:
            alerts.append({'level': 'danger' if days < 0 else 'warning',
                           'title': 'Monitoring visit overdue' if days < 0 else f'Monitoring visit due in {days} days',
                           'detail': visit['id'] + ' · ' + visit['scope'], 'study_id': visit['study_id'],
                           'page': 'operations', 'rule': f'Planned visit within {monitoring_days} days', 'owner': 'Clinical monitor'})
    for deviation in deviations:
        age = (today - datetime.fromisoformat(deviation['occurred_date']).date()).days
        deviation['age_days'] = age
        if deviation['status'] == 'Open' and age >= deviation_days:
            alerts.append({'level': 'danger' if deviation['category'] == 'Major' else 'warning',
                           'title': f'{deviation["category"]} deviation open {age} days',
                           'detail': deviation['id'] + ' · ' + deviation['summary'], 'study_id': deviation['study_id'],
                           'page': 'operations', 'rule': f'Open deviation age ≥ {deviation_days} days', 'owner': deviation['owner']})
    forecasts = [_forecast(study, participants, today) for study in studies if study['status'] == 'Recruiting']
    for forecast in forecasts:
        if forecast['target_probability_raw'] < .5:
            alerts.append({'level': 'danger' if forecast['target_probability_raw'] < .2 else 'warning',
                           'title': f'Target attainment probability {forecast["target_probability"]}%',
                           'detail': forecast['study_id'] + ' · projected ' + (forecast['projected_completion'] or 'beyond ten-year display horizon'),
                           'study_id': forecast['study_id'], 'page': 'operations',
                           'rule': 'Amber <50%; red <20% by planned end', 'owner': 'Study coordinator'})
    result = {'sites': sites, 'monitoring_visits': monitoring, 'deviations': deviations,
              'forecasts': forecasts, 'batch_context': _batch_context(studies, participants, events),
              'operation_alerts': alerts,
              'operations_counts': {'sites': len(sites),
                                    'monitoring_due': sum(v['status'] == 'Planned' and v['days_until_due'] <= monitoring_days for v in monitoring),
                                    'open_deviations': sum(d['status'] == 'Open' for d in deviations),
                                    'critical_forecasts': sum(f['status'] == 'Critical' for f in forecasts)}}
    if core.role_key(role) == 'leadership':
        result.update(sites=[], monitoring_visits=[], deviations=[])
        for alert in alerts:
            alert.update(detail=alert['study_id'] + ' · aggregate operational alert', owner='Study oversight team')
    return result


def mutate(core, conn, role, path, data):
    match = re.fullmatch(r'/api/sites/([A-Za-z0-9-]+)/activate', path)
    if match:
        site = core.get(conn, 'sites', match[1])
        core.authorized(role, 'operations', site['study_id'])
        study = core.get(conn, 'studies', site['study_id'])
        if site['status'] != 'Setup':
            raise core.ApiError(409, 'Site is already active.')
        if study['status'] != 'Recruiting' or not core.study_readiness(study)['ready']:
            raise core.ApiError(409, 'Site activation requires a recruiting study with current readiness checks.')
        reason = core.text_field(data, 'reason', 500)
        before = dict(site)
        site['status'] = 'Active'
        core.save(conn, 'sites', site)
        core.audit(conn, role, 'SITE_ACTIVATED', site['id'], site['study_id'], before, site, reason)
        return {'record': site}
    if path == '/api/queries':
        study_id = core.text_field(data, 'study_id')
        core.authorized(role, 'query', study_id)
        core.get(conn, 'studies', study_id)
        query = {'id': 'DQ-' + secrets.token_hex(4).upper(), 'study_id': study_id,
                 'field': core.text_field(data, 'field', 120), 'message': core.text_field(data, 'message', 1000),
                 'status': 'Open', 'opened_at': core.stamp(), 'resolution': ''}
        reason = core.text_field(data, 'reason', 500)
        core.save(conn, 'queries', query)
        core.audit(conn, role, 'QUERY_OPENED', query['id'], study_id, after=query, reason=reason)
        return {'record': query}
    if path == '/api/sites':
        study_id = core.text_field(data, 'study_id')
        core.authorized(role, 'operations', study_id)
        study = core.get(conn, 'studies', study_id)
        code = core.text_field(data, 'code', 30).upper()
        if not re.fullmatch(r'[A-Z0-9-]{2,30}', code):
            raise core.ApiError(400, 'Site code must use 2–30 letters, numbers or hyphens.')
        if any(s['study_id'] == study_id and s['code'] == code for s in core.rows(conn, 'sites')):
            raise core.ApiError(409, 'This site code already exists in the study.')
        site = {'id': 'SITE-' + secrets.token_hex(4).upper(), 'study_id': study_id, 'code': code,
                'name': core.text_field(data, 'name', 120), 'city': core.text_field(data, 'city', 80),
                'investigator': core.text_field(data, 'investigator', 120),
                'target': core.number(data, 'target', 1, 10000), 'status': core.choice(data, 'status', ['Setup', 'Active']),
                'created_at': core.stamp()}
        if site['status'] == 'Active' and (study['status'] != 'Recruiting' or not core.study_readiness(study)['ready']):
            raise core.ApiError(409, 'An active site requires a recruiting study with current readiness checks.')
        core.save(conn, 'sites', site)
        reason = core.text_field(data, 'reason', 500)
        core.audit(conn, role, 'SITE_CREATED', site['id'], study_id, after=site, reason=reason)
        return {'record': site}
    if path == '/api/monitoring-visits':
        study_id = core.text_field(data, 'study_id')
        core.authorized(role, 'operations', study_id)
        site = core.get(conn, 'sites', core.text_field(data, 'site_id'))
        if site['study_id'] != study_id:
            raise core.ApiError(409, 'Monitoring site does not belong to the selected study.')
        visit = {'id': 'MON-' + secrets.token_hex(4).upper(), 'study_id': study_id, 'site_id': site['id'],
                 'scheduled_date': core.calendar_date(data, 'scheduled_date'),
                 'scope': core.text_field(data, 'scope', 300), 'monitor': core.text_field(data, 'monitor', 120),
                 'status': 'Planned', 'created_at': core.stamp()}
        core.save(conn, 'monitoring_visits', visit)
        reason = core.text_field(data, 'reason', 500)
        core.audit(conn, role, 'MONITORING_VISIT_PLANNED', visit['id'], study_id, after=visit, reason=reason)
        return {'record': visit}
    match = re.fullmatch(r'/api/monitoring-visits/([A-Za-z0-9-]+)/complete', path)
    if match:
        visit = core.get(conn, 'monitoring_visits', match[1])
        core.authorized(role, 'operations', visit['study_id'])
        if visit['status'] != 'Planned':
            raise core.ApiError(409, 'Monitoring visit is already completed.')
        if visit['scheduled_date'] > core.utcnow().date().isoformat():
            raise core.ApiError(409, 'A future monitoring visit cannot be completed before its scheduled date.')
        before = dict(visit)
        reason = core.text_field(data, 'reason', 500)
        visit.update(status='Completed', completed_at=core.stamp(), findings=core.text_field(data, 'findings', 2000))
        core.save(conn, 'monitoring_visits', visit)
        core.audit(conn, role, 'MONITORING_VISIT_COMPLETED', visit['id'], visit['study_id'], before, visit, reason)
        return {'record': visit}
    if path == '/api/deviations':
        study_id = core.text_field(data, 'study_id')
        core.authorized(role, 'operations', study_id)
        site = core.get(conn, 'sites', core.text_field(data, 'site_id'))
        if site['study_id'] != study_id:
            raise core.ApiError(409, 'Deviation site does not belong to the selected study.')
        participant_id = core.text_field(data, 'participant_id', 80, required=False)
        if participant_id:
            participant = core.get(conn, 'participants', participant_id)
            if participant['study_id'] != study_id or participant.get('site_id', 'SITE-' + study_id) != site['id']:
                raise core.ApiError(409, 'Participant does not belong to the selected study and site.')
        deviation = {'id': 'DEV-' + secrets.token_hex(4).upper(), 'study_id': study_id, 'site_id': site['id'],
                     'participant_id': participant_id, 'category': core.choice(data, 'category', ['Major', 'Minor']),
                     'summary': core.text_field(data, 'summary', 500),
                     'occurred_date': core.calendar_date(data, 'occurred_date'),
                     'owner': core.text_field(data, 'owner', 120), 'status': 'Open', 'created_at': core.stamp()}
        if deviation['occurred_date'] > core.utcnow().date().isoformat():
            raise core.ApiError(400, 'Deviation occurrence date cannot be in the future.')
        core.save(conn, 'deviations', deviation)
        reason = core.text_field(data, 'reason', 500)
        core.audit(conn, role, 'DEVIATION_RECORDED', deviation['id'], study_id, after=deviation, reason=reason)
        return {'record': deviation}
    match = re.fullmatch(r'/api/deviations/([A-Za-z0-9-]+)/close', path)
    if match:
        deviation = core.get(conn, 'deviations', match[1])
        core.authorized(role, 'operations', deviation['study_id'])
        if deviation['status'] != 'Open':
            raise core.ApiError(409, 'Deviation is already closed.')
        before = dict(deviation)
        reason = core.text_field(data, 'reason', 500)
        deviation.update(status='Closed', closed_at=core.stamp(),
                         corrective_action=core.text_field(data, 'corrective_action', 2000))
        core.save(conn, 'deviations', deviation)
        core.audit(conn, role, 'DEVIATION_CLOSED', deviation['id'], deviation['study_id'], before, deviation, reason)
        return {'record': deviation}
    return None


def inspection(core, conn, role, study_id=None):
    """One scoped read transaction, aggregate-only output, no regulatory verdict."""
    if not conn.in_transaction:
        conn.execute('BEGIN')
    studies = core.scoped(core.rows(conn, 'studies'), role, True)
    if study_id:
        core.authorized(role, study_id=study_id)
        core.get(conn, 'studies', study_id)
        studies = [s for s in studies if s['id'] == study_id]
    ids = {s['id'] for s in studies}
    selected = lambda table: [r for r in core.rows(conn, table) if r['study_id'] in ids]
    study_map = {s['id']: s for s in studies}
    participants = selected('participants')
    active = [p for p in participants if p['status'] == 'Enrolled']
    consented = [p for p in active if p['consent'] and not p.get('reconsent_required') and
                 p['consent_version'] == study_map[p['study_id']].get('consent_version', study_map[p['study_id']]['protocol'])]
    today, now = core.utcnow().date().isoformat(), core.stamp()
    events = [core.event_deadlines(e, study_map[e['study_id']]) for e in selected('events')]
    checks = {
        'studies_with_readiness_blockers': sum(not core.study_readiness(s)['ready'] for s in studies),
        'active_participants_without_current_consent': len(active) - len(consented),
        'expired_iec_approvals': sum(bool(s['iec_expiry']) and s['iec_expiry'] < today for s in studies),
        'documents_awaiting_review': sum(d['status'] == 'Submitted' for d in selected('documents')),
        'overdue_safety_steps': sum(bool(e.get(due)) and e[due] < now and not e.get(done)
                                   for e in events for due, done in [('initial_due', 'reported_at'), ('analysis_due', 'analysis_at')]),
        'overdue_recipient_followups': sum(o['status'] != 'Acknowledged' and o['due_at'] < now for o in selected('obligations')),
        'open_deviations': sum(d['status'] == 'Open' for d in selected('deviations')),
        'overdue_monitoring': sum(v['status'] == 'Planned' and v['scheduled_date'] < today for v in selected('monitoring_visits')),
        'open_queries': sum(q['status'] == 'Open' for q in selected('queries')),
    }
    return {'generated_at': now, 'study_ids': sorted(ids), 'checks': checks,
            'current_consent': {'active': len(active), 'current': len(consented)},
            'audit': core.verify_audit(conn) if 'audit' in core.role_info(role)['permissions'] else None,
            'scope_note': 'Counts may overlap. Missing uploads and external approval authenticity are not verified. Audit verification covers the full stored chain.'}
