# Master strategy: reviewed decisions and delivered increment

Updated 1 October 2026. Reviewed against the supplied **ANVAYA Master Strategy & Innovation Document**, the running code and official sources. **Built** means an implemented software workflow; **prototyped** means a running analytical method evaluated on synthetic data; **designed** means specifications and acceptance gates only. None of these labels establishes clinical validation or institutional approval.

## Delivered from the strategy

| Recommendation | Current result | Evidence and boundary |
|---|---|---|
| Visible configurable alerting | **Built:** Operations & alerts page, scoped inbox, displayed rules/owners, five editable thresholds | Recruitment pace, IEC expiry, query age, monitoring horizon and deviation age. Missing registration, safety clocks and fixed forecast thresholds are also visible. Inbox entries are derived from records, not stored acknowledgements or external notifications. |
| Site register | **Built:** primary and additional sites, recorded activation, site selection at enrolment | Study readiness and consent remain enforced. Study activation activates its primary site in the same transaction. Site targets are planning values, not independent enrolment caps. Site approval authenticity is not verified. |
| Monitoring visits | **Built:** schedule, monitor, scope, completion findings and audit history | Future visits cannot be completed. Completion is an operational record; it is not an electronic signature. |
| Protocol deviations | **Built:** study/site/optional participant linkage, category, owner, occurrence, corrective action and closure | Invalid study/site combinations, future occurrence dates and repeat closure are rejected. No automatic clinical severity or CAPA adequacy decision. |
| Data queries | **Built:** creation, ageing alerts, resolution and audit history | Uses existing query permissions and study assignments. |
| Enrolment forecast | **Prototyped:** study-level Gamma–Poisson forecast, target probability, nominal 90% count interval and trailing-rate comparison | Reproducible 300-study synthetic holdout evaluation; no site-hierarchical model or validated field performance. See below. |
| Batch-linked safety | **Built, narrower:** configured formulation/batch displayed beside study-level AE counts | Individual exposure, actual event-to-batch attribution and dictionary-coded event denominators are missing. No PRR/ROR or causal signal is calculated. |
| Pre-inspection report | **Built:** scoped aggregate checks and downloadable HTML | Current consent coverage, readiness, IEC expiry, pending document review, overdue safety steps/recipient follow-ups, monitoring, deviations, queries and audit status. Not a certificate; missing source uploads/authenticity are not established. |
| Preservation on upgrade | **Built:** additive tables and audited primary-site/default creation | Existing study, participant and safety payloads remain unchanged. Reinitialisation does not duplicate audit events or inject fictional monitoring/deviations into an existing database. |

Implementation: [study_operations.py](../study_operations.py), [operations.js](../public/operations.js). Reproduction and browser evidence: [VALIDATION.md](VALIDATION.md). The updated [presentation](PRESENTATION_CONTENT.md) describes these functions directly.

## Corrections to the supplied strategy

