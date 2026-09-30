'use strict';

function safetyLocalTime(value=new Date().toISOString()) {
    const d=new Date(value);
    return new Date(d-d.getTimezoneOffset()*60000).toISOString().slice(0,19);
}

function safetyActions(event) {
    const coded=event.coded_term,history=event.coding_history||[];
    const obligations=(data.obligations||[]).filter(o=>o.event_id===event.id);
    const coding=coded?details([['Reviewed code',coded.code+' · '+coded.label],['Dictionary release',coded.name+' · '+coded.version],['Dictionary kind',coded.kind],['Reviewer',coded.reviewer],['Reviewed at',timeLabel(coded.reviewed_at)]]):'<p class="status-note">No reviewed dictionary code is recorded. The verbatim event remains unchanged.</p>';
    const reviewHistory=history.length?`<details class="section-gap"><summary>Previous coding decisions (${history.length})</summary>${table(['Code / label','Release','Reviewer / time'],history.map(c=>`<tr><td class="event-term">${esc(c.code)}<small class="block muted">${esc(c.label)}</small></td><td>${esc(c.name)}<small class="block muted">${esc(c.kind)} · ${esc(c.version)}</small></td><td>${esc(c.reviewer)}<small class="block muted">${esc(timeLabel(c.reviewed_at))}</small></td></tr>`).join(''))}</details>`:'';
    const controls=(can('safety')||can('report'))?button('Review code suggestions','safety-suggestions','','search',`data-event-id="${esc(event.id)}"`):'';
    return `<section class="section-gap"><h3>Dictionary coding</h3>${coding}${reviewHistory}<div class="button-row section-gap">${controls}${can('settings')?button('Terminology packages','dictionaries','small','settings'):''}</div>${can('report')&&!me.user_id?'<p class="status-note section-gap">Sign in with a named account to confirm a coding decision. Demo roles can inspect lexical suggestions.</p>':''}</section><section class="section-gap"><div class="button-row"><h3>Recipient follow-up</h3>${can('report')?button('Add recipient obligation','safety-new-obligation','small','plus',`data-event-id="${esc(event.id)}"`):''}</div><p class="status-note section-gap">Track an assigned recipient, deadline, actual dispatch and acknowledgment. These actions record external activity; this application does not send reports or escalation messages.</p>${obligations.length?table(['Recipient / phase','Owner / due','Status','Follow-up'],obligations.map(o=>`<tr><td class="event-term">${esc(o.recipient)}<small class="block muted">${o.phase==='analysis'?'Analysis':'Initial'} · ${esc(o.id)}</small></td><td>${esc(o.assignee_name)}<small class="block muted">${esc(timeLabel(o.due_at))}</small></td><td>${pill(o.status,o.status==='Acknowledged'?'':o.overdue?'danger':'warning')}${o.overdue?'<small class="block countdown overdue">Overdue</small>':''}</td><td>${safetyObligationActions(o)}</td></tr>`).join('')):'<p class="muted">No recipient obligations recorded for this event.</p>'}${obligations.map(safetyObligationEvidence).join('')}</section>`;
}

function safetyObligationActions(o) {
    if(!can('report'))return '<span class="muted">Read only</span>';
    const attrs=`data-id="${esc(o.id)}" data-event-id="${esc(o.event_id)}"`;
    return `<div class="button-row">${o.status==='Awaiting dispatch'?button('Record dispatch','safety-dispatch','small','',attrs):o.status==='Awaiting receipt'?button('Record receipt','safety-receipt','small','',attrs):''}${o.status!=='Acknowledged'?button('Record escalation','safety-escalate','small','',attrs):''}</div>`;
}

function safetyObligationEvidence(o) {
    return `<details class="section-gap"><summary>${esc(o.recipient)} · ${o.phase==='analysis'?'Analysis':'Initial'} evidence · ${(o.escalations||[]).length} escalations</summary>${details([['Rule basis / reason',o.rule_basis],['Assigned account',o.assignee_id],['Created',timeLabel(o.created_at)+' · '+o.created_by],['Actual dispatch',timeLabel(o.sent_at)],['Dispatch reference',o.dispatch_reference||'Not recorded'],['Dispatch entered',o.dispatch_entered_at?timeLabel(o.dispatch_entered_at)+' · '+o.dispatch_recorded_by:'Not recorded'],['Actual receipt',timeLabel(o.received_at)],['Receipt reference',o.receipt_reference||'Not recorded'],['Receipt entered',o.receipt_entered_at?timeLabel(o.receipt_entered_at)+' · '+o.receipt_recorded_by:'Not recorded']])}${(o.escalations||[]).map(e=>`<div class="timeline-event"><small>${esc(timeLabel(e.at))} · ${esc(e.actor)}</small><strong>${esc(e.reason)}</strong></div>`).join('')}</details>`;
}

