# Demo script and judge Q&A

## Start and rehearse

```bash
cd /Users/om/Projects/Sih_2026_winning_project_2
python3 server.py --port 8046
```

Open **http://127.0.0.1:8046**. The local demonstration permits Research administrator login with **Demo#26046** when demo login is enabled. Named accounts are also implemented. Create fictional rehearsal accounts in **Access management**, assign the required studies, and complete each account's first-login password change before presenting. Use named accounts for document submission/review, amendments, dictionary imports and coding approval. Keep passwords off the slides. Shared role login attributes actions to a demo role; it is not individual identity evidence.

The study data and rehearsal identities are fictional. Use a fresh database for a repeatable seed if needed without deleting the existing one:

```bash
CTMS_DB=data/rehearsal.sqlite python3 server.py --port 8047
```

Existing filenames preserve previous demo actions. Choose another filename for another fresh run. Do not reset the main database during a live presentation.

Prepare a named administrator, a principal investigator assigned to `AIIA-001`, an independent ethics reviewer assigned to that study, and a PV reviewer with the same assignment. Document upload/review and amendment submission/approval must use different individuals. A named administrator can demonstrate terminology import; a named PV reviewer can demonstrate final code selection.

Use [VALIDATION.md](VALIDATION.md) for documented integration and browser checks and their current results. This script is a rehearsal guide, not a replacement validation record. The [production gap analysis](PRODUCTION_GAP_ANALYSIS.md) supplies detailed rationale and acceptance criteria for the five production questions.

## Five-minute walkthrough

| Time | Action | Say | Evidence |
|---|---|---|---|
| 0:00–0:30 | Open overview as a named user | “The same persistent synthetic records drive this portfolio, its exports and its audit history.” | Scoped studies, derived KPIs and identified account |
| 0:30–1:00 | Open a study and inspect readiness | “Recorded registration, current ethics approval and applicable consent are checked before recruitment.” | Six checks; formulation, batch and study versions |
| 1:00–1:35 | Attempt enrolment in an unready setup study; then inspect a valid enrolment | “Missing prerequisites are rejected by the server; valid enrolment creates visits and audit evidence.” | Blocked action and saved participant |
| 1:35–2:15 | Documents & amendments → prepared reviewed records | “A different named reviewer approves evidence; changing consent marks participants for recorded reconsent.” | Upload checksum, submitter/reviewer, revision and consent history |
| 2:15–2:55 | Safety & vigilance → prepared synthetic terminology suggestions | “These are lexical candidates, not clinical confidence. A named reviewer selects the code; the original text remains.” | Synthetic package version, candidate score and recorded coding |
| 2:55–3:30 | Inspect a recipient obligation | “Dispatch and receipt are manually recorded external evidence with separate timestamps; the app does not send reports.” | Assignee, deadline basis, dispatch, receipt and escalation |
| 3:30–4:15 | Integration & evidence → prepared CSV batch; Data exchange → check/download | “Rows are mapped, reviewed and committed through existing gates; duplicate protection and provenance survive.” | Row findings, import outcome, provenance and local FHIR checks |
| 4:15–4:45 | Audit trail → Verify chain | “Named actions retain reasons and before/after values, with checkable hash links.” | Account, amendment/import/coding events and verification |
| 4:45–5:00 | Show integration acceptance path | “The implemented core is inspectable; institutional hosting, licensed sources and a real partner still need acceptance.” | Clearly labelled partner onboarding design |

For a three-minute slot, show the readiness failure, one completed evidence/reconsent chain, one safety case and the audit record. Prepare sample records before the timed walkthrough so account setup and long form entry do not consume the slot. Never substitute a screenshot of a planned screen for a working interaction.

## New study activation walkthrough

For the complete create-to-enrol path, follow [WEBSITE_UPGRADE_STEPS.md](WEBSITE_UPGRADE_STEPS.md). Create a draft, save protocol/consent and registry/IEC metadata, inspect all six checks, then activate with a reason. Enrol using the study’s current consent version and inspect `STUDY_SETUP_UPDATED` and `STUDY_ACTIVATED` in the audit view. The recorded references remain fictional.

## Optional evidence, import and coding exercises

### Reviewed amendment and reconsent

