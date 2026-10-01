# Website upgrades — implementation and walkthrough

Updated 1 October 2026. This register records completed website workflows and remaining institutional acceptance requirements. The current presentation describes demonstrable features in the present tense. External integration, deployment and certification claims require their own evidence.

## Stage 1 — Study readiness and activation: completed

Previously, a new study remained in Setup with no way to open recruitment. The complete workflow now connects draft creation, setup evidence, readiness review, activation, participant enrolment and audit history.

### What changed

| Area | Implemented behaviour |
|---|---|
| Study portfolio | Shows studies in setup and the count ready for activation; Review setup opens a relevant study |
| Study detail | Shows six checks with Passed/Required labels, evidence, blockers and a record revision |
| Setup form | Edits protocol, independent consent version, investigator, formulation, batch, registry and IEC references/dates, and study dates |
| Draft saving | Allows incomplete regulatory evidence to be saved while keeping recruitment locked |
| Activation | Administrator confirms review and supplies a reason; the server rechecks readiness before changing Setup to Recruiting |
| Concurrent edits | A changed revision causes 409 rejection rather than silently overwriting another update |
| Enrolment | Reuses readiness checks; validates the separate current consent version, status, capacity and participant fields |
| Audit | `STUDY_SETUP_UPDATED` and `STUDY_ACTIVATED` retain before/after values, reason and role attribution |
| Persistence | Study configuration and activation survive page reload and server restart |
| Interface recovery | A mutation waits for an in-flight refresh, then fetches current data before reopening the saved study |

### Six readiness checks

1. **Registration:** a recorded reference, not a REF application number, and a registration date no later than today.
2. **Ethics:** an IEC reference and valid approval period. New activations require an effective approval date and unexpired approval.
3. **Versions:** both protocol and current consent version are recorded; their values may differ.
4. **Investigator:** a responsible investigator is recorded.
5. **Intervention:** formulation/regimen context is recorded; compound and single-herb formulation studies also require a batch reference.
6. **Study period:** today falls between the recorded start and end dates.

These checks evaluate entered metadata, not authenticated external documents. No external registry or IEC is contacted. The investigator name remains metadata. Named accounts and study assignments are managed separately through Access management.

### Try the entire workflow

1. Open `http://127.0.0.1:8046`. Select **Research administrator**, password `Demo#26046`.
2. Open **Studies**, choose **New study** and enter:
   - Title: `Synthetic activation walkthrough`.
   - Research area: `Workflow demonstration`.
   - Target: `40`.
   - Design: `Compound formulation`.
   - Site: `Delhi`.
   - Formulation: `Fictional study formulation`.
3. Create the draft. Its detail dialog opens automatically. Observe missing evidence and the disabled **Activate recruitment** button.
4. Choose **Edit study setup**. Use different versions to demonstrate separate tracking: protocol `P-3`, consent `ICF-2`.
5. Enter investigator `Synthetic investigator`, batch `DEMO-BATCH-01`, registry reference `DEMO-CTRI-01` and registration date today or earlier.
6. Enter IEC reference `DEMO-IEC-01`, approval date today or earlier, and expiry after today. Ensure the study period includes today. These are fictional examples.
7. Add an explanatory reason and choose **Save setup**. The detail view shows **6 of 6 checks passed** when all conditions are satisfied.
8. Choose **Activate recruitment**, check the review confirmation, enter an activation reason and submit. The study displays **Recruiting**, with activation time and actor recorded.
9. Open **Participants** and enrol a synthetic adult in the new study. Selecting the study fills `ICF-2` as the current consent version. Confirm consent and submit.
10. Open **Audit trail**. Inspect setup, activation and enrolment events; expand their before/after records and verify the chain.
11. Reload the page. The saved state remains. Switch to the regulator role to see that edit/activation controls are absent.

The screenshot [05-study-readiness.png](screenshots/05-study-readiness.png) shows the tested readiness screen. Browser-test records live in a temporary database, so the exact study shown there is not added to the main dataset.

### Validation and recovery

**Verified:** 15 API integration test methods pass, plus the extended browser workflow. Checks include incomplete activation, invalid dates, future registration/approval, missing evidence, REF-number rejection, stale revisions, unauthorised roles, duplicate activation, independent consent versions, persistence and audit integrity. The browser covers create, configure, activate, reload and enrol, as well as the previous safety/export/audit flow.

Review found that a draft with a placeholder formulation could not be corrected in setup. The form and API now allow correction; the API regression verifies that the draft can become ready afterwards.

If a form reports a stale revision, close it and reopen the study after refresh. If activation remains blocked, inspect the check's explanation. If the API returns a validation error, the form retains its inputs. An active study cannot be edited through this setup form; use the reviewed amendment workflow below.

### Existing-data compatibility

