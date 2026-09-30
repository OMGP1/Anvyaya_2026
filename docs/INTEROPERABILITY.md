# Interoperability and data-mapping specification

**Status:** implemented CSV intake, export subset and reviewed terminology; partner integration design. **Date:** 30 September 2026.

## 1. Version and boundary decisions

- D0 targets core **FHIR R4 4.0.1** research resources.
- The ABDM implementation guide observed in research is **6.5.0**. Its current published status must be rechecked at integration time.
- DM and AE exports are **mapping previews**, not conformant submission datasets.
- Select compatible CDASH, SDTM/SDTMIG, ADaM/ADaMIG, Define-XML and terminology versions for each actual study. Do not blindly choose each standard’s newest version independently.
- Source references: [S16–S22, S25–S26](SOURCES.md).

## 2. Implemented FHIR export

| CTMS field/entity | FHIR destination | Transform | Verification |
|---|---|---|---|
| Study id | ResearchStudy.id; identifier.value | Preserve synthetic identifier | Unique resource and identifier |
| Study title | ResearchStudy.title | Preserve text | Escaped on UI; JSON serialised |
| Recruiting | ResearchStudy.status = active | Explicit status lookup | Allowed R4 value |
| Setup | ResearchStudy.status = in-review | Demo mapping only | Does not mean IEC formally accepted a submission |
| Follow-up | ResearchStudy.status = closed-to-accrual | Distinguish closed recruitment from completion | Allowed R4 value |
| Study start/end | ResearchStudy.period | Date-only ISO values | No invented timestamp precision |
| Participant id | Patient.id and identifier | Synthetic pseudonym | No direct identifiers |
| Recorded sex code | No Patient.gender mapping | Deliberately omitted from FHIR Patient | Biological sex and administrative gender are different concepts; preserve the original sex field in the research mapping |
| Participant-study link | ResearchSubject.study / individual | Resolve to fullUrl values | Every reference resolves within bundle |
| Enrolled / Withdrawn | ResearchSubject.status | on-study / withdrawn | Allowed R4 values |
| Consent flag | Consent.status | active / inactive | Reflect withdrawal |
| Consent record | ResearchSubject.consent | Link to Consent resource | Reference resolves |
| Consent time | Consent.dateTime | Preserve UTC | Valid timezone-aware dateTime |
| Consent context | scope=research; category=consent document | Core coding plus policy text | No signature or ABDM permission claim |

`Bundle.type` is `collection`. The example host in `fullUrl` is a namespace for export linkage; it is not a running FHIR REST server. No CapabilityStatement, search API, FHIR import or terminology server is implemented.

## 3. DM and AE mapping previews

| Source | Preview field | Meaning / caveat |
|---|---|---|
| study_id | STUDYID | Stable study identifier |
| constant | DOMAIN | DM or AE |
| participant id | USUBJID, SUBJID | Synthetic subject identity; production uniqueness rules must be approved |
| participant site | SITEID | Demo city label; production requires a stable site code |
| age | AGE; AGEU=YEARS | Exact integer synthetic age; source derivation not implemented |
| sex | SEX | Demo field; controlled terminology review required |
| consent_at | RFICDTC | Consent timestamp; not treatment/reference-start date |
| event index | AESEQ | Export sequence; production sequence must be stable per subject/source record |
| verbatim term | AETERM | Do not replace with an inferred preferred term |
| severity | AESEV | Uppercase demo severity; versioned terminology review required |
| serious | AESER | Y/N, separate from severity |
| occurred_at | AESTDTC | Event onset timestamp |

Missing elements include full required/permissible domain variables, MedDRA-coded terms, action/outcome/causality details, many timing/arm variables, XPT and complete metadata. CSV formula prefixes are neutralised for safe spreadsheet opening; the CSV is not the canonical source dataset.

## 4. Proposed additional mappings

| CTMS concept | Candidate FHIR representation | Candidate CDISC domain | Required review |
|---|---|---|---|
| Vital measurement | Observation with unit/code/time | VS | UCUM units, visit timing, method and result precision |
| Concomitant medication | MedicationStatement / MedicationAdministration | CM | Indication, start/end, coding, source semantics |
| Actual exposure | MedicationAdministration or protocol-defined source representation | EC / EX as appropriate | Collected versus derived exposure distinction |
| Procedure | Procedure plus protocol context | PR / relevant domain | Match model and design; do not force all Panchakarma records into a drug domain |
| AE/SAE | AdverseEvent plus subject/study context | AE | Required R4 fields, seriousness, coding and causality semantics |
| Assessment | Observation / QuestionnaireResponse | QS / FA / justified mapping | Instrument rights, scale version, item-level traceability |
| Audit/change provenance | AuditEvent / Provenance | Source lineage / metadata | These are not interchangeable; model actor/activity/entity correctly |
| Analysis dataset | No automatic one-resource equivalent | ADaM | Approved SAP, derivations, analysis population and traceability |

