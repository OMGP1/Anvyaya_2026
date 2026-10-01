# Anvaya CTMS — User personas and access needs

Version: 1.1 · Updated: 30 September 2026 · Context: SIH problem statement 26046

## 1. Purpose and evidence status

These personas explain who the product serves, the decisions each person makes, and how those decisions map to the working prototype. They are **hypothetical design personas**, derived from the supplied problem statement and the implemented role model. They are not findings from AIIA interviews, a validated description of AIIA staffing, or a claim about actual institutional workflows. The example names and seeded records are fictional; named-account records are provisioned by an administrator.

The product uses synthetic studies and participants and now supports **named local accounts**, administrator-managed study assignments, required initial/reset password changes and session revocation. Optional shared demo-role login retains fixed rehearsal personas. A named account improves attribution but does not establish the real person's identity, professional standing or delegated clinical authority. Institutional onboarding must verify those facts and approve access; SSO/MFA remains an external integration requirement.

Read these personas with [WORKFLOWS.md](WORKFLOWS.md), [DESIGN.md](DESIGN.md), [REGULATORY_TRACEABILITY.csv](REGULATORY_TRACEABILITY.csv), and the permissions in [server.py](../server.py). The added interactions are implemented in [public/workflows.js](../public/workflows.js) and [public/safety.js](../public/safety.js). “Implemented” describes current behaviour; “Future” identifies a proposed extension. [VALIDATION.md](VALIDATION.md) records software checks, not completed institutional user research.

## 2. Persona map and priorities

| Persona | Role key | Primary decision | Product priority |
|---|---|---|---|
| Research administrator | `admin` | Which studies need operational intervention? | Primary portfolio user |
| Principal investigator | `pi` | Is the study ready to enrol and are safety obligations being handled? | Primary accountable study user |
| Study coordinator | `coordinator` | What participant and study work must be completed today? | Primary frequent operator |
| Clinical monitor | `monitor` | Which source-data gaps need verification and documented resolution? | Primary quality user |
| Ethics committee reviewer | `ethics` | Do visible approval, consent and safety records need follow-up? | Oversight user |
| Pharmacovigilance officer | `pv` | Which safety cases require review and reporting attention? | Primary safety user |
| Institutional leadership | `leadership` | Where should institutional attention and resources go? | Aggregate oversight user |
| Read-only regulator | `regulator` | Can a recorded action be traced to its context and history? | Inspection demonstration user |
| DSMB member | No current role | Does reviewed evidence warrant a recommendation under the DSMB charter? | Future independent oversight user |

No usability research supports this prioritisation yet. It is a delivery hypothesis: coordinators and investigators create operational records; administration and safety teams act on the resulting exceptions; other roles inspect evidence within their authorised remit.

## 3. Current access model

### 3.1 Data visibility

Named administrators have institution-wide study scope in the current model. Every other named role receives **only explicitly assigned studies**; an empty assignment is valid and exposes no study records. The fixed scopes below apply only when the optional shared demo persona is selected. Data-type restrictions in the remaining columns also apply to named users, within their own assignments.

| Role | Optional shared-demo scope | Participant records | Visit records | Safety records | Data queries | Audit history |
|---|---|---|---|---|---|---|
| Administrator | All studies | Yes | Yes | Yes | Yes | All entries |
| Principal investigator | AIIA-001, AIIA-002 | Assigned studies | Assigned studies | Assigned studies | Assigned studies | Entries linked to assigned studies |
| Coordinator | AIIA-001, AIIA-002, AIIA-003 | Assigned studies | Assigned studies | Assigned studies | Assigned studies | No |
| Monitor | AIIA-001, AIIA-003, AIIA-005 | Assigned studies | Assigned studies | Assigned studies | Assigned studies | Entries linked to assigned studies |
| Ethics committee | All studies | Yes | No | Yes | No | All entries |
| Pharmacovigilance | All studies | Yes | Yes | Yes | Yes | No |
| Leadership | All studies | No individual records | No individual records | Aggregate counts; no case narratives | Aggregate count only | No |
| Regulator | All studies | Yes | Yes | Yes | Yes | All entries |

Every role receives its visible study portfolio, readiness checks and derived KPIs. Leadership also receives study alerts, some containing case references; removing individual arrays is not a formally assessed anonymisation system. Named ethics, PV, leadership and regulator accounts use their assigned studies rather than inheriting the shared demo's all-study access. Audit views are similarly scoped to study-linked entries for assigned users; administrators can inspect global account events.

