# Anvaya — AIIA clinical-trial workspace

Working synthetic-data MVP and detailed research for **SIH 2026, problem statement 26046**. Updated 1 October 2026. Product name is provisional. No PowerPoint or PDF was generated; presentation content is editable Markdown.

## Presentation and research

1. [Slide-ready content and speaker notes](docs/PRESENTATION_CONTENT.md).
2. [Five-minute demo and 22 judge questions](docs/DEMO_AND_JUDGE_QA.md).
3. [Research findings and corrections to the supplied plan](docs/RESEARCH_FINDINGS.md).
4. [Five production gaps: clinical rationale, SDTM, cloud, EDC and coding](docs/PRODUCTION_GAP_ANALYSIS.md).
5. [Primary-source register](docs/SOURCES.md).
6. [Master strategy review, delivered operations and measured forecast limits](docs/MASTER_STRATEGY_REVIEW.md).

## Run the working prototype

```bash
cd /Users/om/Projects/Sih_2026_winning_project_2
python3 server.py --port 8046
```

Open **http://127.0.0.1:8046**. Choose a role. Shared demonstration password: **Demo#26046**.

For a fresh GitHub checkout, open a terminal in the repository folder and run `python3 server.py --port 8046`. No existing database is needed: the app creates its synthetic dataset on first launch.

Python 3.10+ and a modern browser are enough. The local listener needs no runtime packages, remote API account, CDN or downloaded fonts. The deployment container uses pinned Waitress 3.0.2. Records persist in `data/ctms.sqlite`. Stop with Ctrl+C. Restarting requires login again and preserves saved records.

Use a different database for a fresh rehearsal without deleting your work:

```bash
CTMS_DB=data/rehearsal.sqlite python3 server.py --port 8047
```

The database is seeded only when empty. A fresh dataset has six studies, 100 participants, 200 visits, five adverse-event records and 12 data queries. Counts change when you operate the demo. Dates are relative to initialisation.

## What works

- Scoped portfolio, study details, derived KPIs, filters and search.
- Eight optional demo roles plus named accounts, study assignments, password changes/resets, account disable and session revocation.
- Versioned document uploads, independent review, active-study amendments and preserved reconsent history.
- Mapped synthetic CSV intake with preview, row errors, duplicate protection, source provenance and transactional workflow checks.
- Draft study creation, editable setup, six readiness checks and audited recruitment activation.
- Separate protocol/consent versions, stale-edit protection and consent-checked participant enrolment.
- Registration, IEC validity, recruiting-state, capacity and current-consent gates.
- Consent withdrawal, cancellation of future visits, visit completion and query resolution.
- AE/SAE capture with occurrence/awareness/entry timestamps and separate seriousness/severity.
- Study-specific initial/analysis clocks, assigned recipient obligations, recorded external dispatch/receipt and escalation.
- Versioned terminology-package import, lexical suggestions and named reviewer approval; fictional demo terms, no bundled licensed dictionary.
- Configurable operational alerts.
- Site register/activation, site-aware enrolment, monitoring visits/findings, deviations/corrective actions and query creation.
- Operations alert inbox, rule thresholds and scoped HTML pre-inspection summaries.
- Study-level enrolment forecast, nominal count uncertainty and trailing baseline, with a reproducible 300-study synthetic evaluation.
- Descriptive study safety counts beside configured formulation/batch context; individual exposure is unverified.
- Attributable change history, append-only audit triggers and SHA-256 chain verification.
- FHIR R4 research JSON, local reference checks, DM/AE mapping-preview CSV and provenance downloads.
- Verified backup/restore CLI, Waitress WSGI runtime and tested Docker/HTTPS configuration.

## Detailed deliverables