These are design candidates. A mapping must preserve meaning; one-to-one equivalence cannot be assumed. Ayurveda-specific concepts may need governed extensions or documented supplemental data rather than invented standard codes.

## 5. ABDM connector contract, planned

1. Confirm whether the application acts as HIP, HIU, or uses an existing institutional component.
2. Obtain institutional authorisation, sandbox access and current API/consent specifications.
3. Select a supported clinical artefact, such as an OP consultation or diagnostic record, with a legitimate research-use and sharing basis.
4. Produce/consume the required Composition-based document with the applicable DocumentBundle and resource profiles.
5. Handle consent artefacts, purpose, data minimisation, linking, encryption/exchange requirements and revocation according to the approved integration.
6. Validate against the pinned profile package and run negative tests for missing/expired permissions and wrong-patient linkage.
7. Reconcile imported records and retain source provenance; never silently overwrite trial-approved data.

Research consent is not automatically an ABDM data-sharing consent artefact. An ABHA identifier should not be requested solely to make a hackathon screen look interoperable.

## 6. EDC/HIS ingestion contract, planned

Each import should carry source system, source record identifier, source version, study/site binding, event type, occurred/updated time, payload hash, mapping version and import status. Use an idempotency key based on source identity/version. Conflicts go to a review queue.

Start with one documented partner API or approved file export. Polling or signed webhooks depend on the partner’s capabilities. Validate data at the boundary, scope credentials per institution, retry safely, and preserve rejected records without placing patient details in operational logs.

## 7. Validation gates

| Gate | D0 evidence | Production requirement |
|---|---|---|
| Parseable output | JSON and CSV downloads | Automated schema/version checks |
| Record linkage | All exported research references resolve | Cross-system identity reconciliation |
| Required resource elements | Official base-R4 validator: zero errors; consent-policy warnings and disabled terminology checks documented in [FHIR_VALIDATION.md](FHIR_VALIDATION.md) | Resolve applicable policy/terminology findings and validate recipient profiles |
| ABDM conformance | Not claimed | Profile validation and sandbox partner acceptance |
| SDTM conformity | Not claimed | Complete domains and approved rule checks |
| ADaM traceability | Not implemented | SAP-based derivations, independent programming/review |
| Define-XML | Not implemented | Schema, codelist, origin and dataset metadata validation |
| Reproducibility | Persistent source records | Frozen snapshot, mapping/version manifest, checksums and reviewer sign-off |

The slide phrase is **“FHIR research export and CDISC mapping foundation”**, not “one-click submission-ready interoperability.”

## Implemented intake, coding and validation update — 30 September 2026

`exchange.py` now implements synthetic CSV intake: exact source-text hashing, explicit canonical-to-source mappings, a persistent preview, row findings and a reviewed transactional commit. It accepts 1–100 rows with external ID, age, sex, Prakriti, current consent version, language and explicit consent confirmation. Source/study/external-ID keys prevent duplicates; changed values under an existing key are rejected. Commit invokes the ordinary enrolment handler, preserving readiness, consent and capacity gates. A separate provenance CSV exposes lineage. It is not a live EDC API, historical participant merge or FHIR importer.

The FHIR exporter adds generated XHTML narratives. The official HL7 validator checked the 306-resource fresh synthetic export against base R4 4.0.1: zero errors/fatals, 100 consent-policy warnings and 100 terminology-disabled notices. See [FHIR_VALIDATION.md](FHIR_VALIDATION.md) for the unmodified report, pinned tool and reproducible offline invocation. Local `/api/exchange/check` evaluates structural/reference checks only and is not a replacement for that Java validator.

`safety_workflow.py` accepts a supplied versioned dictionary package and records named code approval without changing the verbatim report. No licensed terms or full MedDRA hierarchy ship with this repository. Reviewed coding is visible in the case record; the existing AE CSV remains a mapping preview and does not claim a full coded submission domain. The browser explains the exact difference between current CSVs and a released SDTM/XPT/Define-XML package.

[PRODUCTION_GAP_ANALYSIS.md](PRODUCTION_GAP_ANALYSIS.md) supplies the partner gateway/OAuth/SMART design, source reconciliation contract, versioned CDISC release pipeline and terminology-assistance evaluation. Those designs do not imply partner credentials, clinical acceptance or external report delivery.
