# Graph Report - .  (2026-09-30)

## Corpus Check

## Summary
- 656 nodes · 1272 edges · 31 communities (27 shown, 4 thin omitted)
- Extraction: 96% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 41 edges (avg confidence: 0.64)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30

## God Nodes (most connected - your core abstractions)
1. `esc()` - 28 edges
2. `Judge questions and defensible answers` - 28 edges
3. `AccountTest` - 24 edges
4. `Client` - 24 edges
5. `WorkflowTest` - 22 edges
6. `ExchangeTests` - 22 edges
7. `Anvaya CTMS — User workflows and exception handling` - 19 edges
8. `renderPage()` - 17 edges
9. `ApiError` - 16 edges
10. `snapshot()` - 16 edges
11. `SafetyWorkflowTest` - 16 edges
12. `Anvaya CTMS — User personas and access needs` - 16 edges

## Surprising Connections (you probably didn't know these)
- `inspect_database()` --calls--> `verify_audit()`  [EXTRACTED]
  ops.py → server.py
- `accessPage()` --indirect_call--> `match()`  [INFERRED]
  public/workflows.js → public/app.js
- `documentsPage()` --indirect_call--> `match()`  [INFERRED]
  public/workflows.js → public/app.js
- `integrationPage()` --indirect_call--> `match()`  [INFERRED]
  public/workflows.js → public/app.js
- `initialize()` --calls--> `create()`  [EXTRACTED]
  server.py → accounts.py
- `snapshot()` --calls--> `public()`  [EXTRACTED]
  server.py → accounts.py
- `snapshot()` --calls--> `list_documents()`  [EXTRACTED]
  server.py → documents.py
- `snapshot()` --calls--> `summary()`  [EXTRACTED]
  server.py → exchange.py
- `snapshot()` --calls--> `list_dictionary_metadata()`  [EXTRACTED]
  server.py → safety_workflow.py
- `snapshot()` --calls--> `list_obligations()`  [EXTRACTED]
  server.py → safety_workflow.py
- `create_app()` --calls--> `initialize()`  [EXTRACTED]
  wsgi.py → server.py
- `AccountTest` --uses--> `Client`  [INFERRED]
  tests/test_accounts.py → tests/test_api.py

## Import Cycles
- None detected.