function showSafetyDictionaries() {
    const dictionaries=data.dictionaries||[];
    const sample={name:'Fictional demonstration terms',version:'demo-1',kind:'Synthetic',terms:[{code:'DEMO-NAUSEA',label:'Synthetic nausea'},{code:'DEMO-DIZZINESS',label:'Synthetic dizziness'},{code:'DEMO-IRRITATION',label:'Synthetic skin irritation'}]};
    const metadata=dictionaries.length?table(['Package / version','Kind / terms','Provenance'],dictionaries.map(d=>`<tr><td class="event-term">${esc(d.name)}<small class="block muted">${esc(d.version)} · ${esc(d.id)}</small></td><td>${pill(d.kind,d.kind==='Synthetic'?'neutral':'warning')}<small class="block muted">${esc(d.term_count)} terms</small></td><td class="event-term">${esc(d.imported_by)}<small class="block muted">${esc(timeLabel(d.imported_at))}</small><details><summary>Release evidence</summary><p>${esc(d.licence_verification)}</p><p class="hash">SHA-256: ${esc(d.sha256)}</p></details></td></tr>`).join('')):'<p class="status-note">No terminology packages imported.</p>';
    const upload=can('settings')&&me.user_id?formWrap('safety-dictionary-form',`<h3 class="section-gap">Import an immutable release</h3><p class="status-note section-gap">Upload JSON or edit the fictional sample below. Supply a name, version, kind and 1–2,000 code/label pairs. Existing releases cannot be overwritten. WHODrug packages describe medicinal products and are excluded from adverse-event suggestions.</p><label class="field"><span>Dictionary JSON file (optional, up to 700 KiB)</span><input name="dictionary_file" type="file" accept=".json,application/json"></label><label class="field"><span>Dictionary JSON</span><textarea name="dictionary_json" rows="10" maxlength="716800" required>${esc(JSON.stringify(sample,null,2))}</textarea></label><label class="checkbox"><input name="licence_confirmed" type="checkbox"><span>For a MedDRA or WHODrug package, I confirm that my institution has permission to use this supplied release. This declaration is not independent licence verification. No confirmation is needed for Synthetic terms.</span></label>`,'Import terminology release'):can('settings')?'<p class="status-note section-gap">Sign in with a named administrator account to import an attributable terminology release.</p>':'';
    modal('Terminology packages','No licensed dictionary terms are bundled. The sample codes and labels are fictional.',metadata+upload);
}

function safetySuggestionsForm(event,selected='') {
    const dictionaries=(data.dictionaries||[]).filter(d=>['Synthetic','MedDRA'].includes(d.kind));
    dictionaries.sort((a,b)=>Number(b.id===selected)-Number(a.id===selected));
    if(!dictionaries.length)return '<p class="status-note">A named administrator must import a Synthetic or authorised MedDRA package before suggestions can be requested.</p>';
    return formWrap('safety-suggestions-form',select('Dictionary release','dictionary_id',dictionaries.map(d=>[d.id,d.name+' · '+d.version+' · '+d.kind])),'Find lexical suggestions',`data-event-id="${esc(event.id)}"`);
}

function showSafetySuggestions(event,result) {
    let content=details([['Verbatim event',event.term]])+safetySuggestionsForm(event,result?.dictionary.id);
    if(result) {
        content+=`<p class="status-note section-gap">${esc(result.method)} Only candidates at or above the ${esc(result.threshold)} lexical threshold appear, up to five. A named reporting reviewer must confirm any code; no automatic coding occurs.</p>`;
        content+=result.abstained?'<p class="status-note warning">Abstained: no label met the lexical similarity threshold. The event remains unchanged; consult an appropriate reviewer and terminology release.</p>':table(['Code / label','Lexical score','Review'],result.candidates.map(c=>`<tr><td class="event-term"><strong>${esc(c.code)}</strong><small class="block muted">${esc(c.label)}</small></td><td>${esc(Number(c.lexical_similarity).toFixed(4))}</td><td>${can('report')&&me.user_id?button('Review this code','safety-code-select','small','',`data-event-id="${esc(event.id)}" data-dictionary-id="${esc(result.dictionary.id)}" data-code="${esc(c.code)}" data-label="${esc(c.label)}"`):'<span class="muted">Named reporting reviewer required</span>'}</td></tr>`).join(''));
    }
    content+=`<div class="button-row section-gap">${button('Back to safety record','event-detail','small','',`data-id="${esc(event.id)}"`)}${can('settings')?button('Terminology packages','dictionaries','small','settings'):''}</div>`;
    modal('Review coding suggestions',event.id+' · Preserve the verbatim event and review the dictionary context.',content);
}