An administrator typing the responsible investigator's name into Setup changes study metadata, not access. **Access management** separately creates/updates an account's role and assignments, disables access, resets temporary passwords or revokes sessions. Every such change requires the relevant administrator workflow and invalidates existing sessions. A user must change an initial/reset password before accessing study records.

All non-leadership roles can inspect/download document evidence and inspect amendments within scope. Leadership receives neither document/amendment nor recipient-obligation arrays. **Integration & evidence** is an informational page for all roles, but import batch history requires import permission and provenance/FHIR actions require export permission. Terminology metadata and suggestions are available to safety/report roles (administrators also manage packages). Viewing explanatory cards is not permission to use their operational APIs.

### 3.2 Actions, including study setup and activation

| Role | Enrol / withdraw | Record visit | Capture AE / SAE | Record external reporting step | Resolve query | Create/setup/activate study / edit alert thresholds | Export | View audit |
|---|---|---|---|---|---|---|---|---|
| Administrator | Yes | Yes | Yes | Yes | Yes | Yes / Yes | Yes | Yes |
| Principal investigator | Yes | Yes | Yes | Yes | Yes | No / No | Yes | Yes |
| Coordinator | Yes | Yes | Yes | No | Yes | No / No | No | No |
| Monitor | No | No | No | No | Yes | No / No | Yes | Yes |
| Ethics committee | No | No | No | No | No | No / No | No | Yes |
| Pharmacovigilance | No | No | Yes | Yes | No | No / No | No | No |
| Leadership | No | No | No | No | No | No / No | No | No |
| Regulator | No | No | No | No | No | No / No | Yes | Yes |

Permissions are enforced by the server, and an allowed action remains restricted to the user's study assignments. Only the administrator creates studies, edits Setup metadata and activates recruitment; setup edits are rejected after activation. Reviewed amendments provide the separate active-study change path. “Record external reporting step” stores evidence, not a transmission. Dataset exports create audit events even for the otherwise read-only regulator role.

### 3.3 Added evidence, access, import and safety permissions

| Role | Upload evidence | Review evidence / approve amendment | Submit amendment | Record reconsent | Preview / commit CSV | Confirm coding / recipient follow-up | Manage accounts / dictionaries |
|---|---|---|---|---|---|---|---|
| Administrator | Named account | Named; independent | Named account | Yes | Yes | Named coding / Yes | Yes / named dictionary import |
| Principal investigator | Named account | No | Named account | Yes | Yes | Named coding / Yes | No |
| Coordinator | Named account | No | No | Yes | Yes | No; may inspect suggestions / No | No |
| Monitor | No | No | No | No | No | No | No |
| Ethics committee | No | Named; independent | No | No | No | No | No |
| Pharmacovigilance | No | No | No | No | No | Named coding / Yes | No |
| Leadership | No | No | No | No | No | No | No |
| Regulator | No | No | No | No | No | No | No |

“Independent” means the approving named user differs from the uploader or amendment submitter; it does not prove organisational independence or professional authority. Reconsent uses enrolment permission. Final coding uses reporting permission plus a named account; a coordinator can request lexical suggestions but cannot approve a code. Recipient records use reporting permission and must be assigned to an active named reporting user with access to the study. These actions record manual external dispatch/receipt/escalation evidence, without sending reports or messages.

Named administrators cannot silently bypass independent document/amendment review, alter immutable file versions or remove the last active named administrator. Account access changes and resets also have stale-revision checks. The broad administrator clinical permissions are a demonstration policy to review with the institution, not a statement that an IT administrator may perform clinical duties.

## 4. P01 — Research administrator

**Illustrative persona:** Aditi Sharma, research office administrator. **Implemented role:** `admin`.

**Context and goals.** The administrator needs one portfolio view for recruitment, approvals, unresolved queries and safety deadlines. The working setup checklist helps the administrator see which recorded prerequisites block recruitment, save incomplete evidence and activate a ready study explicitly. The dashboard should make exceptions visible while preserving the investigator's responsibility for clinical and protocol decisions.

**Decisions and pain-point hypotheses.** The administrator decides which team to contact, whether recorded study evidence is complete enough for activation, whether an approval milestone needs attention, and which operational threshold warrants an alert. Likely pain points include inconsistent study names, stale spreadsheets, missing owners and ambiguity about whether a reported task actually happened. These hypotheses need interviews; they are not measured AIIA problems.

