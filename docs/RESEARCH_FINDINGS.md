# AIIA CTMS — Research findings and product implications

**Research date:** 29 September 2026. **Scope:** official problem statement, supplied research plan, official rules/standards, selected primary research and software documentation.  
**Evidence register:** [SOURCES.md](SOURCES.md). **Requirement traceability:** [REGULATORY_TRACEABILITY.csv](REGULATORY_TRACEABILITY.csv).

## 1. Recommendation

Position Anvaya as **a traceable research-operations workspace for Ayurveda**. The strongest initial demonstration is a connected workflow: an enrolment is checked against study readiness and consent; an SAE carries an applicable clock; a review action creates audit evidence; the same records support a structured export.

The defensible innovation is the composition of Ayurveda context, study-specific oversight and explainable operational rules. A dashboard, RBAC, FHIR and an audit trail are individually established ideas. Do not claim a first-ever CTMS or invented clinical accuracy. The best evidence tonight is software that works and an honest route to institutional validation.

## 2. What the official problem actually asks

The official SIH page confirms PS 26046, Ministry of Ayush / All India Institute of Ayurveda. It requests a cloud-oriented CTMS with portfolio and study oversight, role-based KPIs, ethics/registry tracking, pharmacovigilance, clinical-data standards and auditability. It explicitly permits staged implementation. [S01](SOURCES.md)

Therefore a credible D0 need not pretend to deliver full regulatory submission automation. It should demonstrate the highest-risk interactions and describe the acceptance gates for later capabilities. The present deliverable is a local, persistent, synthetic-data MVP with a deployment path; it has not been deployed on a compliant public cloud.

“GCP” in this clinical context means **Good Clinical Practice**. It does not require Google Cloud Platform. Cloud procurement is a separate decision.

## 3. Domain discovery

### Trial lifecycle

| Stage | Operational evidence | Ayurveda-specific consideration | D0 status |
|---|---|---|---|
| Protocol and feasibility | Study question, design, endpoints, sample-size basis, sites | Fixed product, personalised regimen, procedure or observational design | Representative metadata |
| Product/procedure preparation | Product identity, manufacturing/batch documentation, accountability, SOP | Botanical/formulation identity and procedure standardisation | Formulation and batch references only |
| Ethics and registration | IEC decision/version, CTRI registration, applicable permissions | ASU guidance plus design-specific regulatory pathway | Seeded records and enrolment guards |
| Site activation | Staff delegation, training, essential documents and readiness | Procedure resources and product availability | Recruiting state represents seeded readiness; activation workflow planned |
| Consent and screening | Approved information/consent, eligibility criteria, screening record | Protocol-defined Prakriti tool and other assessments | Consent metadata; no complete screening CRF |
| Enrolment/allocation | Unique subject, date, arm if applicable | Stratification only if scientifically justified in protocol | Enrolment works; randomisation absent |
| Treatment/follow-up | Visits, intervention accountability, outcomes, deviations | Procedure sessions, Pathya-Apathya adherence, regimen changes | Visit completion; detailed CRFs planned |
| Data review and safety | Queries, coding, source verification, AE/SAE review | Product/batch/procedure context supports investigation | Queries and safety workflow work |
| Lock, analysis and close-out | Resolved data, lock sign-off, analysis plan, final reports | Standardised mapping must preserve original concepts | Roadmap |

Trial-specific screening procedures need appropriate prior consent. Administrative prescreening and routine clinical care may follow different approved arrangements. A production workflow must define this distinction; the demo starts at documented enrolment.

### Data that a generic trial template may overlook