| Document | Contents |
|---|---|
| [PRD](docs/PRD.md) | Problem, outcomes, release scope, user stories, business rules and acceptance |
| [TRD](docs/TRD.md) | Architecture, storage, APIs, security, concurrency, audit and deployment requirements |
| [Design specification](docs/DESIGN.md) | Screens, tokens, components, interaction states, responsive/accessibility requirements |
| [User personas](docs/USER_PERSONAS.md) | Eight roles, future DSMB, permission matrix, scenarios and discovery questions |
| [Workflows](docs/WORKFLOWS.md) | Detailed current/future flows, decisions, exceptions and Mermaid diagrams |
| [Research findings](docs/RESEARCH_FINDINGS.md) | Domain, regulation, alternatives, AI feasibility, corrections and open evidence |
| [Sources](docs/SOURCES.md) | Thirty source groups with direct links and claim boundaries |
| [Regulatory traceability CSV](docs/REGULATORY_TRACEABILITY.csv) | Requirement-to-design-to-proof mapping and remaining production gaps |
| [KPI register CSV](docs/KPI_REGISTER.csv) | Formulas, denominators, owners, thresholds and limitations |
| [Interoperability specification](docs/INTEROPERABILITY.md) | Implemented FHIR/CSV fields and proposed partner/submission validation |
| [Presentation content](docs/PRESENTATION_CONTENT.md) | Six suggested slides, speaker notes, references and backup material |
| [Demo and judge Q&A](docs/DEMO_AND_JUDGE_QA.md) | Rehearsal path, recovery steps and defensible answers |
| [Validation](docs/VALIDATION.md) | Actual checks, results and limitations |
| [Website upgrade steps](docs/WEBSITE_UPGRADE_STEPS.md) | Completed stage, detailed walkthrough, verification and ordered follow-up work |
| [Production gap analysis](docs/PRODUCTION_GAP_ANALYSIS.md) | Clinical rationale and exact institutional integration/acceptance requirements |
| [Deployment and recovery](docs/DEPLOYMENT.md) | Named access, container/HTTPS setup, backup, restore and release controls |
| [Graphify notes](docs/GRAPHIFY_NOTES.md) | Extraction scope, graph findings, benchmark and query caveats |

New screens: [readiness](docs/screenshots/05-study-readiness.png), [accounts](docs/screenshots/06-access-management.png), [documents](docs/screenshots/07-documents-amendments.png), [integration](docs/screenshots/08-integration-evidence.png), [coding](docs/screenshots/10-coding-followup.png).

Screenshots: [overview](docs/screenshots/02-overview.png), [safety](docs/screenshots/03-safety.png), [mobile](docs/screenshots/04-mobile.png).

## Verification

The complete suite uses isolated databases and installed Google Chrome:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/python tests/run_checks.py --browser
```

Verified: **69 test methods and three browser workflows pass**. See [VALIDATION.md](docs/VALIDATION.md) for dated runtime/container evidence and external standards boundaries. Tests open loopback ports and preserve the main database. Reproduce the synthetic forecast evaluation with `.venv/bin/python scripts/evaluate_forecasts.py`; both stable-rate and slowdown results are reported.

## Demonstration boundaries

All records and registry references are fictional. Named accounts provide local attribution; neither they nor shared demo roles verify a person’s professional authority or delegation. This installation has not been approved to hold actual participant records; use synthetic data. The app has not been deployed on a compliant cloud or certified against GCP, ISO or DPDP.

No live CTRI/ABDM/EDC/HIS connection, licensed dictionary, validated electronic signature, randomisation engine, full CDISC submission package, autonomous medical decision or regulatory message delivery is claimed. External reporting controls record metadata only. See the PRD and research pack for the staged production path.

## Deployment and recovery

The Docker image uses Waitress. `compose.yaml` adds Caddy HTTPS, private application networking, named-access defaults and persistent storage. Build, container smoke tests and configuration validation have been exercised; public hosting and DNS are still required.

Follow [DEPLOYMENT.md](docs/DEPLOYMENT.md) for exact commands and [WEBSITE_UPGRADE_STEPS.md](docs/WEBSITE_UPGRADE_STEPS.md) for the complete walkthrough. `ops.py` creates verified backup and restore copies without overwriting existing databases.

GitHub link supplied by the team: [OMGP1/Anvyaya_2026](https://github.com/OMGP1/Anvyaya_2026). A public UI URL has not yet been provisioned. Local updates do not imply a GitHub push or public deployment.