**Data scope and permissions.** The administrator has all-study visibility and the broadest implemented permissions. It creates drafts, edits versioned Setup and activates recruitment after the six readiness checks. Setup fields include separate protocol/consent versions, investigator, formulation/batch, registry and IEC dates/references, and study dates. The role also manages named accounts/assignments, uploads/reviews evidence, submits/approves amendments, reviews CSV imports, imports dictionary packages, records safety follow-up and performs the core participant/query/export/audit actions. Named identity and independent-review conditions still apply. Institutional policy should separate platform administration, research coordination and clinical authority where required.

**Representative scenario.** Aditi creates a formulation study and opens its readiness checklist. She saves protocol `P-3`, consent `ICF-2`, a responsible investigator, formulation/batch, registry and IEC metadata, and study dates, together with a reason. The checklist evaluates registration, current IEC approval, both versions, investigator, intervention context and the open study period. Once all six pass, she reviews the confirmation dialog and activates recruitment with a decision reason. The server rechecks the current revision and readiness before saving Recruiting status and its audit entry. A later enrolment must use `ICF-2`; supplying `P-3` as the consent version is rejected.

In **Access management**, Aditi separately provisions a named PI and ethics reviewer with the appropriate study assignment. Both replace temporary passwords before use. The PI uploads amendment evidence, and the different reviewer records the decision. If a staff assignment changes, Aditi updates it with a reason; prior sessions become invalid. Editing a display name in the study never substitutes for these account actions.

**Record safeguards and boundaries.** Setup, activation, access changes and review decisions retain reasons, times, revisions and audit values. Stale forms cannot overwrite newer revisions. Legacy active records retain documented compatibility behaviour without invented evidence. Uploaded documents have immutable API versions/checksums and named review decisions, but these do not authenticate an IEC/CTRI issuer or replace external approval. Naming an investigator does not give login access. Alert thresholds do not change statutory timers. A licence declaration on a terminology package is recorded, not independently verified.

**Success criteria and accessibility.** Aditi should locate an exception and its study without reading every record, understand each readiness blocker and distinguish a saved draft from an activated study. Status must be understandable from text as well as colour. A stale-revision error should explain how to review the latest record before retrying. Portfolio tables should remain usable with zoom, keyboard navigation and horizontal scrolling on smaller screens. Whether these criteria are met requires usability testing.

**Validation questions.** Who owns the master study list? Who may authorise recruitment activation, and what source documents and signatures must support that decision? Which alert thresholds may administrators change? Which duties must remain with investigators? Are all sites visible to one research office, or are separate institutional boundaries required?

## 5. P02 — Principal investigator

**Illustrative persona:** Dr. Kavya Rao, investigator responsible for a study. **Implemented role:** `pi`.

**Context and goals.** The PI needs a reliable picture of assigned studies, enrolment readiness, participant consent and safety reporting work. The product should help the PI inspect the evidence behind a status and identify the next action without treating the dashboard as a clinical decision maker.

**Decisions and pain-point hypotheses.** The PI reviews whether the required study prerequisites are in place, whether a safety case needs reporting action, and whether a data query has an adequate explanation. Potential pain points are competing clinical duties, delayed information from coordinators, consent-version confusion and the difference between event occurrence, staff awareness and later data entry.

**Data scope and permissions.** A named PI sees administrator-assigned studies; the optional demo PI retains AIIA-001/AIIA-002. The PI can inspect readiness, enrol/reconsent/withdraw, record visits and safety, confirm coding as a named reporting user, record recipient follow-up, resolve queries, upload evidence, submit amendments, preview/commit CSV imports, export and inspect assigned audit history. The PI has no document-review or amendment-approval permission and cannot create/setup/activate studies, change global settings or manage accounts. Naming the PI in study metadata does not expand access or confer authority to sign a real regulatory report.

**Representative scenario.** Dr. Rao submits an amendment using three approved evidence versions. A different ethics reviewer approves it; changed consent marks active participants for reconsent. Dr. Rao then reviews an SAE's original narrative, occurrence/awareness times and configured pathway. She creates a recipient obligation assigned to an active named reporting user. After external dispatch and acknowledgment, she records each timestamp/reference and reason. Those external times remain separate from entry time; the application does not transmit the report or authenticate its receipt.