1. As the named PI, upload synthetic protocol, consent and IEC PDF/TXT files with explicit versions. The server retains their checksums and rejects overwriting an existing study/kind/version.
2. As a different named ethics reviewer, approve each document with a reason. The uploader cannot approve their own file version.
3. As the PI, submit an amendment for a recruiting study using the approved evidence, valid IEC dates and a target at least as large as recorded enrolment.
4. As the independent reviewer, approve the current revision. A stale proposal or self-approval is rejected.
5. Show an affected active participant marked for reconsent. Record consent to the current version as an authorised operator; inspect the retained earlier consent metadata. A withdrawal must remain a withdrawal.

The application records a reviewer decision; it does not verify the issuer's signature, act as an IEC or establish participant understanding.

### CSV staging and provenance

1. Use the synthetic CSV sample in the integration screen. Review its source name, study assignment and explicit source-to-target field mapping.
2. Preview the batch. Demonstrate one invalid consent version or invalid value and its row-level finding; fix the source and create a new preview.
3. Confirm review and commit valid rows. The server executes the existing enrolment operation, including current readiness, capacity and consent checks.
4. Preview the same source again: matching rows are already imported. Reusing a source ID with changed content produces a conflict instead of silent replacement.
5. Inspect the imported participant's source/import IDs and file/row hashes; download provenance and the FHIR research export. Explain that the FHIR check is local structure/reference validation.

This is a controlled synthetic CSV connector. A real EDC/HIS adapter, source-version update workflow and approved identity linkage require partner-specific implementation and acceptance.

### Terminology review and recipient follow-up

Import this small example through the dictionary form using **kind: Synthetic**, a release such as `demo-1`, and a descriptive name. It is a test vocabulary, not MedDRA or WHODrug data:

```json
[
  {"code": "SYN-DIZZINESS", "label": "Dizziness"},
  {"code": "SYN-NAUSEA", "label": "Nausea"},
  {"code": "SYN-IRRITATION", "label": "Skin irritation"}
]
```

As the PV reviewer, open a corresponding synthetic event, inspect suggestions, then select a code with a reason. The display uses **lexical similarity**, and may abstain when no candidate reaches the threshold. Inspect the unchanged narrative and dictionary version. Recode against a new supplied release only with a reason; previous coding remains in history. A WHODrug package is not an AE dictionary and is rejected for AE coding.

Create a recipient obligation with a named reporting assignee, phase, explicit deadline and rule basis. Record an external dispatch timestamp/reference, then a receipt timestamp/reference. Try an out-of-order or future timestamp and inspect the rejection. Escalation records follow-up without marking an acknowledgment. These steps do not transmit anything externally or automatically determine every statutory obligation.

### Recovery evidence

Show the documented backup verification and restore results in [VALIDATION.md](VALIDATION.md). The delivered `ops.py` uses SQLite's backup API and verifies integrity/audit linkage. Restores target a new database path; do not replace the active rehearsal database on stage. The Docker build and local health/login/FHIR/audit smoke checks passed; Compose and Caddy configuration validation also passed. Those checks establish a local deployment path, not a public HTTPS endpoint or measured cloud recovery SLA.

## Inputs for the live safety example

- Participant: `SYN-01-001`.
- Event term: `Synthetic unplanned hospital admission`.
- Seriousness: `Hospitalisation`.
- Severity: `Moderate`.
- Occurrence/awareness: keep the prefilled current local time.
- Narrative: `Fictional demonstration case. No actual participant or clinical outcome is represented. Causality remains unassessed.`

The seeded AIIA-001 is flagged NDCT applicable solely to illustrate that pathway. This is not a legal classification of an actual Ayurvedic product.

## If something goes wrong

| Symptom | Recovery |
|---|---|
| Port occupied | Choose `--port 8047` and use that URL |
| Page cannot connect | Confirm server terminal is still running |
| Signed out after server restart | Log in again; records remain |
| Old view after code changes | Restart backend, reload browser; no frontend build needed |
| Wrong role cannot act | Switch to administrator or the relevant operational role |
| Document or coding action requires a named account | Sign in with the prepared individual account; shared demo identity is deliberately insufficient |
| Own document or amendment cannot be approved | Use the independent reviewer; do not weaken the control for the demo |
| Amendment is stale | Review the current study and submit a new proposal against its revision |
| Routine visit is blocked after an amendment | Record genuine synthetic reconsent to the current version before demonstrating routine visit completion |
| CSV preview reports a conflict | Reconcile the source ID and contents; do not relabel an existing person just to bypass duplicate protection |
| No terminology suggestion appears | Explain abstention; review the source and package instead of forcing an unrelated code |
| Enrolment blocked | Choose a ready recruiting study, its current consent version and adult age |
| Deadline no longer looks imminent | Demo data was seeded earlier; use a fresh database filename for a new rehearsal |
| No internet at venue | Local app requires no CDN, external fonts or API connection |
| Live demo unavailable | Use `docs/screenshots/`; label screenshots as prototype evidence |

