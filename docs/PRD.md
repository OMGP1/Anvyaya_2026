# Anvaya — Product Requirements Document

**Version:** 1.1 · **Date:** 30 September 2026 · **Problem:** SIH 26046  
**Audience:** student team, reviewers, future AIIA product owner, research operations and compliance stakeholders.  
**Working product name:** Anvaya. Team and college identity are intentionally unspecified.

## 1. Product decision

Anvaya is a working clinical-research operations workspace for Ayurveda that connects study progress, participant consent, safety reporting and evidence of change. The current release supports complete workflows using synthetic data: named account administration, study activation, independent document review, amendments and reconsent, reviewed CSV intake, safety coding and recipient follow-up. Institutional acceptance remains necessary before handling actual trial records.

The platform is a CTMS and oversight layer. It is not a diagnostic service, a treatment recommender, a replacement for the Ethics Committee, or an automatically approved regulatory filing system. Synthetic CSV intake demonstrates mapping, reconciliation and guarded enrolment; live EDC and hospital connections require partner-specific adapters and access agreements.

## 2. Problem and evidence

The official problem statement describes fragmented study tracking, disconnected tools and delayed visibility across clinical research. It requests prospective registration tracking, ethics oversight, safety workflows, role-specific KPIs and interoperability. These requirements are the evidence for the initial scope; specific AIIA baseline numbers have not been measured. [S01](SOURCES.md)

Three user problems drive the product:

1. **Investigators cannot quickly reconcile portfolio status with the underlying records.** A useful dashboard must show its denominator and let the user inspect the study or work item.
2. **Safety and regulatory work depends on dates, recipients and applicability.** A coloured card is insufficient unless the required action, owner, clock and evidence are available.
3. **Data is difficult to trust or reuse when consent, changes and standards mapping are disconnected.** Integrity and export metadata must be part of the workflow.

Ayurveda-specific design requirements include formulation and batch context, protocol-defined Prakriti assessments, procedure-based interventions and whole-system regimens. Their precise instruments and vocabulary require investigator approval. The MVP includes representative fields, not clinical validation.

## 3. Outcomes and measurement

| Outcome | MVP acceptance | Future pilot measure |
|---|---|---|
| Reliable oversight | Portfolio counts derive from persisted participant, study and visit records | Reconciliation error against signed source extracts |
| Prevent obvious enrolment errors | API rejects missing registration, expired IEC approval, non-recruiting state and absent/outdated consent | Rate of prevented invalid attempts, independently reviewed |
| Timely safety review | Capture occurrence, awareness and receipt; display appropriate pending clocks | Median/95th percentile occurrence-to-notification and on-time initial reports |
| Traceable operations | Relevant committed mutations include attributable before/after audit events | Audit completeness and reviewer retrieval time |
| Least privilege | Mutation permissions and study scopes enforced server-side | Access-review exceptions and attempted cross-study access |
| Controlled study changes | Independent named review precedes amendment approval; changed consent versions flag affected participants | Reconsent completion and exceptions against approved protocol procedures |
| Reconciled intake | Preview identifies rejected and previously imported source rows; commit reuses enrolment gates | Reconciliation accuracy and source-to-record traceability |
| Reviewable terminology | Up to five lexical candidates or explicit abstention; a named reporting reviewer confirms coding | Adjudicated coding agreement, retrieval recall and abstention by language |
| Recoverable records | Backup and restoration to a new database pass SQLite and audit-chain verification | Institution-approved restoration time and data-loss limits, demonstrated in drills |
| Reusable data | Download linked FHIR research JSON and documented CSV mapping previews | Validator results and end-to-end partner acceptance |
| Usable workflow | Key demo paths work on desktop and mobile viewport | Task success, time, error rate and user feedback |

No percentage reduction in reporting delay, cost saving, diagnostic accuracy or patient outcomes is claimed. Establish a baseline before setting a pilot benefit target. A proposed pilot target is at least 90% independent completion of the five core operational tasks after brief onboarding; this is a target, not a result.

## 4. Users and jobs

Detailed profiles are in [USER_PERSONAS.md](USER_PERSONAS.md). They are design hypotheses, not interviewed AIIA staff.