**Success criteria and accessibility.** The PI should distinguish seriousness from severity and distinguish a pending report from a recorded reporting step. Deadlines need exact times as well as countdowns. A compact screen should support quick review between tasks, while an expanded record should preserve the full narrative.

**Validation questions.** Which tasks are delegated to coordinators? Who verifies consent documentation? Which safety timelines apply to each study? Which recipients and documentary evidence prove reporting? How should corrections and late entries be reviewed?

## 6. P03 — Study coordinator

**Illustrative persona:** Neha Singh, study coordinator. **Implemented role:** `coordinator`.

**Context and goals.** The coordinator maintains day-to-day study records. The main needs are clear enrolment prerequisites, a manageable visit list, visible consent status and forms that preserve work when validation fails. The coordinator must be able to record a safety concern promptly without making an unsupported causality judgment.

**Decisions and pain-point hypotheses.** The coordinator decides which due visit or query to handle next and whether an enrolment attempt has all the required metadata. Possible pain points include repeating identifiers across spreadsheets, mismatched consent versions, ambiguous overdue lists and difficulty recording an event discovered after it occurred.

**Data scope and permissions.** A named coordinator sees assigned studies; the optional demo persona retains AIIA-001/AIIA-002/AIIA-003. The role can enrol, record reconsent/withdrawal, complete permitted visits, capture safety events, request lexical suggestions, resolve queries, upload evidence using a named account and preview/commit synthetic CSV imports. It cannot approve coding, document review or amendments, submit amendments, record recipient reporting steps, export operational datasets, inspect Audit, manage accounts or change study settings. Scoped evidence downloads remain available; these are distinct from dataset-export permission.

**Representative scenario.** Neha selects an assigned study, checks the prefilled current consent version and enrols a synthetic adult. Protocol and consent versions can differ; the server checks the consent-specific field, repeats study readiness checks and creates two follow-up visits. Later, she records withdrawal with a reason. Incomplete visits scheduled on or after the withdrawal date become Cancelled in the displayed schedule, and routine visit completion is blocked by the server.

For an active participant affected by an approved consent amendment, Neha sees **Reconsent due**, reviews the current version and records language/confirmation/evidence. **History** retains earlier consent and source provenance. Routine visit completion stays blocked until current-version consent is recorded. For CSV intake, she reviews mapping and rejected rows before committing; the import cannot bypass the same readiness/consent gates or silently duplicate a source identity.

**Success criteria and accessibility.** A failed form should show a specific corrective message while retaining entered values. Required controls should have visible labels. The coordinator should not need to distinguish similar colours to recognise consent withdrawal, due visits or serious events. The current interface is English; a consent-language field is not a translated user interface.

**Validation questions.** What is a typical daily participant volume? Which languages are needed? What consent evidence exists outside the application? Are visit dates scheduled centrally or per protocol? What happens during network loss? Which coordinator actions need PI countersignature?

## 7. P04 — Clinical monitor

**Illustrative persona:** Arjun Patel, clinical monitor. **Implemented role:** `monitor`.

**Context and goals.** The monitor reviews assigned studies for data completeness and traceability. The application should make it possible to connect a query with its study, inspect recorded actions and produce a scoped export for further review.

**Decisions and pain-point hypotheses.** The monitor decides whether a source-verification explanation supports resolution of an existing query. Likely friction includes incomplete audit context, inconsistent query tracking and uncertainty about which study records fall within an assignment.

**Data scope and permissions.** A named monitor sees assigned studies; the optional demo persona retains AIIA-001/AIIA-003/AIIA-005. The role resolves queries, exports records/provenance, runs local FHIR checks and inspects assigned audit history, documents and amendments. It cannot import/commit participant batches, enrol, record visits or safety, change consent, approve evidence or manage accounts. Query creation, independent response and closure stages remain outside the single Open → Resolved demonstration.

**Representative scenario.** Arjun filters queries to an assigned study, records an explanation and checks `QUERY_RESOLVED` in Audit. He can inspect available protocol/consent/IEC file versions, their checksums and review status, then compare exported provenance for an imported participant. The document register is not a full clinical source repository: batch/source CRFs may remain external, and no formal source-data verification attestation is implemented.

**Success criteria and accessibility.** Study filters should be predictable, and inspection should expose the recorded reason and before/after values without requiring database access. Table headings, expanded details and download actions should work with keyboard navigation.

