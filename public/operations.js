'use strict';
nav.push(['operations','calendar','Operations & alerts']);
workflowPages.operations=operationsPage;
let inspectionReport=null;

function operationsSites(studyId,active=false) {
    return (data.sites||[]).filter(s=>s.study_id===studyId&&(!active||s.status==='Active')).map(s=>[s.id,s.code+' · '+s.name]);
}
function enrolSiteField(studyId) {return select('Study site','site_id',operationsSites(studyId,true));}
function updateEnrolSites(form,studyId) {
    form.elements.site_id.innerHTML=operationsSites(studyId,true).map(([id,label])=>`<option value="${esc(id)}">${esc(label)}</option>`).join('');
}
function operationsParticipants(studyId,siteId) {
    return [['','No participant — study-level deviation'],...(data.participants||[]).filter(p=>p.study_id===studyId&&(!siteId||(p.site_id||'SITE-'+p.study_id)===siteId)).map(p=>[p.id,p.id])];
}
function operationsSection(title,body,note='') {
    return `<section class="card section-gap"><div class="card-header"><div><h2>${esc(title)}</h2>${note?`<p>${esc(note)}</p>`:''}</div></div>${body}</section>`;
}
function operationsPage() {
    const c=data.operations_counts||{},forecasts=(data.forecasts||[]).filter(match),batches=(data.batch_context||[]).filter(match);
    let actions=can('operations')?button('Add site','operations-new-site','','plus')+button('Plan monitoring','operations-new-monitoring','','calendar')+button('Record deviation','operations-new-deviation','primary','warn'):'';
    if(can('query'))actions+=button('Open data query','operations-new-query','','query');
    actions+=button('Pre-inspection report','operations-inspection','','shield');
    let html=heading('Operations & alerts','Sites, monitoring, deviations and operational oversight.',actions)+`<div class="stats">${stat('Study sites',c.sites||0,'','All assigned studies','studies')}${stat('Monitoring due',c.monitoring_due||0,'','Within configured horizon','calendar')}${stat('Open deviations',c.open_deviations||0,'','All assigned studies','warn')}${stat('Critical forecasts',c.critical_forecasts||0,'','Below 20% target probability','pulse')}</div>`+filters();
    const alerts=data.alerts.filter(match);
    html+=operationsSection('Alert inbox',alerts.length?table(['Severity','Study / alert','Rule / owner','Action'],alerts.map(a=>`<tr><td>${pill(a.level,a.level)}</td><td><strong>${esc(a.title)}</strong><small class="block muted">${esc(a.study_id)} · ${esc(a.detail)}</small></td><td>${esc(a.rule||operationsAlertRule(a))}<small class="block muted">${esc(a.owner||operationsAlertOwner(a))}</small></td><td><button class="button small" data-page="${esc(a.page)}">Review</button></td></tr>`).join('')):empty('No alerts at current thresholds.'),'Alerts update from saved records; no email or external dispatch is implied.');
    html+=operationsSection('Configured rules',details([['Recruitment pace',`Below ${data.settings.enrolment_threshold}% of expected`],['IEC expiry',`Within ${data.settings.iec_days} days`],['Open query age',`${data.settings.query_days} days`],['Monitoring due',`Within ${data.settings.monitoring_days} days`],['Open deviation age',`${data.settings.deviation_days} days`],['Forecast probability','Amber <50%; red <20%']])+(can('settings')?`<div class="button-row">${button('Edit thresholds','settings','small','settings')}</div>`:''),'Safety clocks follow the study pathway; missing registration is always flagged.');
    const forecastTable=forecasts.length?table(['Study','Target probability','Rate / projection','Uncertainty / status'],forecasts.map(f=>`<tr><td><strong>${esc(studyName(f.study_id))}</strong><small class="block muted">${f.enrolled} / ${f.target} enrolled · ${f.recent_enrolments} in ${f.observed_days} days</small></td><td><strong>${f.target_probability}%</strong><small class="block muted">by ${date(f.planned_end)}</small></td><td>${f.posterior_weekly_rate} / week<small class="block muted">Trailing rate: ${f.trailing_weekly_rate} / week<br>Rate-based date: ${f.projected_completion?date(f.projected_completion):'Beyond ten years'}</small></td><td>${pill(f.status,f.status==='Critical'?'danger':f.status==='At risk'?'warning':'')}<small class="block muted">90% range: ${f.predictive_enrolments_90.map(n=>n===null?'outside calculation limit':n).join('–')} additional enrolments by end</small></td></tr>`).join('')):empty('No recruiting studies match this view.');
    html+=operationsSection('Enrolment forecast',forecastTable,'Synthetic model: Gamma(0.5, rate 0.5 days) prior, up to 56 days of observations, constant future rate. Nominal ranges describe enrolment counts, not clinical outcomes; abrupt rate changes can invalidate them.');
    if(me.role!=='leadership') {
        const sites=(data.sites||[]).filter(match),monitoring=(data.monitoring_visits||[]).filter(match),deviations=(data.deviations||[]).filter(match);
        html+=operationsSection('Study sites',sites.length?table(['Site / study','Location','Investigator','Target','Status / action'],sites.map(s=>`<tr><td><strong>${esc(s.code)} · ${esc(s.name)}</strong><small class="block muted">${esc(s.study_id)}</small></td><td>${esc(s.city)}</td><td>${esc(s.investigator)}</td><td>${s.target}</td><td>${pill(s.status,s.status==='Setup'?'warning':'')}${s.status==='Setup'&&can('operations')?button('Activate','operations-activate-site','small','check',`data-id="${esc(s.id)}"`):''}</td></tr>`).join('')):empty(),'Site targets are planning values; study capacity remains the enrolment limit.');
        html+=operationsSection('Monitoring visits',monitoring.length?table(['Visit / study','Site / monitor','Schedule','Scope / findings','Status / action'],monitoring.map(v=>`<tr><td><strong>${esc(v.id)}</strong><small class="block muted">${esc(v.study_id)}</small></td><td>${esc(v.site_id)}<small class="block muted">${esc(v.monitor)}</small></td><td>${date(v.scheduled_date)}${v.overdue?'<small class="block countdown overdue">Overdue</small>':''}</td><td class="event-term">${esc(v.scope)}<small class="block muted">${esc(v.findings||'')}</small></td><td>${pill(v.status,v.overdue?'danger':v.status==='Planned'?'warning':'')}${v.status==='Planned'&&v.days_until_due<=0&&can('operations')?button('Complete','operations-complete-monitoring','small','check',`data-id="${esc(v.id)}"`):''}</td></tr>`).join('')):empty());
        html+=operationsSection('Protocol deviations',deviations.length?table(['Deviation / study','Category','Summary / corrective action','Owner / age','Status / action'],deviations.map(d=>`<tr><td><strong>${esc(d.id)}</strong><small class="block muted">${esc(d.study_id)}${d.participant_id?' · '+esc(d.participant_id):''}</small></td><td>${pill(d.category,d.category==='Major'?'danger':'warning')}</td><td class="event-term">${esc(d.summary)}<small class="block muted">${esc(d.corrective_action||'')}</small></td><td>${esc(d.owner)}<small class="block muted">${d.age_days} days</small></td><td>${pill(d.status,d.status==='Open'?'warning':'')}${d.status==='Open'&&can('operations')?button('Close','operations-close-deviation','small','check',`data-id="${esc(d.id)}"`):''}</td></tr>`).join('')):empty());
    }
    return html+operationsSection('Formulation and batch context',batches.length?table(['Study / configured batch','Formulation','Participants with AE','Serious events'],batches.map(b=>`<tr><td><strong>${esc(b.study_id)}</strong><small class="block muted">${esc(b.batch)}</small></td><td>${esc(b.formulation)}</td><td>${b.participants_with_events}</td><td>${b.serious_events}</td></tr>`).join('')):empty('No formulation batches match this view.'),'Study-level counts only. Individual exposure and event-batch attribution are unverified; these are not PRR, incidence rates or causal signals.');
}
function operationsAlertRule(alert) {
    if(alert.page==='queries')return `Open query age ≥ ${data.settings.query_days} days`;
    if(alert.page==='safety')return 'Configured case deadline or recipient obligation';
    if(alert.page==='studies')return `Recruitment pace < ${data.settings.enrolment_threshold}%`;
    return alert.title.includes('Registration')?'Registration reference required':`IEC expiry within ${data.settings.iec_days} days`;
}
function operationsAlertOwner(alert) {
    return {queries:'Data review team',safety:'Pharmacovigilance team',studies:'Study coordinator',compliance:'Investigator / ethics reviewer'}[alert.page]||'Study operations team';
}
async function operationsInspection() {
    const session=me.csrf;
    const report=await api('/api/operations/inspection'+(studyFilter?'?study='+encodeURIComponent(studyFilter):''));
    if(me?.csrf!==session||page!=='operations')return;
    inspectionReport={...report,session};
    modal('Pre-inspection readiness report','Saved-record summary for '+report.study_ids.join(', '),details([['Generated',timeLabel(report.generated_at)],['Current consent coverage',`${report.current_consent.current} / ${report.current_consent.active} active participants`],['Audit chain',report.audit?(report.audit.valid?'Verified':'Verification failed')+' · '+report.audit.entries+' events':'Unavailable to this role'],...Object.entries(report.checks).map(([label,count])=>[label.replaceAll('_',' '),count])])+`<p class="status-note section-gap">${esc(report.scope_note)} This report supports review; it does not certify inspection readiness.</p><div class="button-row">${button('Download HTML report','operations-download-report','small','export')}</div>`);
}
async function operationsWorkflowAction(action,el) {
    if(!action?.startsWith('operations-'))return false;
    if(action==='operations-inspection'){await operationsInspection();return true;}
    if(action==='operations-download-report') {
        if(!inspectionReport||inspectionReport.session!==me.csrf)throw Error('Generate a report in this session first.');
        const {session,...report}=inspectionReport;
        const html='<!doctype html><html lang="en"><meta charset="utf-8"><title>Anvaya pre-inspection summary</title><body><h1>Anvaya pre-inspection summary</h1><p>Synthetic records; this report does not certify readiness.</p><pre>'+esc(JSON.stringify(report,null,2))+'</pre></body></html>';
        const url=URL.createObjectURL(new Blob([html],{type:'text/html'})),a=document.createElement('a');a.href=url;a.download='anvaya-pre-inspection.html';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);return true;
    }
    const studies=data.studies.map(s=>[s.id,s.title]),studyId=studies[0]?.[0];
    if(action==='operations-new-query') {
        if(!can('query'))throw Error('Query permission is required.');
        modal('Open data query','Record the discrepancy and its review context.',formWrap('operations-query-form',select('Study','study_id',studies)+field('Field or record reference','field','text','','maxlength="120"')+textarea('Query','message','Describe the discrepancy without personal identifiers.',1000)+textarea('Reason','reason','Record source and review context.',500),'Open query'));return true;
    }
    if(!can('operations'))throw Error('Study-operations permission is required.');
    if(action==='operations-new-site') {
        modal('Add study site','Record site metadata; authorisation documents are reviewed separately.',formWrap('operations-site-form',select('Study','study_id',studies)+`<div class="form-grid">${field('Site code','code','text','','maxlength="30"')}${field('Site name','name','text','','maxlength="120"')}${field('City','city','text','','maxlength="80"')}${field('Investigator','investigator','text','','maxlength="120"')}${field('Site target','target','number','20','min="1" max="10000"')}${select('Status','status',['Setup','Active'])}</div>`+textarea('Creation evidence and reason','reason','Record the synthetic authorisation basis.',500),'Add site'));return true;
    }
    if(action==='operations-activate-site') {
        modal('Activate study site',el.dataset.id,formWrap('operations-site-activate-form',textarea('Activation evidence and reason','reason','Record the review basis; study readiness must pass.',500),'Activate site',`data-id="${esc(el.dataset.id)}"`));return true;
    }
    if(action==='operations-new-monitoring') {
        modal('Plan monitoring visit','Assign a site, monitor, date and review scope.',formWrap('operations-monitoring-form',select('Study','study_id',studies)+select('Site','site_id',operationsSites(studyId))+`<div class="form-grid">${field('Scheduled date','scheduled_date','date',data.server_time.slice(0,10))}${field('Monitor','monitor','text',me.name,'maxlength="120"')}</div>`+textarea('Monitoring scope','scope','State the records and controls to review.',300)+textarea('Planning reason','reason','Record why this visit is scheduled.',500),'Plan visit'));return true;
    }
    if(action==='operations-complete-monitoring') {
        modal('Complete monitoring visit',el.dataset.id,formWrap('operations-monitoring-complete-form',textarea('Findings','findings','Record synthetic findings and follow-up.',2000)+textarea('Completion evidence and reason','reason','Record the review basis.',500),'Complete visit',`data-id="${esc(el.dataset.id)}"`));return true;
    }
    if(action==='operations-new-deviation') {
        modal('Record protocol deviation','Preserve the event and route it for review.',formWrap('operations-deviation-form',select('Study','study_id',studies)+select('Site','site_id',operationsSites(studyId))+select('Participant (optional)','participant_id',operationsParticipants(studyId,operationsSites(studyId)[0]?.[0]))+`<div class="form-grid">${select('Category','category',['Minor','Major'])}${field('Occurrence date','occurred_date','date',data.server_time.slice(0,10))}${field('Owner','owner','text',me.name,'maxlength="120"')}</div>`+textarea('Deviation summary','summary','Describe the protocol departure without personal identifiers.',500)+textarea('Recording reason','reason','Record source and review context.',500),'Record deviation'));return true;
    }
    if(action==='operations-close-deviation') {
        modal('Close protocol deviation',el.dataset.id,formWrap('operations-deviation-close-form',textarea('Corrective and preventive action','corrective_action','Record correction, impact review and prevention.',2000)+textarea('Closure reason','reason','Record closure evidence and reviewer basis.',500),'Close deviation',`data-id="${esc(el.dataset.id)}"`));return true;
    }
    return false;
}
async function operationsWorkflowSubmit(form,fields) {
    let path,body=fields;
    if(form.id==='operations-site-form'){path='/api/sites';body={...fields,target:Number(fields.target)};}
    if(form.id==='operations-site-activate-form')path='/api/sites/'+form.dataset.id+'/activate';
    if(form.id==='operations-query-form')path='/api/queries';
    if(form.id==='operations-monitoring-form')path='/api/monitoring-visits';
    if(form.id==='operations-monitoring-complete-form')path='/api/monitoring-visits/'+form.dataset.id+'/complete';
    if(form.id==='operations-deviation-form')path='/api/deviations';
    if(form.id==='operations-deviation-close-form')path='/api/deviations/'+form.dataset.id+'/close';
    if(!path)return false;
    const session=me.csrf;
    await api(path,body);if(me?.csrf!==session)return true;
    document.querySelector('#modal').close();await refresh(true);if(me?.csrf===session)toast('Record saved with audit evidence.');return true;
}
document.addEventListener('change',event=>{
    const form=event.target.form;
    if(!form||!['operations-monitoring-form','operations-deviation-form'].includes(form.id))return;
    if(event.target.name==='study_id')form.elements.site_id.innerHTML=operationsSites(event.target.value).map(([id,label])=>`<option value="${esc(id)}">${esc(label)}</option>`).join('');
    if(form.elements.participant_id&&['study_id','site_id'].includes(event.target.name))form.elements.participant_id.innerHTML=operationsParticipants(form.elements.study_id.value,form.elements.site_id.value).map(([id,label])=>`<option value="${esc(id)}">${esc(label)}</option>`).join('');
});