## Judge questions and defensible answers

### 1. Why build this instead of using REDCap or OpenClinica?

They are credible systems with established capture and audit capabilities. Anvaya focuses on Ayurveda-specific portfolio oversight and connected institutional workflows. Where an institution already has EDC, the integration design preserves that source and stages authorised data before existing domain gates allow a write. We do not claim those tools lack permissions or audit logs.

### 2. What is genuinely new here?

The product composition: Ayurveda context, reviewed study evidence, reconsent, attributable oversight, governed imports and safety follow-up in one workflow. The building blocks are standard. Pilot feedback must establish whether that composition improves the institution's work; we do not claim an invented algorithm or measured institutional benefit.

### 3. Is this GCP compliant?

It demonstrates controls motivated by GCP and data-integrity requirements. Compliance also depends on validated software, SOPs, people, training and operations. We are not claiming a certified or validated production system.

### 4. Is the audit trail immutable?

The app prevents update/delete through its audit table and verifies a SHA-256 chain. That is tamper evidence. Independent protected storage, checkpoints and administrative separation are needed for stronger immutability assurances.

### 5. Does your app actually enforce RBAC?

Yes. Named local accounts carry roles and managed study assignments; the server checks actions and record scope. Password reset, first-login change and session revocation are implemented. Document approvals and final coding decisions require named accounts. Shared role login remains a local demo option. Institutional SSO/MFA, identity proofing and access-review procedures remain deployment work.

### 6. Why are you not using blockchain?

We have one institutional record owner in the initial scope. A transactional journal with protected independent retention is simpler to validate. Blockchain would not prove the correctness of a source record or the validity of consent.

### 7. Are the trial data real?

No. Studies, personnel, participants, adverse events and registry identifiers are fictional. The problem statement explicitly supports synthetic/de-identified development. No clinical efficacy or safety inference is made from these counts.

### 8. Do all Ayurveda trials follow NDCT safety timelines?

No. Applicability must be determined for the study and product. One synthetic study demonstrates the 24-hour initial and 14-day investigator analysis branch; other studies use an internal SOP target. Recipient obligations now record the chosen assignee, deadline and rule basis explicitly. That does not automatically determine every legal actor, recipient, outcome or exception.

### 9. What starts the safety clock?

For the implemented NDCT investigator path, occurrence. Awareness and server receipt are separate fields and do not reset it. Other legal duties can have different anchors; the production rules must preserve those distinctions.

### 10. Does clicking “Record initial” notify the regulator?

No. The report-step action saves metadata. The recipient workflow additionally records manually entered dispatch and receipt times/references, responsible users and escalation history. Entry time is separate from claimed external event time. There is no transmission, authenticated receipt or automatic filing; an approved partner connection must supply that evidence.

### 11. Is an AE proof that an Ayurveda medicine is unsafe?

No. An AE is an event record. Suspected causality, coding and signal assessment require appropriate expert review and evidence. We keep seriousness separate from severity and do not infer causality automatically.

### 12. How do you handle consent withdrawal?

We record the request, block routine study-visit completion and retain history; safety reporting remains available. Consent amendments separately mark active participants for reconsent, and recording reconsent preserves the previous consent metadata. Real deployment must distinguish participation, processing/sharing permissions and required retention. These controls must not obstruct necessary clinical care.

### 13. Is this ABDM integrated?