No database is reset. Existing studies without a revision are treated as revision zero until edited. Old studies without a separate consent version retain their existing protocol value as the consent fallback. Old active records without an IEC approval date keep the earlier reference/expiry gate and visibly report that the historical date was not captured. New activations must record an approval date; the upgrade never invents one for existing records.

Optional demonstration personas remain available alongside named accounts. The application uses one process and SQLite. Institutional identity, authentic external evidence and approved public hosting remain separate requirements.

## Stages 2–6 — implemented and exercised

The connected workflows below run in the website. They use locally generated synthetic records; they do not imply external authority, production certification or a live hospital connection.

| Stage | Delivered behaviour | Demonstration evidence |
|---|---|---|
| 2. Individual access | Named accounts, unique usernames, salted password derivation, first-sign-in password change, per-account study assignments, disable/reset/revocation, stale-edit guards | Access management page; account and browser tests; no password material in responses/audit |
| 3. Documents and amendments | Immutable PDF/text versions with checksums; different named reviewer; approved evidence binds an active-study amendment; consent changes mark reconsent; prior consent remains in history | Documents & amendments page; self-review rejected; complete approval/reconsent browser workflow |
| 4. Source import | Synthetic CSV field mapping, row findings, source hash, explicit review, no duplicates, conflicting-source rejection, all-or-nothing commit through enrolment gates | Integration & evidence page; rejected rows explained; import and provenance checks |
| 5. Safety depth | Supplied terminology releases, lexical suggestions and named code review; assigned recipients, actual external dispatch/receipt timestamps and recorded escalation | Safety record dialog; fictional terminology demonstration; version and reviewer retained |
| 6. Deployment/recovery | Waitress WSGI serving, Docker image, Caddy/Compose configuration, private application network, health endpoint, verified backup/restore | WSGI tests, running local container smoke checks, configuration validation and recovery tests |

### Stage 2 walkthrough: named access

1. Enter the local demonstration as Research administrator and open **Access management**.
2. Create a named administrator account and a separate ethics reviewer. Assign the reviewer only `AIIA-001`. Use private temporary passwords of at least 12 characters.
3. Sign out, choose **Named account**, sign in and replace the temporary password. The workspace is blocked until this change succeeds.
4. Inspect the reviewer portfolio: only assigned studies are available. Changing a role or assignments requires an administrator and invalidates older sessions.
5. Reset or revoke a test account, then demonstrate that its older browser session cannot read records. Preserve at least one active named administrator.

### Stage 3 walkthrough: reviewed evidence and reconsent

1. As a named administrator or PI, open **Documents & amendments** and upload three small synthetic text files for `AIIA-001`: Protocol version `P-3`, Consent `ICF-3`, IEC `IEC-3`.
2. The register shows their checksums and Submitted state. The uploader cannot approve their own evidence, even with administrator permission.
3. Sign in as the assigned named ethics reviewer and review each file. Record an approval or rejection reason; a reviewed version cannot be silently overwritten.
4. Return to the named author. Submit an amendment using the three approved documents, applicable approval dates/reference and target enrolment.
5. A different named reviewer approves the amendment. The server rechecks the study revision, evidence, dates and target. An outdated competing amendment is rejected.
6. Existing consenting participants receive a reconsent requirement when the consent version changes. Routine visits are blocked until current-version consent is recorded; safety reporting remains available.
7. In **Participants**, choose **Record reconsent**, confirm the current version and language, and enter the evidence reason. **History** retains the previous consent metadata. A withdrawn participant cannot be reactivated through this form.

A document checksum proves the bytes associated with this stored version; it does not authenticate the issuer or certify a signature. Study activation remains a metadata readiness workflow; externally authentic approvals are an institutional responsibility.

### Stage 4 walkthrough: source review

1. Open **Integration & evidence** and choose **Import synthetic CSV**. The form supplies one fictional example row.
2. Select a study and source name. Upload a CSV or paste its contents. If source column names differ, provide an explicit JSON target-to-source mapping.
3. Confirm synthetic-only content and validate. Preview saves a review batch without inserting participants. Every row shows Ready, Already imported or Rejected with a reason.
4. Correct any rejected source rows and create another preview. A rejected batch cannot partially commit.
5. Confirm source/consent review and record a reason. Commit rechecks study readiness, current consent and capacity in the same transaction used for ordinary enrolment.
6. Repeat the commit or import the same source IDs again: existing participants are not duplicated. Changed values under an existing source ID are rejected for reconciliation; current records are not silently overwritten.
7. Download provenance to inspect source identity, batch ID, exact source-text hash, row hash and import timestamp. The intake records new enrolment in this workspace; it does not reconstruct unverified historical consent dates.

This is a working file intake, not an authenticated live EDC/HIS connector. The page explains the gateway, partner authentication, adapter and reconciliation architecture needed for a real source.

### Stage 5 walkthrough: terminology and recipients