**Validation questions.** Can the same person respond to and close a query? How are monitoring assignments approved? Are remote source documents accessible? Which records must be redacted from exports? What evidence constitutes a completed monitoring visit?

## 8. P05 — Ethics committee reviewer

**Illustrative persona:** IEC reviewer; no real committee member is represented. **Implemented role:** `ethics`.

**Context and goals.** The reviewer needs to inspect approval status, consent metadata, serious reports and related recorded actions. The interface should present evidence for review without implying that viewing a dashboard constitutes committee approval.

**Decisions and pain-point hypotheses.** A reviewer identifies matters that require a request for clarification, discussion or formal review through the committee's actual procedures. Possible pain points are disconnected safety updates, uncertain protocol versions and difficulty reconstructing the order of consent and study actions.

**Data scope and permissions.** A named ethics reviewer receives assigned studies, participant consent metadata, safety/document/amendment records and scoped audit history; visit/query arrays remain withheld. The optional demo ethics persona exposes all synthetic studies. A named ethics account can approve/reject uploaded evidence and approve an amendment submitted by a different person. It cannot upload evidence, submit amendments, enrol/reconsent, record safety/reporting steps, export datasets or manage accounts. Recording an independent application review is distinct from issuing an IEC decision, verifying a signature, establishing quorum or recording formal minutes.

**Representative scenario.** The reviewer inspects the protocol, consent and IEC files in **Documents & amendments**, confirms their context through the institution's external process and records an independent decision with a reason. The reviewer then examines a submitted amendment, its study revision and reconsent implications. Approval applies the reviewed metadata and marks affected active participants; Audit retains the named decision. The legal committee decision and its authorised evidence are still obtained outside this application.

**Success criteria and accessibility.** Approval expiry, protocol version, consent status and timestamps should be legible in text. Long narratives and audit details should remain readable at increased text size. The reviewer should be able to identify what evidence is present and what must be requested externally.

**Validation questions.** What minimum information does the IEC need? Which case narratives may it access? How are committee conflicts of interest handled? Who uploads approval evidence? Which decisions need signatures, quorum evidence or formal minutes?

## 9. P06 — Pharmacovigilance officer

**Illustrative persona:** Dr. Meera Iyer, pharmacovigilance officer. **Implemented role:** `pv`.

**Context and goals.** The safety user reviews AE/SAE records, distinguishes initial/analysis work, selects terminology through human review and preserves recipient follow-up evidence. The key need is a time-aware inbox with clear rule/SOP labels, intact source narratives and no suggestion that a software score establishes clinical meaning.

**Decisions and pain-point hypotheses.** The officer prioritises cases for human assessment and checks whether reporting metadata is complete. Hypothesised pain points include conflating seriousness with severity, calculating deadlines from data-entry time, missing external acknowledgements and treating all Ayurveda studies as subject to an identical legal pathway.

**Data scope and permissions.** A named PV user sees assigned studies and their detailed arrays, including visits and queries; the optional demo persona remains all-study. The role can capture safety cases, request suggestions, confirm coding through a named account and create/record recipient obligations, dispatch, receipt and escalations. It can inspect scoped document evidence but cannot upload/review evidence, submit amendments, import participant CSVs, enrol/reconsent/withdraw, complete visits, resolve queries, export datasets, manage dictionaries/accounts or view Audit. Institutional review should narrow any additional data exposure to the actual safety purpose.

**Representative scenario.** Meera records the original event and reviews its conditional timer. She selects an administrator-supplied Synthetic or authorised MedDRA package, inspects lexical candidates and either leaves the case unresolved or confirms a code with a reason. Original text remains unchanged, and later recoding retains earlier versions. She adds an explicit recipient/deadline/rule basis and assigns an active reporting user for that study. After external activity she records dispatch/receipt references and times; an unresolved obligation can receive an escalation record. No report or escalation message is sent by Anvaya.

**Success criteria and accessibility.** The user should find the next deadline and its basis, distinguish actual external-event claims from entry time and reconstruct follow-up. Status must remain meaningful without colour. **Lexical score** must never be labelled clinical confidence, model accuracy or causality. Abstention should be an understandable state, not an error to bypass. Synthetic packages must remain labelled synthetic; WHODrug product terms must not appear as AE codes. No trained AI or independent licence verification is claimed.

**Validation questions.** Which cases enter trial safety versus wider pharmacovigilance surveillance? Who reviews seriousness and causality? Which recipients and acknowledgements are required? Who licenses and maintains terminology? Which events require follow-up after withdrawal? How are duplicate cases reconciled?