| Persona | Primary decision | Scope |
|---|---|---|
| PI | Is the study recruiting safely and following the protocol? | Assigned studies |
| Coordinator | Which participant, visit or query needs action next? | Assigned studies |
| Monitor | Which record needs source verification or corrective follow-up? | Assigned studies |
| Ethics reviewer | Which approvals, consent issues and safety reports require oversight? | Authorised institutional studies |
| PV officer | Which safety case needs review, coding or reporting evidence? | Authorised safety portfolio |
| Administrator | Which accounts, assignments, study evidence and operational thresholds need action? | Institution |
| Leadership | Where should management attention and resources go? | Aggregate institution metrics |
| Regulator/auditor | Can an authorised record and its change history be inspected? | Read-only authorised scope |
| DSMB, future | What do appropriately blinded/unblinded aggregate safety data indicate? | Board charter and masking policy |

## 5. Release scope

### Release D1 — implemented synthetic-data product

- Eight permission profiles, named accounts with assigned study scopes, first-login password change, account enable/disable, password reset and session revocation. Shared demonstration roles remain an optional local exploration mode.
- Six seeded fictional studies, 100 initial synthetic participants, scheduled visits, safety cases and data queries.
- Persistent SQLite records; updates survive reload and server restart.
- Portfolio statistics and eight weekly cumulative recruitment snapshots derived from records.
- Study drill-down with protocol, site, formulation, batch and regulatory context.
- Draft creation, editable setup, six readiness checks and an audited Setup-to-Recruiting activation decision. Protocol and current consent versions are separate fields.
- Versioned Protocol, Consent and IEC PDF/TXT uploads, file hashes, controlled downloads and approval/rejection by a different named account from the uploader.
- Active-study amendments referencing approved evidence, an independent named approval, study revision checking and reconsent flags when the consent version changes.
- Consent-gated enrolment, current-version reconsent with previous metadata retained, consent withdrawal and cancelled future visit treatment.
- Visit completion and explained data-query resolution.
- Synthetic CSV preview, explicit field mapping, strict header/row checks, 1–100-row review batches, source hashes and repeat-import protection. Commit rechecks the same enrolment gates as manual entry.
- AE/SAE capture with seriousness distinct from severity.
- Initial safety-report and analysis-record metadata, with explicit external-reference fields and occurrence-based timers where applicable.
- Immutable user-supplied terminology releases, deterministic lexical suggestions, explicit abstention, named human coding confirmation, dictionary versions and previous coding decisions. Only fictional sample terms are supplied.
- Manual recipient obligations with an eligible named owner, a recorded rule basis and deadline, actual external dispatch/receipt timestamps, references and escalation history. No external transmission occurs.
- Adjustable operational thresholds for recruitment pace, IEC warning window and query age.
- Append-only application audit history, SHA-256 linkage and verification.
- FHIR R4 research collection bundle, local structural/reference checks, DM/AE mapping-preview CSV and source-provenance downloads.
- Optional single-process Waitress deployment with Docker and Caddy configuration, Secure-cookie mode, named-account bootstrap and disabled demo login by default in Compose.
- Verified online SQLite backup, read-only integrity/audit checks and restoration to a new database path.

### Release P1 — institutional pilot prerequisites

Institutional identity integration and MFA/SSO; approved account-provisioning and study-assignment procedures; approved protocol, safety and consent rules; validated electronic signatures where required; authentic source-document verification; approved storage, retention and access logging; independent audit checkpoints; operational backup schedules and restoration drills; institution-approved hosting; security testing; and incident procedures. Named accounts, uploaded files, version history and backup commands already work, but their existence does not establish institutional validation or a compliant operating service.

### Later releases

Live EDC/HIS connectors, ABDM sandbox exchange and partner certification, institution-authorised licensed terminology deployments and clinical evaluation, actual external report delivery with verified acknowledgments, randomisation integration with concealment, full CDISC export pipeline, blinded DSMB workspaces, offline-assisted capture and evaluated decision support.

## 6. Functional requirements

Priority **Must** identifies implemented release requirements, exercised on synthetic records. **Pilot** and **Later** identify additional acceptance requirements or future capabilities. Passing a Must test is not institutional or clinical approval.