- **Prakriti:** assessment instrument, version, assessor, date, raw observations and derived classification. Do not store only a label if the trial requires reproducibility.
- **Dosha or other Ayurveda assessments:** retain the protocol’s definitions and assessment scale. Avoid inventing universal coding.
- **Intervention:** distinguish product, compound formulation, procedure and whole-system regimen. Capture changes at the participant/time level when the protocol allows personalisation.
- **Product traceability:** ingredients, authentication, manufacturer, batch, certificate/reference, expiry and dispensing accountability as applicable.
- **Procedures:** session type, trained operator, planned/actual duration, protocol deviations and concomitant interventions.
- **Diet/lifestyle:** protocol-defined adherence evidence. Missing adherence is not proof of non-adherence.
- **Blinding:** taste, smell or procedures may make masking difficult. Record the actual design and safeguards; never label an unblinded workflow “double blind” for appearance.

The MVP implements only Prakriti label, intervention design, formulation/regimen and batch reference. The remaining fields are a proposed data-collection specification for investigator review, not invented production records. [S04, S05](SOURCES.md)

## 4. Gap analysis and user decisions

These gaps derive from the SIH statement and workflow analysis, not direct measurement at AIIA.

| Current pattern described or hypothesised | Failure mechanism | Product requirement | Evidence to collect in a pilot |
|---|---|---|---|
| Separate recruitment sheets | Different counts and update times | One source-linked count with visible denominator | Reconcile a sample against signed site logs |
| Calendar/email ethics reminders | An expiry is missed or assigned to nobody | Date, owner, threshold and evidence of review | Missed/late reminders before and after pilot |
| Safety narratives in disconnected channels | Unknown start time and unclear recipient | Occurrence, awareness, receipt, duty, recipient and acknowledgement | Trace a mock SAE end to end |
| Manual consent version tracking | Old form used after amendment | Approved version gate and reconsent queue | Number of obsolete-version attempts caught |
| Unexplained edits | Reviewer cannot reconstruct why a value changed | Versioned corrections and audit history | Blind reconstruction exercise |
| Manual report reformatting | Semantic loss during export | Explicit mapping, terminology and lineage | Validator and reconciliation results |

## 5. Regulatory findings that change the design

### Registration and ethics

CTRI requires prospective registration. An application reference is not the assigned registration number. The platform should record registration status, assigned identifier, date and verification evidence, and block trial enrolment when required registration is absent. [S03]

An Ethics Committee’s institutional registration and its approval of a particular study are different records. NDCT Rule 7 concerns committee constitution; registration and study-specific protocol approval are distinct processes. A Form CT-02 reference must not be treated as the study’s approval letter. [S06]

Do not infer that every IEC approval expires exactly one year after its date. Store the actual approved period and continuing-review requirements. CTRI’s current declaration about the recency/validity of submitted ethics documents is not a universal one-year expiry rule for every committee decision. [S03, S05]

### SAE reporting

The inspected NDCT text supports the initial investigator notification within 24 hours of occurrence and a 14-day analysed reporting path. Rule 42 also contains recipient-, actor- and outcome-specific procedures with other anchor wording. [S06]

Production must represent a reporting obligation as:

```text
study applicability + rule/version + actor + event criterion
+ clock anchor + duration + recipients + delivery evidence + escalation owner
```

Capture occurrence, awareness and server receipt separately. Late entry must not reset the occurrence-based clock. Preserve reasons for delay. Distinguish clinical event handling from suspected drug reactions and spontaneous pharmacovigilance reports.

D0 implements two clearly labelled pathways:

| Pathway | Initial timer | Analysis timer | Interpretation |
|---|---|---|---|
| Synthetic study flagged NDCT applicable | Occurrence + 24h | Occurrence + 14d | Demonstrates investigator path only |
| Other synthetic studies | Occurrence + configured 24h | No universal deadline assigned | Internal demo SOP target, not a statutory assertion |

The app records the time an operator entered an external report reference. It does not independently prove when a report reached each recipient. A production safety module needs separate actual submission times, receipt files, recipient-level obligations and escalation; it must not mark “on time” merely because a button was pressed.

### Privacy and security