## 10. P07 — Institutional leadership

**Illustrative persona:** Research director. **Implemented role:** `leadership`.

**Context and goals.** Leadership needs a concise portfolio view of recruitment progress, due-visit completion, open queries and pending safety reports. The purpose is institutional oversight and resource allocation, not individual participant management.

**Decisions and pain-point hypotheses.** Leadership decides which teams need attention, where recruitment is below the planned pace and whether unresolved exceptions warrant escalation. Potential pain points include inconsistent denominators and dashboards that show attractive totals without their definitions.

**Data scope and permissions.** Named leadership receives summaries within assigned studies; the optional demo persona covers all studies. The API removes individual participant/visit/query/event arrays and withholds document/amendment, recipient, import and dictionary records. Leadership has no mutation, export or audit permission. It can read **Integration & evidence** explanations; **Documents & amendments** shows a restricted view and **Access management** is absent. Some study alerts retain case references, so this is an aggregate-focused view rather than a formally assessed anonymisation mechanism.

**Representative scenario.** The director compares cumulative enrolment against total targets, reviews an expiring approval alert and checks the count of pending initial SAE reports. The director requests follow-up from the responsible team outside the app. The app does not infer treatment efficacy from these operational metrics.

**Success criteria and accessibility.** Each KPI should state its denominator or meaning. An unavailable rate should appear as unavailable rather than a misleading zero. The overview should remain readable when projected during a review meeting.

**Validation questions.** Which decisions are made weekly versus monthly? Is site comparison appropriate across different designs and recruitment stages? What aggregation or suppression is needed for small studies? Which exceptions justify direct case access, and who approves it?

## 11. P08 — Read-only regulator

**Illustrative persona:** Audit observer. **Implemented role:** `regulator`.

**Context and goals.** This persona demonstrates inspection access to study records and application history. It represents a product capability rather than an assertion that a real regulator would use this interface or accept its evidence.

**Decisions and pain-point hypotheses.** The observer determines whether records can be traced to a study, timestamp, role and reason, and identifies missing evidence for follow-up. Potential friction includes reconstructing change history, confusing a dataset preview with a submission package and mistaking application hash checks for independent immutability.

**Data scope and permissions.** A named regulator/observer receives assigned-study records, document/amendment evidence, scoped Audit, dataset/provenance downloads and local FHIR checks. The optional demo persona covers all synthetic studies. It cannot mutate clinical records, approve evidence/coding, manage accounts or inspect/commit import batches through the import API. Downloads create audit evidence where implemented. A real inspection account needs approved identity/delegation, institution, study scope, access period and disclosure policy.

**Representative scenario.** The observer opens a consent-withdrawal audit entry, expands its before/after values and verifies the stored hash chain. The observer downloads the FHIR research bundle or a DM/AE mapping preview. These exports are review artifacts, not validated regulatory submissions.

**Success criteria and accessibility.** Ledger entries need stable sequence numbers, readable timestamps and an expandable explanation. Export labels should describe actual contents. Chain verification should explain its local scope rather than claiming that an administrator cannot alter the underlying system.

**Validation questions.** Which inspection records may be disclosed? Must exports include a signed manifest? What retention and independent checkpointing are required? Is inspection access time-limited? What evidence proves the identity and delegation of the person who entered a record?

## 12. P09 — DSMB member: future persona

**Status:** Planned; no DSMB account, workspace or decision workflow exists in the MVP.

**Context and goals.** A future independent safety-monitoring user would review charter-defined evidence and make documented recommendations. The scope might include aggregate safety summaries, protocol-defined analyses and restricted unblinded information. The actual study charter must determine whether a DSMB is required and what it may see.

**Decisions and pain-point hypotheses.** The member needs enough validated evidence to make a recommendation while protecting blinding and maintaining independence. Potential pain points are incomplete denominators, version ambiguity, unsupported automated “signals” and accidental disclosure of treatment assignments.

**Proposed scope and workflow.** Provide access only to assigned studies and charter-authorised reports. Separate blinded and unblinded packages. Record the report version, meeting participation, conflicts, recommendation and authorised communication. Do not grant the current leadership or PV role broader access and relabel it DSMB.