1. As a named administrator, open **Integration & evidence → Terminology packages**. Import the prefilled **Synthetic** package. Its codes and labels are fictional.
2. Open **Safety & vigilance**, inspect `AE-0003`, and choose **Review code suggestions**. Select the package and request lexical candidates.
3. Inspect the original verbatim report, candidate labels and lexical scores. A score is string similarity, not clinical confidence. A named reporting reviewer selects a code and records a rationale; the original report remains unchanged.
4. A supplied MedDRA release requires the institution's declared permission. The app includes no licensed package, full MedDRA hierarchy or trained NLP model. WHODrug is recognised as a medicinal-product dictionary and is not used to code AE terms.
5. Add a recipient obligation with an active named reporting assignee, phase, deadline and rule/SOP basis.
6. Record an escalation, actual external dispatch and acknowledgment, with references and reasons. The server distinguishes actual timestamps from the time metadata was entered, rejects invalid ordering and prevents repeated dispatch/receipt.
7. Confirm the obligation becomes Acknowledged. Nothing is sent externally by these controls; they preserve evidence of external activity.

### Stage 6 walkthrough: deployment and recovery

Use [DEPLOYMENT.md](DEPLOYMENT.md) for exact commands. `ops.py backup` includes committed WAL records; `verify` checks SQLite integrity and the audit chain; `restore` creates a new destination and never overwrites a running database. Docker image build, local container health/login/export/audit checks, Compose validation and Caddy configuration validation have passed. Public DNS, certificate issuance, hosting ownership, monitoring/incident operations and institutional approval remain external deployment work.

## Stage 7 — exchange verification and remaining acceptance

**Delivered:** linked FHIR research exports, local reference checks and a reproducible official HL7 base-R4 validator run on an isolated synthetic dataset. The final run reports 306 resources, zero errors/fatals, 100 consent-policy warnings and 100 terminology-disabled information messages. See [FHIR_VALIDATION.md](FHIR_VALIDATION.md) for exact version, command, hashes and raw evidence.

**Still requires external/domain inputs:** licensed terminology validation, partner-specific profiles, ABDM sandbox acceptance and an approved SDTM/ADaM/Define-XML submission package. These are separate from generating a FHIR research collection or DM/AE-shaped CSV. [PRODUCTION_GAP_ANALYSIS.md](PRODUCTION_GAP_ANALYSIS.md) specifies the architectural delta and acceptance criteria.

## Verification and current handoff

The complete command is `.venv/bin/python tests/run_checks.py --browser`. See [VALIDATION.md](VALIDATION.md) for the latest test count and results. All three browser walkthroughs use temporary databases; their screenshots do not add test accounts, amendments or operations to the main demonstration portfolio.

The local service is `http://127.0.0.1:8046`. GitHub: [OMGP1/Anvyaya_2026](https://github.com/OMGP1/Anvyaya_2026). The baseline was published at `ea04d2d9fc172404999f7c166dee75d821a6d951`; subsequent publication needs its own recorded commit. Public hosting has not been provisioned. Use a reachable public URL in the PPT only after deployment and signed-out access testing.

## Stage 8 — Operations & alerts

1. Open **Operations & alerts** as admin, PI, coordinator or monitor. KPI cards show all assigned studies; the study filter and search narrow the tables. Leadership sees aggregates instead of individual operation records.
2. Inspect the **Alert inbox** and **Configured rules**. Admin can edit recruitment pace, IEC horizon, query age, monitoring horizon and deviation age. Safety clocks and forecast thresholds have separate stated bases.
3. **Add site**, then **Activate** with a review reason. Activation requires a ready Recruiting study. New-study activation also enables the primary site.
4. In participant enrolment, select the active site. Study/site membership, readiness, capacity and current consent are checked. Legacy callers/CSV intake without a site use the primary site only.
5. **Plan monitoring** with a site, monitor, date and scope. On/after that date, **Complete** with findings and reason. Inspect the audit entry; repeat completion is rejected.
6. **Record deviation** with study/site, optional participant, occurrence, category, owner and reason. Cross-site participants are rejected. **Close** requires corrective/preventive action and a recorded basis.
7. **Open data query**, then resolve it through **Data quality**. Ageing unresolved queries appear in the inbox.
8. Inspect the **Enrolment forecast**, trailing-rate comparison and nominal count range. State the constant-rate assumption; the synthetic slowdown scenario exposes its limitations.
9. Inspect **Formulation and batch context**. Study-level AE counts do not establish participant exposure to that batch.
10. Filter one study, open **Pre-inspection report**, inspect consent coverage/open work/audit status, then **Download HTML report**. The summary does not certify readiness or verify external approvals.

Screenshots: [desktop](screenshots/11-operations-alerts.png), [mobile](screenshots/12-operations-mobile.png). Evidence and remaining strategy items: [master strategy review](MASTER_STRATEGY_REVIEW.md).