async function safetyWorkflowAction(action,el) {
    if(action==='dictionaries') {showSafetyDictionaries();return true;}
    if(!['safety-suggestions','safety-code-select','safety-new-obligation','safety-dispatch','safety-receipt','safety-escalate'].includes(action))return false;
    const event=data.events.find(e=>e.id===el.dataset.eventId);
    if(!event)throw Error('This safety event is no longer available in your assigned studies.');
    if(action==='safety-suggestions') {
        if(!can('safety')&&!can('report'))throw Error('Safety workflow access is required.');
        showSafetySuggestions(event);return true;
    }
    if(!can('report'))throw Error('Reporting permission is required.');
    if(action==='safety-code-select') {
        if(!me.user_id)throw Error('Use a named account to confirm a coding decision.');
        const dictionary=(data.dictionaries||[]).find(d=>d.id===el.dataset.dictionaryId);
        if(!dictionary)throw Error('This dictionary release is no longer available.');
        modal('Confirm reviewed coding',event.id+' · The code is recorded with your account and dictionary version.',formWrap('safety-coding-form',details([['Verbatim event',event.term],['Selected label',el.dataset.label],['Dictionary',dictionary.name+' · '+dictionary.version],['Kind',dictionary.kind]])+field('Selected code','code','text',el.dataset.code,'readonly')+textarea('Review reason','reason','Explain why this dictionary term represents the verbatim report. No causality decision is inferred.'),'Record reviewed code',`data-event-id="${esc(event.id)}" data-dictionary-id="${esc(dictionary.id)}"`));return true;
    }
    if(action==='safety-new-obligation') {
        const requestSession=me.csrf;
        const result=await api('/api/safety/'+encodeURIComponent(event.id)+'/assignees');
        if(me?.csrf!==requestSession)return true;
        if(!result.assignees.length)throw Error('Create or assign an active named reporting user with access to this study before adding a recipient obligation.');
        modal('Add recipient obligation',event.id+' · Manually record the recipient and applicable reporting basis.',formWrap('safety-obligation-form',field('Recipient / organisation','recipient','text','','maxlength="160"')+`<div class="form-grid">${select('Reporting phase','phase',[['initial','Initial'],['analysis','Analysis']])}${select('Responsible account','assignee_id',result.assignees.map(u=>[u.id,u.name+' · '+(roles[u.role]?.label||u.role)]))}</div>`+field('Due time (your local time)','due_at','datetime-local',event.initial_due?safetyLocalTime(event.initial_due):'','step="1"')+textarea('Rule basis and reason','reason','Identify the recipient requirement, applicable rule or approved SOP, and why this deadline and owner apply.')+'<p class="status-note">The initial event deadline is prefilled when available. Confirm each recipient’s actual requirements; adding this record does not establish a legal reporting obligation or send a report.</p>','Add recipient obligation',`data-event-id="${esc(event.id)}"`));return true;
    }
    const obligation=(data.obligations||[]).find(o=>o.id===el.dataset.id&&o.event_id===event.id);
    if(!obligation)throw Error('This recipient obligation is no longer available.');
    const operation=action.replace('safety-','');
    if((operation==='dispatch'&&obligation.status!=='Awaiting dispatch')||(operation==='receipt'&&obligation.status!=='Awaiting receipt')||(operation==='escalate'&&obligation.status==='Acknowledged'))throw Error('This follow-up state has changed. Reopen the safety record.');
    const timeField=operation==='dispatch'?'sent_at':'received_at';
    const fields=operation==='escalate'?'':field(operation==='dispatch'?'Actual dispatch time (your local time)':'Actual receipt time (your local time)',timeField,'datetime-local',safetyLocalTime(),'step="1"')+field(operation==='dispatch'?'External dispatch reference':'External acknowledgment reference','reference','text','','maxlength="160"');
    modal(operation==='escalate'?'Record escalation':'Record '+operation,obligation.recipient+' · '+obligation.phase+' · '+event.id,formWrap('safety-followup-form',details([['Status',obligation.status],['Assigned account',obligation.assignee_name],['Due',timeLabel(obligation.due_at)]])+fields+textarea(operation==='escalate'?'Escalation action and reason':'Evidence and reason','reason',operation==='escalate'?'Describe the follow-up already performed, recipient contacted and next step.':'Describe supporting evidence and explain any delay.')+'<p class="status-note">This records external activity only. No report, acknowledgment or escalation message is sent by the application.</p>',operation==='escalate'?'Record escalation':'Record '+operation,`data-id="${esc(obligation.id)}" data-event-id="${esc(event.id)}" data-operation="${operation}"`));
    return true;
}