Use final DPDP instruments, not the January 2025 draft. Commencement is phased: the final rules state immediate provisions, a one-year group and an eighteen-month group. The later intervals have not elapsed as of 29 September 2026. The Gazette instruments are dated 13 November 2025 and carry 14 November electronic references; quote the relative commencement language when precise dates are unnecessary. [S08–S10]

Correct distinctions for the pitch:

- Health information warrants strong protection, but the DPDP Act does not reproduce every earlier “sensitive personal data” category as a distinct category.
- SDF status depends on government designation. A health-research platform is not automatically an SDF.
- DPDP does not contain a general GDPR Article 22-style prohibition on all solely automated significant decisions. Human oversight here is a clinical/product safety requirement; do not cite a nonexistent blanket DPDP rule.
- A research exemption is conditional, not blanket permission to ignore data protection.
- India-resident hosting is requested in the problem and relevant to government procurement/operations. DPDP alone should not be described as a universal localisation rule for all clinical data.
- Withdrawal of study participation, withdrawal of a processing permission, clinical-record retention and statutory audit retention are separate decisions.

CERT-In directions require reporting specified cyber incidents within six hours of noticing/being informed, and secure rolling 180-day ICT logs in India. That is a different reporting clock from SAE notification. Clinical records can require longer retention under their applicable framework; 180 days is not a universal deletion schedule. [S11]

## 6. Data integrity findings

ALCOA+ requires a governance system, not one cryptographic function. The MVP provides server times, explainable changes, atomic audit writes, an append-only interface and hash-chain verification. It does not provide independently immutable storage or validated electronic signatures. [S12]

Hash chains make changes visible relative to a trusted history. A database administrator could rewrite the whole chain or remove its tail. The pilot needs independent checkpoints, restricted database administration, protected archives, reliable time, restoration proof and record-review procedures.

The practical recommendation is a relational audit table plus independent retention. A permissioned blockchain adds governance and deployment burdens before proving a need for multiple mutually distrustful writers. It does not establish source-data truth, valid consent or clinical correctness.

## 7. Interoperability findings

FHIR is an exchange model. CDISC spans standardised collection, tabulation, analysis and metadata. They solve related but different problems. Semantic mapping must preserve study context, units, timing, terminology and derivation lineage. The Leroux paper explicitly examines these mapping challenges; the Gulden implementation provides a credible FHIR trial-registry precedent. Neither proves our app is interoperable with a hospital. [S16–S22, S25–S26]

The observed current ABDM guide is 6.5.0, based on FHIR R4. Its clinical artefacts use Composition-based profiles and DocumentBundle. A collection containing ResearchStudy and ResearchSubject is not, by itself, an ABDM clinical document or sandbox-approved integration. [S18]

The full submission path requires a study-specific annotated CRF, approved standards versions, controlled terminology, tabulation domains, validated derivations, the statistical analysis plan, ADaM, metadata and submission-format checks. D0 exports a useful mapping preview and linked research resources without claiming this full chain.

## 8. Competitive landscape

| Alternative | Established strength | Where Anvaya’s proposed scope fits | What not to claim |
|---|---|---|---|
| Spreadsheets and shared documents | Familiar and adaptable | Adds connected operational checks and traceability | Do not invent measured time/cost loss |
| REDCap | Research capture, user rights, audit, integrations | Can supply data to the Ayurveda oversight layer | REDCap does not lack audit or permissions |
| OpenClinica | EDC and trial-data operations; documented APIs | Partner integration where an institution already uses it | No verified universal plug-and-play FHIR claim |
| CTRI | Public registration and transparency | Track registration evidence and study updates | CTRI is not the internal CTMS and no write API is established here |
| Existing PV network and tools | National safety-reporting responsibilities | Link study operations to the institution’s PV process | This app does not replace NPvCC or national reporting infrastructure |

Vendor capability descriptions are based on vendor primary documents [S28–S29]. This is not an exhaustive procurement comparison. Pricing, enterprise licences and AIIA’s existing contracts are unknown; no fabricated cost comparison appears in the slides.