**Representative future scenario.** A data manager produces a reviewed safety package. An authorised independent reviewer checks its version, examines predefined analyses and records a committee recommendation. The study team receives only the information permitted by the charter. This is a proposed workflow, not a current feature or an efficacy claim.

**Success criteria and accessibility.** A reviewer should know the data cutoff, population, denominator, analysis version and blinding status of every report. Charts need tabular alternatives. Recommendation recording should not require copying confidential case-level data into unrestricted notes.

**Validation questions.** Which studies need a DSMB? Who may receive unblinded data? What are the charter's review triggers? Who prepares independent analyses? How are recommendations communicated, acknowledged and retained?

## 13. Represented participant: a stakeholder without an account

The participant has no portal or login. Staff record a synthetic identifier, age, sex, Prakriti, consent version/language and study events. Participant forms do not collect names, phone numbers, Aadhaar or ABHA identifiers or participant signatures. The new consent-document upload is **study-level evidence**, not a signed participant-consent upload or electronic-signature ceremony. Only synthetic files belong in the demonstration; operators must not place real participant identifiers in free text or uploaded files.

An approved consent amendment can flag an active participant for reconsent. Recording the new consent preserves earlier metadata and does not invent a signature or prove understanding. A withdrawn participant cannot be reactivated through the reconsent action. Safety recording remains available independently of routine research participation.

Future research should establish whether participants understand the consent process, receive accessible information in the required language and can withdraw without confusing withdrawal from treatment, research procedures, data processing and legally required record retention. The current withdrawal action records one simplified research-consent state. It does not implement a full participant-rights or privacy-request service.

## 14. Validation plan

Recruit representatives through authorised institutional channels; no interviews or outreach have been performed for these documents. Begin with one coordinator, one PI, research administration, an IEC representative and a PV representative. Add monitoring, leadership, data management and information security before expanding access or integrations. The proposed sample is a starting plan, not a completed study.

Use synthetic tasks: locate an expiring approval; explain a readiness rejection; create and scope a named account; reject self-approval; trace an approved amendment to reconsent history; reconcile a CSV duplicate/conflict; distinguish a lexical candidate from an approved code; identify an overdue recipient receipt; record withdrawal; and explain a KPI. Observe completion, interpretation errors, requests for help and missing information. Record actual user-study results after testing; software/browser checks do not establish achieved usability or clinical impact.

Confirm the role matrix, data scope and approval ownership before translating the demo into institutional access policy. Prioritise findings that change participant protection, safety reporting, permitted access or the meaning of a KPI. Maintain an evidence log distinguishing interview statements, observed behavior, legal requirements and team assumptions.

The implemented browser paths are evidenced by [Access management](screenshots/06-access-management.png), [Documents & amendments](screenshots/07-documents-amendments.png), [Integration & evidence](screenshots/08-integration-evidence.png), [mobile integration](screenshots/09-integration-mobile.png) and [coding/follow-up](screenshots/10-coding-followup.png). These are actual screenshots from automated Chrome workflows on synthetic data. They are not interviews, clinical validation, trained-model results or production acceptance.

## 15. Source context

### Operations increment — 1 October

Admin, PI, coordinator and monitor now hold the `operations` permission within their existing study assignments: site records/activation, monitoring schedule/completion and deviation capture/closure. Existing query roles can create as well as resolve queries. Ethics, PV and regulator can inspect scoped operation records without these mutation actions. Leadership receives counts/forecasts and redacted alerts; individual sites, monitoring and deviation arrays are withheld. This is a prototype access matrix, not an approved institutional delegation policy.

Additional user tasks: a monitor records findings and corrective action; a coordinator interprets a forecast against its trailing-rate baseline; an administrator edits alert horizons; leadership reviews aggregate open work. All roles can generate a scoped aggregate pre-inspection report; audit verification remains limited to audit-authorised roles. No DSMB membership, clinician interview or verified usability outcome is implied.

The role families and broad CTMS needs come from the user-supplied text of SIH 26046, associated with the [official SIH problem-statement listing](https://sih.gov.in/sih2026PS). The exact current permissions come from the local implementation, not from an assumed legal assignment of duties. The [CTRI FAQ](https://ctri.nic.in/Clinicaltrials/faq.php) supports the prospective-registration design context. Study-specific safety applicability should be checked against the [CDSCO NDCT rules and amendments](https://www.cdsco.gov.in/opencms/opencms/en/Acts-and-rules/New-Drugs/) and the approved protocol/SOP; the personas themselves are design hypotheses.