| ID | Requirement and user story | Acceptance / boundary | Priority |
|---|---|---|---|
| FR01 | As an investigator, see only assigned studies | API omits out-of-scope records and rejects out-of-scope writes | Must |
| FR02 | As leadership, see aggregate progress | Individual participant/event/query/visit arrays excluded from leadership response | Must |
| FR03 | As a user, understand currentness | Display refresh cadence and last fetched time; show connection failure | Must |
| FR04 | As an administrator, configure and activate a study | Starts Setup; reason and current revision required for setup/activation; six readiness checks enforced; atomic audit history | Must |
| FR05 | As a coordinator, enrol a participant | Server validates role, scope, study state, registry date, IEC validity, capacity and consent | Must |
| FR06 | As a coordinator, document consent context | Version, language, server timestamp and recorder retained; no signature claim | Must |
| FR07 | As an authorised user, record withdrawal | Status changes; history stays; future routine visits are cancelled; safety reporting remains possible | Must |
| FR08 | As a study user, record a completed visit | Reject future visits, withdrawn consent and outstanding reconsent; require explanation; audit actual entry time | Must |
| FR09 | As a monitor, close a data query | Require resolution; reject duplicate closure; preserve before/after | Must |
| FR10 | As a PV user, capture adverse events | Validate event, participant, timestamps, narrative and seriousness; no automatic causality | Must |
| FR11 | As PI/PV, track an applicable SAE clock | Use occurrence for implemented 24h initial / 14d investigator analysis timers; label rule origin | Must |
| FR12 | As PI/PV, record evidence of external reporting | Require reference and explanatory note; prevent duplicate initial/analysis step; initial precedes analysis | Must |
| FR13 | As administrator, configure operational warnings | Limits validated; cannot modify statutory clock through alert settings | Must |
| FR14 | As monitor/auditor, inspect history | Show actor, time, action, entity, reason, before/after and digest; verify links | Must |
| FR15 | As authorised user, export data | Scoped exports, linked references, formula-safe CSV and audit event | Must |
| FR16 | As an authorised reviewer, review evidence and study changes | Named reviewer differs from uploader/submitter; immutable document versions, approval reasons and current study revision; electronic signatures are a separate pilot dependency | Must |
| FR17 | As a data manager, reconcile imported records | Synthetic CSV only; explicit mapping, 1–100 rows, per-row errors, source-key duplicate protection, reviewed transactional commit and provenance export | Must |
| FR18 | As a statistician, prepare a submission | Reviewed mapping, controlled terms, required domains, SAP-derived ADaM and validated metadata | Later |
| FR19 | As a sponsor/PI, manage randomisation | Allocation concealment, validated sequence, access separation and emergency unblinding | Later |
| FR20 | As an administrator, manage individual access | Unique username, role and valid study assignments; forced temporary-password change; revision-checked access/reset/revoke; preserve an active named administrator | Must |
| FR21 | As a study author, submit document evidence | Named upload of Protocol/Consent/IEC PDF or UTF-8 TXT up to 512 KiB; unique study/kind/version, SHA-256, scoped download; document authenticity remains a review responsibility | Must |
| FR22 | As PI/admin, amend an active study | Recruiting/Follow-up only; select three approved evidence documents; update protocol/consent/IEC/target; different named reviewer rechecks revision, readiness and capacity before applying | Must |
| FR23 | As a coordinator, record required reconsent | Current consent version and language, positive attestation and reason required; retain previous metadata; withdrawn participants cannot be reconsented | Must |
| FR24 | As PV/PI, review a dictionary suggestion | Synthetic/MedDRA AE candidates only; up to five lexical scores or abstention; named reporting reviewer chooses a release/code with reason; no automatic clinical decision | Must |
| FR25 | As a reporting user, track recipient follow-up | Manual recipient/phase/deadline/rule basis and eligible named assignee; dispatch before receipt; timestamps and references retained; escalations record external follow-up only | Must |
| FR26 | As an operator, recover a database | Backup includes committed WAL data; verify SQLite integrity and audit linkage; restore to a new path without overwriting live or existing files | Must |
| FR27 | As an operator, package a deployment | Waitress 3.0.2, single application process, Caddy proxy and persistent-volume Compose configuration; image and configuration checks pass | Must |
| FR28 | As an institutional owner, authorise real clinical use | Approved SOPs, clinical/system validation, privacy and security assessment, hosting acceptance, signatures and partner acceptance where applicable | Pilot |

## 7. Core business rules

**Enrolment is cumulative.** A withdrawn participant remains part of the number ever enrolled. Active participants and active consent are separate measures. Never silently replace the cumulative denominator with current active participation.

**Consent is more than a checkbox.** The product stores metadata and an operator attestation. An approved amendment to the consent version flags active consenting participants for reconsent and blocks routine visit completion until it is recorded. Reconsent preserves previous version/language/time/recorder metadata; it cannot revive withdrawn consent. Real use still needs approved information sheets, consent-process evidence, appropriate identity/signature controls and distinct processing/sharing permissions where required.