async function safetyWorkflowSubmit(form,fields) {
    let path,body,message;
    const requestSession=me?.csrf,eventId=form.dataset.eventId;
    if(form.id==='safety-suggestions-form') {
        const result=await api('/api/safety/'+encodeURIComponent(eventId)+'/suggestions?dictionary_id='+encodeURIComponent(fields.dictionary_id));
        if(me?.csrf===requestSession&&form.isConnected) {
            const event=data.events.find(e=>e.id===eventId);
            if(event)showSafetySuggestions(event,result);
        }
        return true;
    }
    if(form.id==='safety-dictionary-form') {
        let supplied;
        try{supplied=JSON.parse(fields.dictionary_json);}catch{throw Error('Supply valid dictionary JSON.');}
        if(!supplied||typeof supplied!=='object'||Array.isArray(supplied)||!Array.isArray(supplied.terms)||supplied.terms.length<1||supplied.terms.length>2000)throw Error('The dictionary must contain 1–2,000 code/label pairs in a terms array.');
        const confirmed=form.elements.licence_confirmed.checked;
        if(supplied.kind!=='Synthetic'&&!confirmed)throw Error('Confirm your institution has permission to use this supplied MedDRA or WHODrug release.');
        path='/api/dictionaries';body={name:supplied.name,version:supplied.version,kind:supplied.kind,terms:supplied.terms,licence_confirmed:confirmed};
        if(new TextEncoder().encode(JSON.stringify(body)).length>790000)throw Error('The imported release exceeds the request size limit. Supply a smaller package with a distinct version.');
        message='Terminology release imported with version and provenance.';
    }
    if(form.id==='safety-coding-form') {
        path='/api/safety/'+encodeURIComponent(eventId)+'/coding';body={dictionary_id:form.dataset.dictionaryId,code:fields.code,reason:fields.reason};message='Reviewed coding recorded. Verbatim event preserved.';
    }
    if(form.id==='safety-obligation-form') {
        path='/api/safety/'+encodeURIComponent(eventId)+'/obligations';body={...fields,due_at:safetyTimestamp(fields.due_at)};message='Recipient obligation recorded. No report was sent.';
    }
    if(form.id==='safety-followup-form') {
        path='/api/obligations/'+encodeURIComponent(form.dataset.id)+'/'+form.dataset.operation;body={reason:fields.reason};
        if(form.dataset.operation!=='escalate') {
            const key=form.dataset.operation==='dispatch'?'sent_at':'received_at';
            body[key]=safetyTimestamp(fields[key]);body.reference=fields.reference;
        }
        message='External '+(form.dataset.operation==='escalate'?'escalation':form.dataset.operation)+' recorded; no message sent.';
    }
    if(!path)return false;
    await api(path,body);
    if(me?.csrf!==requestSession)return true;
    document.querySelector('#modal').close();await refresh(true);
    if(me?.csrf!==requestSession)return true;
    if(eventId)eventDetail(eventId);
    else if(form.id==='safety-dictionary-form')showSafetyDictionaries();
    toast(message);return true;
}

function safetyTimestamp(value) {
    const parsed=new Date(value);
    if(!value||!Number.isFinite(parsed.getTime()))throw Error('Enter a valid local date and time.');
    return parsed.toISOString();
}

document.addEventListener('change',async event=>{
    try {
        if(event.target.matches('#safety-dictionary-form input[name=dictionary_file]')) {
            const file=event.target.files[0],form=event.target.form;
            if(file) {
                if(!file.size||file.size>700*1024)throw Error('Choose a non-empty JSON file up to 700 KiB.');
                const text=await file.text();
                if(form.isConnected)form.elements.dictionary_json.value=text;
            }
        }
        if(event.target.matches('#safety-obligation-form select[name=phase]')) {
            const form=event.target.form,record=data.events.find(e=>e.id===form.dataset.eventId);
            const due=event.target.value==='analysis'?record?.analysis_due:record?.initial_due;
            form.elements.due_at.value=due?safetyLocalTime(due):'';
        }
    } catch(error) {toast(error.message,true);}
});