The app exports a FHIR R4 research collection and performs local resource/reference checks. ABDM clinical DocumentBundle profiles, authorised consent exchange, HIP/HIU roles and sandbox acceptance are a separate contract. We have not connected an ABDM environment or received official profile acceptance. See the [ABDM implementation guide](https://nrces.in/ndhm/fhir/r4/).

### 14. Are your CSVs submission-ready SDTM?

They are DM/AE mapping previews. A submission release requires an agreed recipient and compatible SDTM/SDTMIG versions; all applicable domains; reviewed variables, types, lengths, labels, controlled terms and derivations; stable source lineage; actual required transport; validated Define-XML; reconciliation and authorised release. XPT, where required, needs a real writer and independent read-back. `--TPT` means a planned time-point name, not a file format. ADaM separately needs the approved analysis plan and statistical derivations. FDA transport requirements do not automatically apply to every Indian study. [CDISC SDTMIG](https://www.cdisc.org/standards/foundational/sdtmig/sdtmig-v3-4), [FDA technical guide](https://www.fda.gov/media/153632/download), [Define-XML](https://www.cdisc.org/standards/data-exchange/define-xml).

### 15. What AI have you implemented?

The implemented terminology assistant uses deterministic token and string matching against a supplied dictionary package. It displays up to five candidates as lexical similarity and abstains below its threshold. A named reporting reviewer chooses the final code; original text and earlier coding versions remain. There is no trained NLP model, forecasting model, clinical confidence score or automatic causality decision.

### 16. Can you use MedDRA and WHODrug freely?

Access and redistribution depend on the relevant licences and institutional arrangements. The app can import a supplied package with its version and checksum; non-synthetic imports require an institutional licence declaration, which is not independent verification. No licensed term set is bundled in the repository. Synthetic examples remain labelled synthetic. MedDRA supports medical-event coding; WHODrug describes products and is rejected for AE coding here. A governed medication-coding workflow remains separate. [MedDRA terms](https://tools.meddra.org/wbb/eula.htm), [WHODrug Global](https://who-umc.org/whodrug/whodrug-global/what-is-whodrug-global/).

### 17. Does DPDP require every health record to stay in India?

No universal claim follows from DPDP alone. An institution-approved India hosting arrangement is the initial design choice, with transfer restrictions, contracts and sector/procurement rules reviewed separately. CERT-In specifically requires relevant ICT logs to be retained within India. Clinical records, safety records, audit evidence, security logs and backups need their own retention basis; 180 days is not a universal clinical retention period. [DPDP Act](https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf), [CERT-In directions](https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf).

### 18. Is DPDP fully in force already?

The official instruments use phased commencement. As of 30 September 2026, later one-year/eighteen-month tranches from November 2025 have not elapsed. The production owner must review the consolidated instruments, corrigendum and operative dates before go-live. Application features or a cloud configuration do not establish DPDP compliance or “CERT-In certification.” [Commencement notification](https://www.meity.gov.in/static/uploads/2025/11/c56ceae6c383460ca69577428d36828b.pdf), [final Rules](https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf).

### 19. How much does this save?

We have not measured savings. The pilot will compare task time, reconciliation errors, query age and reporting timeliness against a documented baseline. Local demo operation has no external API dependency; production costs include hosting, operations, licences, security and validation.

### 20. Can it scale across many sites?

The current persistence is SQLite with serialised application writes. A WSGI adapter, pinned Waitress and HTTPS reverse-proxy configuration are delivered, along with backup/restore tools. Multi-site acceptance still needs measured concurrency, availability and recovery, institutional identity and security review. A PostgreSQL migration, when justified, must preserve identifiers, document checksums and exact audit payloads, reconcile records and rehearse rollback. No load-tested capacity claim is made.

### 21. What happens if data changes during export?

The current process serialises operations while creating its small export. A production export must freeze a reviewed snapshot and record mapping versions, checksums and reviewer sign-off.

### 22. What must happen before AIIA uses it?

The software base now includes named identity, document review, amendments, controlled imports, safety follow-up and recovery tooling. Institutional adoption still requires approved SOPs and evidence, identity onboarding/MFA, secure hosting and retention, licensed sources where used, one authorised partner mapping, formal workflow/security/recovery validation and institutional acceptance. Validated electronic signatures and full clinical submission releases are separate work.

### 23. Why should a dashboard block enrolment?

Prospective registration supports scrutiny of the intended study before recruitment. Current IEC approval records the ethical basis for the activity. Applicable consent documents voluntary participation in the approved information and process. Anvaya checks the recorded evidence when the action occurs and exposes what is missing. Software cannot prove authentic issuer documents or informed understanding. This is a standards-based control rationale, not a measured claim about AIIA misconduct or Ayush failure rates. [CTRI FAQ](https://ctri.nic.in/Clinicaltrials/faq.php), [ICMR ethical guidelines](https://ethics.ncdirindia.org/asset/pdf/ICMR_National_Ethical_Guidelines.pdf), [GCP-ASU](https://ccras.nic.in/wp-content/uploads/2025/09/3.-ASU-GCP-Guidelines.pdf).

### 24. What is the real EDC/HIS integration path?

Select one authorised partner, its supported API/file format and its permitted data use. Use documented authentication: OAuth client credentials or SMART Backend Services only where the partner supports the relevant flow. Record source identity/version, event and receipt times, payload hash and mapping release. Validate, stage, match using approved study-subject linkage, review conflicts and call existing domain commands before acknowledging an accepted change. Replays must be safe; changed content under the same identity must be a conflict. Our delivered CSV workflow proves part of this path, not a live hospital connection. [FHIR REST](https://hl7.org/fhir/R4/http.html), [OAuth client credentials](https://www.rfc-editor.org/rfc/rfc6749#section-4.4), [SMART Backend Services](https://hl7.org/fhir/smart-app-launch/backend-services.html).

### 25. How will a future NLP coding model be evaluated?

Use an authorised reference set with independent trained coders and adjudication. Hold out related cases together; fix dictionary/model versions and evaluate by language, rarity and ambiguity. Measure top-1 correctness, top-k recall, acceptance/override, abstention coverage, error among displayed suggestions and reviewer time. Inspect negation and clinically significant miscoding. Select thresholds with the PV lead and require regression checks before a release. A similarity score is not calibrated clinical confidence; we have no trained-model accuracy claim. [MedDRA term-selection guidance](https://files.meddra.org/www/Website%20Files/PtCs/001329_termselptc_r4_26_mar2026%20%281%29.html).

### 26. Does a reviewed PDF prove ethics approval?

It proves that the stored file version has a checksum and an attributable reviewer decision. The independent reviewer must verify issuer, site/study, scope, dates and versions using the institution's process. The application does not authenticate an IEC signature or replace the committee's approval. A validated electronic-signature ceremony requires further controls and acceptance.

### 27. Does the six-hour CERT-In clock apply to clinical SAEs?

The six-hour duty discussed in the hosting research concerns specified cyber incidents under CERT-In. Clinical safety timelines depend on study/product applicability, actor, recipient and protocol. They are separate workflows and must not share a misleading universal timer. [CERT-In directions](https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf).

## Last check before submission

- Replace team/college placeholders in your own slides.
- Follow your college’s actual template and slide-count requirement.
- Keep every demo metric labelled synthetic.
- Open the app and rehearse the exact study names once.
- Rehearse named-user access, independent review, reconsent, import provenance and safety follow-up using the submitted build.
- Use the documented integration and browser checks in [VALIDATION.md](VALIDATION.md); do not repeat stale test counts.
- Confirm the public UI address and [GitHub repository](https://github.com/OMGP1/Anvyaya_2026) open for the intended reviewer; localhost is a rehearsal address.
- Avoid claiming a deployment, certification, integration or measured benefit that has not happened.

## Updated answer: official FHIR validation

The official HL7 Java validator 6.10.4 checked the fresh synthetic 306-resource export against base R4 4.0.1 with zero errors/fatals. There are 100 text-only consent-policy warnings and 100 notices because terminology service validation was disabled. The final cached run disabled HTTP. We preserve these findings and make no ABDM, terminology, clinical-system or certification claim. The command, hashes and unmodified outcome are in [FHIR_VALIDATION.md](FHIR_VALIDATION.md).

## Operations addition: short judge walkthrough

Open **Operations & alerts**. Explain an alert's rule and owner, then show a scheduled monitoring visit, recorded findings, a deviation and corrective action. Add a query and resolve it through Data quality. Filter one study and download its pre-inspection HTML. These records use existing permissions and transactional audit.

**How accurate is the forecast?** It is a constant-rate study-level prototype with synthetic holdouts. The nominal 90% count interval covered 91.33% of constant-rate outcomes but only 24% after an unforeseen 50% slowdown. Point forecasts were similar to the trailing-rate baseline. This exposes limitations; it is not clinical validation or superior recruitment performance.

**Why no batch PRR?** The batch is study metadata. Verified participant exposure and comparable coded product/event report counts are absent. The delivered table is descriptive study context; it does not infer causality or equate enrolment with exposure.

**What remains from the master strategy?** Sites, monitoring, deviations, query creation, rules/inbox, forecast and HTML report work. Local LLM reranking, licensed dictionary scale-up, exposure capture, full SDTM/Define-XML, ODM ingestion, validated signatures and independent checkpoints have documented acceptance gates. Public hosting needs an authorised host and domain. See [MASTER_STRATEGY_REVIEW.md](MASTER_STRATEGY_REVIEW.md).