**SAE is not a severity category.** A mildly described symptom associated with hospitalisation can still meet a seriousness criterion. The interface therefore requires separate fields. A safety report does not establish the intervention caused the event.

**Clocks are study- and duty-specific.** The demo’s flagged NDCT study uses the investigator’s initial 24-hour and analysed 14-day paths. Other serious cases use the study’s visibly labelled internal protocol target, seeded at 24 hours. Recipient obligations let an operator record a distinct deadline and basis; they do not automatically determine applicable law. Death, injury, sponsor and EC obligations need reviewed rules and anchors before real use. [S06](SOURCES.md)

**External reporting evidence is recorded separately.** The event-level initial/analysis action records the time the operator entered the reference. Recipient follow-up additionally records the asserted actual dispatch and receipt times, their entry times and actors. A recipient reaches Acknowledged only after dispatch and receipt are recorded. These manually entered records do not independently prove delivery or notify CDSCO, CTRI, IEC or NPvCC. Recipient status does not automatically complete the separate event-level initial/analysis step.

**Activation and amendment are separate decisions.** An administrator reviews registry, ethics, versions, investigator, intervention and study period checks before activating recruitment. Setup edits and activation require the expected revision. After activation, the setup endpoint cannot directly edit the study: a submitted amendment references approved Protocol, Consent and IEC evidence and requires a different named reviewer. Approval rechecks study revision, enrolment target and readiness. None of these local decisions authenticates an external IEC or registry approval. Existing active legacy records retain missing historical approval dates explicitly; the system does not invent dates during loading.

**Corrections must be traceable.** Setup, account access, document review, amendments, reconsent, coding and recipient follow-up use guarded transitions with audit evidence. Coding changes retain the previous reviewed code and release. The product does not provide unrestricted editing of participant or event source records; broader correction workflows require preserved originals, justification, attribution and version history.

**A source identifier is an import identity, not a universal retry key.** Import identity combines source name, study and external participant ID. Repeating the same canonical source row skips an existing participant; changed values under the same identity require reconciliation. A batch containing rejected rows cannot commit, and a later enrolment-gate failure rolls back the batch. General manual enrolment/event creation does not yet accept an idempotency key.

**Terminology assistance requires human judgment and rights.** A named administrator can import a versioned package containing up to 2,000 terms. Non-synthetic packages require an explicit institutional permission declaration, retained as an unverified user declaration. WHODrug packages can be stored but are excluded from AE suggestions because they describe medicinal products. The implemented scorer compares text; its scores are not clinical confidence, causality, a validated NLP result or a licence certification.

**Individual attribution is distinct from demonstrated identity.** Named account events carry the account ID; shared-role events are explicitly labelled `demo:<role>`. Account disabling, reset, revocation and access changes invalidate existing sessions. Named local credentials improve attribution, but do not establish institutional identity assurance or validated electronic signatures.

**Synthetic means synthetic.** Registry strings beginning `DEMO-` and participant identifiers beginning `SYN-` must stay visible. Presentation counts must be labelled demonstration figures.

## 8. Information architecture

The workspace consists of Overview, Studies, Participants, Visit schedule, Safety & vigilance, Data quality, Ethics & regulatory, Data exchange, Audit trail, Documents & amendments, Integration & evidence, Access management and About. Access management appears only for administrators. Safety detail contains coding review/history and recipient follow-up; Integration & evidence provides CSV intake, provenance, export checks and terminology-package management. Primary actions are scoped to the active role. Locked/unsupported views explain their reason.

Every indicator should answer three questions: what happened, what record explains it, and what the authorised user can do next. The interface uses status text alongside colour and keeps failure messages at the form that needs correction.

## 9. Non-functional requirements

- The local `server.py` path needs Python 3.10+ and a modern browser, with only Python standard-library runtime dependencies. The optional deployment path adds pinned Waitress 3.0.2; Docker uses Python 3.12 and a Caddy proxy.
- Mutations and their audit event commit together or roll back together.
- Current demo uses a ten-second polling interval, not a sub-second or push guarantee.
- Named passwords use salted PBKDF2-HMAC-SHA256 with 600,000 iterations. Plaintext passwords and stored password hashes are excluded from API responses and audit payloads.
- Sessions and login throttles live in one process. The database and application lock support the tested single-service topology; performance and capacity remain unmeasured.
- Preserve keyboard access, visible focus, labelled forms, readable errors, responsive navigation and horizontal table containment.
- Production must specify load and availability objectives after discovering trial/site volume. Do not invent a 99.99% SLA.
- Never expose application source or database files through the static server.
- Production encryption, identity, incident response and retention must be designed and evidenced separately from the local demo.