## Communities (31 total, 4 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.15
Nodes (56): aboutPage(), alertList(), api(), auditPage(), boot(), brand(), button(), can() (+48 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (37): Claim boundary for slides and reviews, FHIR R4 validation evidence, Recorded artifact fingerprints, Reproduce the run, Results and remaining messages, What was actually tested, 1. Version and boundary decisions, 2. Implemented FHIR export (+29 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (14): check_bundle(), mutate(), preview(), Controlled synthetic CSV intake and inspectable export checks, not an EDC connec, Local consistency checks only; never labelled official profile validation., summary(), validate_row(), Client (+6 more)

### Community 3 - "Community 3"
Cohesion: 0.15
Nodes (34): BaseHTTPRequestHandler, Exception, actor_id(), ApiError, audit(), authorized(), bundle(), calendar_date() (+26 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (41): 10. Does clicking “Record initial” notify the regulator?, 11. Is an AE proof that an Ayurveda medicine is unsafe?, 12. How do you handle consent withdrawal?, 13. Is this ABDM integrated?, 14. Are your CSVs submission-ready SDTM?, 15. What AI have you implemented?, 16. Can you use MedDRA and WHODrug freely?, 17. Does DPDP require every health record to stay in India? (+33 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (40): ANVAYA — built and tested: presentation content, Completed workflow additions — presenter note, Factual boundary matrix — keep off the slides, Left heading — IMPACTS ON TARGET AUDIENCE, Left panel — Implemented Technology Stack & Methodology, Lower left — CHALLENGES ADDRESSED, Lower left — Operational Feasibility, Lower left — Research Data & Exchange (+32 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (26): 10. Pilot design validation tasks, 1. Design direction, 2. Navigation and information hierarchy, 3. Screen specifications, 4. Design tokens, 5. Components and interaction contracts, 6. States and recovery, 7. Responsive and accessibility requirements (+18 more)

### Community 7 - "Community 7"
Cohesion: 0.08
Nodes (25): 10. WF08 — Record initial and analysed reporting steps, 11. WF09 — Resolve an existing data query, 12. WF10 — Review ethics and registry milestones; configure operational alerts, 13. WF11 — Export scoped research records, 14. WF12 — Inspect changes and verify the audit chain, 15. WF13 — Handle validation, disconnection and uncertain completion, 16. Future workflows: deliberately outside the current MVP, 17. Demonstration path and truthful presentation language (+17 more)

### Community 9 - "Community 9"
Cohesion: 0.09
Nodes (22): 1. Clinical rationale: why the three enrolment gates matter, 2. From DM/AE-shaped CSV to a submission package, 3. Moving from local SQLite to secure institutional hosting, 4. Integrating an existing EDC or hospital system, 5. Licensed MedDRA and WHODrug terminology assistance, 6. Compact slide additions, 7. Judge questions and concise answers, Anvaya: clinical rationale and production completion requirements (+14 more)

### Community 10 - "Community 10"
Cohesion: 0.16
Nodes (11): copy_database(), inspect_database(), main(), Verified SQLite recovery copies; no command replaces an existing database., Verify SQLite structure and the same raw-payload chain checked by the app., Online backup API includes committed WAL data; output must not exist., readonly(), VerificationError (+3 more)

### Community 12 - "Community 12"
Cohesion: 0.11
Nodes (19): 10. Hosting and staged deployment, 11. Technical acceptance, 1. Architecture decision, 2. Repository map and execution, 3. Storage model, 4. API contract, 5. Identity, permissions and request safety, 6.1 Document and amendment state transitions (+11 more)

### Community 13 - "Community 13"
Cohesion: 0.11
Nodes (19): 10. P07 — Institutional leadership, 11. P08 — Read-only regulator, 12. P09 — DSMB member: future persona, 13. Represented participant: a stakeholder without an account, 14. Validation plan, 15. Source context, 1. Purpose and evidence status, 2. Persona map and priorities (+11 more)

### Community 14 - "Community 14"
Cohesion: 0.18
Nodes (16): accessPage(), amendmentFields(), documentsPage(), downloadPath(), fileBase64(), integrationPage(), passwordFields(), renderPasswordChange() (+8 more)

### Community 15 - "Community 15"
Cohesion: 0.26
Nodes (3): principal(), Synthetic fixtures test terminology review and recipient reporting records., SafetyWorkflowTest

### Community 16 - "Community 16"
Cohesion: 0.11
Nodes (18): 10. Corrections to the supplied research plan, 11. Implementation and validation plan, 12. Unresolved evidence, 1. Recommendation, 2. What the official problem actually asks, 3. Domain discovery, 4. Gap analysis and user decisions, 5. Regulatory findings that change the design (+10 more)

### Community 17 - "Community 17"
Cohesion: 0.31
Nodes (3): DocumentWorkflowTest, principal(), Transaction-level evidence and amendment tests using isolated synthetic data.

### Community 18 - "Community 18"
Cohesion: 0.12
Nodes (16): 10. Dependencies and risks, 11. Validation and release gates, 12. Open discovery questions, 1. Product decision, 2. Problem and evidence, 3. Outcomes and measurement, 4. Users and jobs, 5. Release scope (+8 more)

### Community 19 - "Community 19"
Cohesion: 0.13
Nodes (15): Existing-data compatibility, Six readiness checks, Stage 1 — Study readiness and activation: completed, Stage 2 walkthrough: named access, Stage 3 walkthrough: reviewed evidence and reconsent, Stage 4 walkthrough: source review, Stage 5 walkthrough: terminology and recipients, Stage 6 walkthrough: deployment and recovery (+7 more)

### Community 20 - "Community 20"
Cohesion: 0.28
Nodes (14): _ae_dictionary(), _coding_access(), dictionary_metadata(), _eligible_assignee(), list_assignees(), list_dictionary_metadata(), list_obligations(), mutate() (+6 more)

### Community 21 - "Community 21"
Cohesion: 0.26
Nodes (12): _amended_study(), _approved_documents(), _can_read(), _file(), get_document(), list_documents(), metadata(), mutate() (+4 more)

### Community 22 - "Community 22"
Cohesion: 0.36
Nodes (8): assignments(), create(), find(), mutate(), password_hash(), public(), Named local accounts. Password material never enters API responses or audit payl, validate_password()

### Community 23 - "Community 23"
Cohesion: 0.35
Nodes (10): safetyActions(), safetyLocalTime(), safetyObligationActions(), safetyObligationEvidence(), safetySuggestionsForm(), safetyTimestamp(), safetyWorkflowAction(), safetyWorkflowSubmit() (+2 more)

### Community 24 - "Community 24"
Cohesion: 0.22
Nodes (9): Back up and restore, Configuration reference, Container rehearsal, Deployment, access and recovery, Institutional acceptance, Named accounts, Public HTTPS installation, Release checks and rollback (+1 more)

### Community 25 - "Community 25"
Cohesion: 0.25
Nodes (7): Benchmark, initial snapshot, Extraction scope, Graphify use and interpretation, Latest snapshot — study readiness upgrade, 30 September 2026, Query performed, Rebuild, Report findings, quoted and interpreted

### Community 26 - "Community 26"
Cohesion: 0.36
Nodes (5): application(), create_app(), WSGI transport for the same tested handlers, served with Waitress.  One process, Adapt the handler's request/response boundary without a second router., Request

### Community 27 - "Community 27"
Cohesion: 0.40
Nodes (3): Named-user evidence, amendment, import and PV workflows in a real browser., signin(), submit()

### Community 28 - "Community 28"
Cohesion: 0.50
Nodes (3): Answer, Q: What connects renderPage() to aboutPage() and compliancePage()?, Source Nodes

## Knowledge Gaps
- **257 isolated node(s):** `paths`, `config`, `nav`, `workflowPages`, `Presentation and research` (+252 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Are the 15 inferred relationships involving `Client` (e.g. with `AccountTest` and `.setUp()`) actually correct?**
  _`Client` has 15 INFERRED edges - model-reasoned connections that need verification._
- **What connects `paths`, `config`, `nav` to the rest of the system?**
  _257 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.0660377358490566 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.07164404223227752 - nodes in this community are weakly interconnected._
- **Should `Community 3` be split into smaller, more focused modules?**
  _Cohesion score 0.14799154334038056 - nodes in this community are weakly interconnected._
- **Should `Community 4` be split into smaller, more focused modules?**
  _Cohesion score 0.04878048780487805 - nodes in this community are weakly interconnected._
- **Should `Community 5` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._
- **Should `Community 6` be split into smaller, more focused modules?**
  _Cohesion score 0.07692307692307693 - nodes in this community are weakly interconnected._