## 9. AI and analytics feasibility

| Candidate | Value | Evidence/data required | Decision |
|---|---|---|---|
| Explainable recruitment pace rule | High: directs operational attention | Start/end dates, target and enrolments | Implemented; called a rule, not AI |
| Safety deadline rule | High: makes due work visible | Applicability, clock anchor and reporting status | Implemented limited path |
| Recruitment forecast | Moderate; uncertainty matters | Enough site history, interruptions, seasonality | Later; backtest versus a simple baseline |
| MedDRA coding suggestions | Useful but regulated/licensed context | Licensed version, labelled narratives, coding expert review | Deferred; keep verbatim text and review status |
| LLM narrative summary | Potentially useful | Privacy review, approved deployment, factuality benchmark | Deferred; never replace source text |
| PRR/ROR/BCPNN signal screening | Potential PV use at proper scale | Suitable reporting database, comparator/background, deduplication and expert adjudication | Not validly demonstrated by tiny synthetic trial counts |
| Offline/voice AE capture | Potential access benefit | Connectivity interviews, language validation, secure sync | Later after confirming field need |

MagiCoder is a real research precedent for coding ADR narratives. No borrowed accuracy figure is presented as our result. Likewise, Bayesian shrinkage can address instability in signal estimates but cannot turn a tiny biased dataset into reliable causal evidence. There is no single universal minimum report count guaranteeing validity across all signal methods. [S23–S27]

## 10. Corrections to the supplied research plan

| Plan item | Research correction |
|---|---|
| WHO minimum dataset has 20 items | Current WHO page states 24, version 1.3.1 |
| IEC approval has a universal one-year validity cutoff | Track actual approval and institutional continuing-review rules |
| Clinical platform is a likely SDF, so treat as designated | Design strong controls; do not assert a designation without notification |
| DPDP prohibits all purely automated significant decisions | Do not import GDPR wording into the Indian Act |
| A single generic SAE deadline covers the workflow | Model applicability, actor, outcome, anchor and recipient |
| Hash chain equals immutable/ALCOA+-compliant ledger | It is one tamper-evidence control within a larger validated system |
| FHIR support implies ABDM support | ABDM requires its profiles, consent flows and onboarding |
| FHIR-to-SDTM conversion provides submission readiness | Mapping, terminology, SAP/ADaM and metadata validation are required |
| Old PV network counts are current | Label the source date or omit counts from the pitch |
| AI benchmarks can be inherited from papers | Evaluate the actual model/data/task; no accuracy claim for this demo |

## 11. Implementation and validation plan

**Tonight’s handoff:** local MVP, cited research, detailed requirements/design/personas/workflows, slide-ready copy and demo script. Use synthetic-only screenshots. Rehearse the enrolment failure and safety path before presentation.

**Pilot preparation, proposed 2–4 weeks:** interview role representatives; document authoritative systems and protocol variants; agree access and privacy basis; replace shared demo identity; implement document/version review and study activation; validate core workflows on synthetic or approved de-identified fixtures. Duration is an estimate conditional on stakeholder access.

**Integration/validation, proposed subsequent 4–8 weeks:** obtain partner sandboxes and dictionary rights; implement one connector; validate mappings; complete recipient-specific safety workflows and operational assurance. Do not promise ABDM certification or procurement approval within a fixed student sprint.

**Institutional evaluation:** compare source reconciliation, task completion, reporting timeliness, access denials, audit completeness, restoration and conformance. Review any time-saved claim against a recorded baseline, sample size and workflow definition.

## 12. Unresolved evidence

Actual AIIA study portfolio, licensed software stack, source EDC/HIS, SOPs, reporting recipients, consent templates, dictionary access, masking rules, procurement constraints and hosting contracts remain unverified. We have not interviewed staff, evaluated real clinical outcomes, trained a model or validated a production submission package.

These are explicit inputs for the next phase, not reasons to obscure what the present prototype can already demonstrate.