## 10. Dependencies and risks

| Dependency/risk | Consequence | Response |
|---|---|---|
| No verified AIIA portfolio extract or interviews | Wrong assumptions about scale and workflow | Use fictional data; schedule discovery before pilot |
| Regulatory applicability differs by study | Incorrect universal deadline | Require signed applicability assessment and versioned rules |
| Dictionary rights and clinical coding quality | An imported file is not proof of a valid licence or correct coding | Preserve verbatim text, release hashes and named review; secure rights and validate coding against adjudicated examples |
| Integration access | Live partner demo unavailable | Show real local export and explicit connector contract |
| Deletion versus required research retention | Loss of evidence or over-retention | Separate withdrawal from deletion; institution approves schedule and legal basis |
| Optional shared demo identity | A shared persona cannot identify one person | Use named accounts for attributable work; Compose disables demo roles by default; approve institutional identity controls before pilot |
| File review versus source authenticity | A local approval may be mistaken for an authenticated external approval or signature | Keep version/hash/reviewer evidence and explicit boundaries; validate institutional source and signature procedures |
| Single-process SQLite deployment | Lock contention, restart logout and unavailable multi-replica sessions | Measure agreed workload before scale claims; establish hosting, recovery and concurrency requirements |
| Manual recipient follow-up | Incorrect deadlines or unverified receipt assertions | Require rule basis, eligible owner, references and review; approve real reporting SOPs separately |
| Compressed hackathon deadline | Overclaiming incomplete scope | Keep implemented/proposed evidence visible in deck and UI |

## 11. Validation and release gates

The 30 September 2026 verification run passes **59 automated test methods across API, accounts, documents, exchange, safety workflow, recovery and runtime suites, plus two Chrome workflow scripts**. Tests use isolated databases. The checks cover the original enrolment/safety/audit paths and the added named access, independent reviews, amendments/reconsent, import reconciliation, coding, recipient follow-up and recovery behaviours. This count describes test methods, not percentage coverage or the number of clinical scenarios validated. Results and commands belong in [VALIDATION.md](VALIDATION.md).

The Docker image build and smoke checks, Compose configuration and Caddy configuration validation also pass. This verifies a runnable deployment package, not actual public hosting, certificate issuance, a live TLS endpoint or institutional cloud approval.

The seeded FHIR export was checked with the **official HL7 validator 6.10.4 against FHIR R4 4.0.1: 306 resources, 0 errors, 0 fatal issues, 100 `Consent.policyRule` warnings and 100 informational notices for disabled terminology checks**. The final run used `-tx n/a -no-http-access` with cached definitions. The policy warnings concern text-only consent policy rules; the informational notices identify unconfirmed `Consent.category` terminology bindings. See [FHIR validation evidence](FHIR_VALIDATION.md) and the [raw OperationOutcome](validation/fhir-output.json). This result covers the seeded export under that configuration; it is not terminology-complete validation, HL7 certification, ABDM approval or complete CDISC conformance.

Release regression proof must retain login and scope boundaries; temporary-password restrictions and session revocation; blocked/successful activation and stale edits; current consent and withdrawal gates; independent evidence approval and amendment rollback; import duplicate/conflict handling and atomicity; timer anchors, human coding and recipient transitions; scoped exports, recovery checks and audit verification. Browser checks cover navigation, form failures, downloads, operational workflows and mobile containment.

Before a pilot: approve protocol/SOP mappings, user access matrix and privacy basis; conduct user acceptance tests and security review; validate restoration; establish record retention; complete system validation with traceable evidence. A pilot cannot be authorised solely by passing this demo’s tests.

## 12. Open discovery questions

1. Which trial types, sites and study volumes are actually active?
2. Which IEC reviews which study, and what renewal/continuing-review rules apply?
3. Which events are handled through trial safety, spontaneous PV or both?
4. Which source system is authoritative for enrolment, consent, visits and AE data?
5. Which Ayurveda assessment instruments, batches and procedure logs are already approved?
6. Which users may inspect identifiable data, export it, or see unblinded allocation?
7. What is the institution’s approved retention, cloud procurement and incident process?
8. Which external integrations can provide a sandbox and data-sharing agreement?

The research pack supplies a defensible initial design. These unresolved questions must not be relabelled as completed institutional discovery.