1. **FHIR validation and consent were already implemented.** The official HL7 validator run covers a 306-resource seeded research Bundle against base R4, with documented warnings and disabled terminology checks. Consent, withdrawal and amendment-triggered reconsent already work. Neither result establishes ABDM acceptance. [FHIR evidence](FHIR_VALIDATION.md)
2. **A study batch field is not an exposure record.** PRR compares proportions of reports for a specific product/event combination against comparator reports; it is not simply the fraction of enrolled participants with any event divided by another trial's fraction. Different protocols, surveillance intensity and populations also confound cross-trial comparisons. Keep the present display descriptive until actual exposure and coding data exist. [FDA data-mining white paper](https://www.fda.gov/science-research/data-mining/data-mining-fda-white-paper)
3. **EX needs participant treatment data.** A configured formulation alone cannot establish dose, route, dates, administration or lot received. Build reviewed exposure capture before deriving EX. Pin the applicable SDTM/SDTMIG and terminology versions, then reconcile required/expected variables, origins and derivations against the data. Define-XML describes that metadata; generating an XML file does not establish dataset validity. [CDISC SDTMIG](https://www.cdisc.org/standards/foundational/sdtmig/sdtmig-v3-3/html), [Define-XML](https://www.cdisc.org/standards/data-exchange/define-xml)
4. **CORE is a conformance tool, not a submission certificate.** Record dataset versions, selected rule sets, executable version and findings. Add Define-XML schema/semantic checks, terminology checks and recipient-specific review. A `--define-xml-path` option is not evidence that every Define-XML requirement was validated. [Official CORE CLI](https://github.com/cdisc-org/cdisc-rules-engine/blob/main/docs/cli-reference.md)
5. **TM2 existence is supported; mappings still need work.** WHO's February 2025 release announcement includes a module for Ayurveda and related systems. That does not make a specific NAMASTE-to-ICD mapping validated or a resource ABDM-conformant. Pin published code releases and rights; preserve local concepts and mapping provenance. Diagnosis classifications and MedDRA event terminology have different purposes. [WHO 2025 announcement](https://www.who.int/news/item/14-02-2025-who-releases-2025-update-to-the-international-classification-of-diseases-%28icd-11%29)
6. **Local inference is only one privacy control.** It does not establish DPDP compliance, correct permissions, retention, lawful purpose or safe model logging. An imported code must exist in the selected licensed release, a reviewer must decide, and the original narrative must remain available. The current importer is bounded at 2,000 terms: a full dictionary does not simply plug in unchanged. [Existing production analysis](PRODUCTION_GAP_ANALYSIS.md)
7. **Record hashes and approvals are not validated signatures.** An external checkpoint must be outside the database administrator's trust boundary, signed using protected keys, retained independently and actually compared during verification. Local copies of a chain head are insufficient to prove protection against a privileged rewrite.

## Forecast method and measured limitations

The prototype aggregates each study, not individual participants or sites. It uses up to 56 calendar days of recorded enrolments and a Gamma(shape=0.5, rate=0.5 days) prior. With `n` observed enrolments over `t` days, the posterior is `Gamma(0.5+n, 0.5+t)`. Integrating a future Poisson count over that posterior produces a negative-binomial distribution. The app reports `P(future count >= remaining target)` and its 5th/95th count percentiles. The projected completion date uses the posterior mean rate; it is not a confidence bound or a guaranteed deadline. Projections beyond ten years display an explicit limit, rather than a fabricated capped date.

This is a simplified operational prototype inspired by the Poisson–Gamma recruitment literature; it does not implement the cited authors' full multicentre models. Time-varying recruitment requires separate assessment. [Recruitment modelling research](https://arxiv.org/abs/2301.03710)

Run `.venv/bin/python scripts/evaluate_forecasts.py`. The reproducible evaluation uses seed 26047, 56 observed days and an independent 28-day future for each of 300 fictional studies. Future observations never enter the forecast input. Two scenarios each contain 150 studies:

| Synthetic scenario | Target Brier score (lower is better) | Future-count MAE | Trailing-rate MAE | Nominal 90% interval coverage |
|---|---:|---:|---:|---:|
| Constant rate | 0.1456 | 5.77 | 5.78 | 91.33% |
| Unseen 50% recruitment slowdown | 0.3117 | 17.57 | 17.63 | 24.00% |

The constant-rate result demonstrates expected model behaviour; the slowdown result demonstrates a serious limitation. The model offers no meaningful point-prediction advantage over the trailing rate in this simulation. Use it for transparent review, not automated staffing, recruitment or clinical decisions. Abrupt site pauses or changed eligibility can invalidate its intervals. The interface states the constant-rate assumption.

An earlier diagnostic found excessive shrinkage from a Gamma(1,14) prior. We weakened the prior before running the independent evaluation seed. Both outputs are retained: [initial diagnostic](validation/forecast-prior-diagnostic.json), [current evaluation](validation/forecast-evaluation.json). These are simulation results, not real clinical validation or an accuracy percentage.

## Remaining production and innovation work

| Workstream | Status | Concrete next acceptance gate |
|---|---|---|
| Public cloud URL | **Deployment package built; public service outstanding** | Provision an authorised host and domain with persistent storage, deploy pinned image, configure HTTPS/named access, test signed-out reachability and restart/restore. No hosting account, VM, DNS ownership or public URL is supplied. Do not claim an Indian region or certification from configuration alone. |
| Local NLP/LLM reranker | **Designed** | Retain lexical baseline; retrieve from a versioned authorised dictionary; local embedding/reranker returns only candidate IDs or abstention; validate membership; log model/prompt/version and reviewer accept/override. Measure top-1/top-5, abstention and wrong suggestions on separately authored Hindi/English/transliterated synthetic cases before a comparative claim. No model has been installed or benchmarked. |
| Ayush FHIR extension pack | **Designed** | Publish owned canonical URLs, CodeSystem/ValueSet and StructureDefinition artifacts; represent assessments with instrument/date/assessor and products/exposure separately; validate example resources against the actual profiles. Do not assert NAMASTE/TM2 equivalence without reviewed mappings. |
| DM/AE/EX + Define-XML | **Designed; DM/AE previews built** | Complete protocol-specific source fields and exposure records, reviewed mappings and terminology; generate metadata from the same mapping; run schema/conformance/recipient checks and retain findings. ADaM also needs an approved statistical analysis plan and derivation traceability. |
| Independent audit checkpoint | **Designed; local chain verification built** | Sign sequence/head/time under separately controlled keys, retain in independently administered storage with enforced retention, and demonstrate verification against a rewritten/truncated database. Include missing/stale checkpoint handling and key rotation. |
| ODM-XML import | **Designed; CSV staging built** | Support an explicit ODM version and bounded subset; reject DTD/entities, oversized input, ambiguous subject keys and unsupported repeats; preserve StudyOID/MetaDataVersionOID/SubjectKey/ItemOID, source hash and mapping version; route reviewed rows through existing commands. Do not flatten repeating forms silently. |
| Electronic signature | **Designed; named independent review built** | Reauthenticate the named reviewer, capture meaning and exact record/version hash, enforce expiry/replay guards and immutable linkage, validate identity/signature SOPs. Do not call password confirmation Part 11 compliance. |
| Privacy register | **Designed; access/consent controls built** | Institution approves purpose, notices, record-class retention, request restrictions/holds, incident ownership and breach handling. Avoid automatic erasure of retained essential research records. Applicability and commencement remain subject to institutional legal review. |
| DSMB workflow / dropout model | **Aggregate leadership view built; specialist functions designed** | Agree masking, event definitions, denominators and review responsibilities. Censoring, follow-up and cohort quality must be established before survival/dropout modelling; never claim a trained predictor from current visit counters. |

Detailed EDC/HIS authentication, staging/reconciliation and the separate ABDM consent/profile pathway already appear in [PRODUCTION_GAP_ANALYSIS.md](PRODUCTION_GAP_ANALYSIS.md) and [TRD.md](TRD.md). Production hosting and incident controls are specified in [DEPLOYMENT.md](DEPLOYMENT.md). No six- or eighteen-month delivery commitment is inferred from the supplied strategy.

## Demonstration order

1. Show a blocked enrolment and the prerequisite causing it.
2. Open Operations & alerts: explain the rule, threshold and owning role behind an alert.
3. Create/activate a site, complete a scheduled monitoring visit, record/close a deviation and open/resolve a query.
4. Show the forecast, trailing baseline and uncertainty. State the observed slowdown limitation if asked about validity.
5. Show formulation/batch **context**, explicitly distinguishing it from confirmed participant exposure.
6. Filter one study, generate its pre-inspection report, download HTML and verify the audit chain.
7. Use the already implemented named evidence review, import and coding workflows for deeper questions. Describe remaining interfaces and licensed components using the acceptance gates above.
