# Validation evidence

**Updated 1 October 2026. Result: 69 automated test methods and three Chrome workflows pass.** The Operations increment adds ten regression methods and a browser workflow to the earlier account/evidence/import/safety checks. Every test uses isolated synthetic storage; the main demonstration database is preserved. Container and official FHIR results below retain their original scope and date.

## Reproduce the functional checks

```bash
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/python tests/run_checks.py --browser
```

The browser tests require installed Google Chrome. Checks start local listeners; an environment that blocks loopback needs an appropriate execution permission. The suite prints individual failures and returns a nonzero status on failure.

| Suite | Passed methods | What the checks establish |
|---|---:|---|
| `test_api.py` | 15 | Authentication/CSRF/origin checks, study scope, enrolment and readiness, stale revisions, activation, consent/withdrawal, visits, safety clocks, exports, persistence and audit tamper detection |
| `test_accounts.py` | 11 | Named provisioning, password redaction, forced password replacement, account-specific scopes, disable/reset/revoke, last-admin guards, attribution, login-attempt budget and concurrent read/revocation ordering |
| `test_documents.py` | 7 | Named upload, file size/type/path checks, immutable versions, independent review, amendments, stale approval, reconsent and preserved source history |
| `test_exchange.py` | 11 | Mapping/CSV validation, exact source hashing, row findings, idempotent retries, changed-source conflicts, atomic rollback, readiness/consent rechecks, scope, formula-safe provenance and local FHIR checks |
| `test_safety_workflow.py` | 7 | Dictionary release validation, supplied-code lookup, lexical candidates/abstention, named review, preserved narrative/history, recipient scope, chronology and duplicate-action guards |
| `test_study_operations.py` | 10 | Site activation/enrolment, monitoring chronology, deviation linkage/CAPA, query creation/alerts, scoped aggregates, HTML report data, idempotent migration preservation, descriptive batch counts and forecast mathematics/holdout exclusion |
| `test_ops.py` | 5 | Online backup including WAL, verified restore to a new path, no overwrite, restrictive permissions and rejection of corrupted/audit-tampered copies |
| `test_runtime.py` | 3 | Same handlers under Waitress WSGI: assets, health/security headers, authenticated mutations, scope, exports, cross-origin rejection and oversized request rejection |
| **Total** | **69** | Multiple assertions per method; no percentage coverage claim |

## Browser evidence

`test_browser.py` completes desktop navigation, rejected/valid enrolment, SAE capture, JSON download, draft creation, setup, readiness, activation, reload, independent protocol/consent versions, audit verification, read-only regulator behaviour and mobile layout.

`test_browser_extended.py` creates named accounts through the UI, changes initial passwords, uploads evidence, rejects self-review, independently approves documents, submits/applies an amendment, records reconsent, inspects history, previews/commits a synthetic import, checks FHIR references, imports fictional terms, confirms reviewed coding and records recipient escalation/dispatch/receipt. Desktop and 390-pixel mobile views are checked. Neither workflow reports JavaScript page errors.

Screenshots are saved in `docs/screenshots/`. They show temporary test records, so their new accounts, amendment and coding decisions are not added to the main demonstration portfolio. Human visual inspection covered the document register, coding dialog and mobile integration view. Native table scrolling is used on small screens.

## Official FHIR validation

The export builder is unchanged by the Operations increment. The following records the 30 September validation run; no additional profile or terminology acceptance is inferred.

HL7 Java validator **6.10.4**, base **R4 4.0.1**, checked a fresh synthetic export containing **306 resources**. The final run exited 0 with **0 errors, 0 fatal issues, 100 warnings and 100 information messages**. Generated XHTML narratives removed the earlier missing-narrative warnings.

The remaining warnings concern text-only `Consent.policyRule`; the informational messages concern terminology bindings because `-tx n/a` disables the terminology service. The final cached replay also used `-no-http-access`. These limits are part of the result. This does not demonstrate ABDM profile/sandbox acceptance or a fully validated terminology/submission package.

See [FHIR_VALIDATION.md](FHIR_VALIDATION.md), [raw OperationOutcome](validation/fhir-output.json) and [reproducible runner](../scripts/validate_fhir.py).

## Deployment and recovery evidence

The container/Compose/Caddy checks in this list were performed on 30 September. New operations code is included in the Docker build context; current runtime checks exercise it through the same handlers. Additional container evidence, when run, is recorded separately.

- Docker Desktop built `anvaya-ctms:verified` successfully using Python 3.12 and Waitress 3.0.2.
- A temporary container ran with a read-only root filesystem, ephemeral synthetic database, non-root user, dropped capabilities and loopback-only port 18046. Health, login, seeded record count, FHIR reference checks and audit verification passed.
- `docker compose --env-file .env.example config --quiet` passed.
- Caddy's `validate` command accepted the HTTPS proxy configuration. This validates configuration, not public certificate issuance or DNS reachability.
- A real local database backup was created before upgrading the service; SQLite integrity and all 14 pre-upgrade audit entries verified. No existing database was overwritten.
- The upgraded local service uses `http://127.0.0.1:8046`. A public hosting account, DNS and public access proof remain outstanding.

The configured proxy address is explicitly trusted for forwarded client identity; the application listener remains private in Compose. A container image and TLS configuration are not evidence of institutional security acceptance, encrypted host storage, availability or compliance certification.

## Review findings resolved

1. A GET could previously validate a named session, release the lock, and read records after a concurrent revocation committed. Session validation and scoped read now share the same lock; a concurrent regression check confirms ordering and subsequent denial.
2. A successful unrelated login previously reset the IP failure budget. Successful login no longer clears those failures; account-level and IP failure windows are checked, and a regression test preserves the remaining budget.
3. Explicitly malformed empty mappings were previously interpreted as defaults. Only an omitted mapping selects defaults; malformed provided values are rejected.
4. Source-text hashing now uses the exact received CSV, including its final newline, instead of hashing trimmed text.
5. Navigation buttons have stable accessible labels independent of live count badges. Mobile screenshots disable transition motion to capture a settled layout.
6. Earlier verification also fixed stale browser responses across role switches, cancelled post-withdrawal visits in KPI denominators, SQLite connection cleanup and incorrect sex-to-FHIR-gender assumptions.

## Boundaries

These checks establish the documented software behaviours on synthetic records. They are not clinical-system validation, a penetration-test certificate, a comprehensive accessibility review or a workload/availability benchmark. No measured clinical benefit, trained-model accuracy, licensed terminology correctness, full SDTM/ADaM/Define-XML conformity, real EDC/HIS/CTRI integration, automatic regulatory delivery, validated electronic signature or approved institutional cloud is claimed.

## Operations and forecast evidence — 1 October

`test_browser_operations.py` passes site creation/activation, monitoring planning/completion, deviation capture/CAPA closure, query creation/resolution, threshold editing, scoped pre-inspection HTML download and mobile containment without JavaScript errors. Screenshots: [desktop](screenshots/11-operations-alerts.png), [mobile](screenshots/12-operations-mobile.png). Download checks verify study scope and absence of session credentials.

The migration test compares original study, participant and event rows byte-for-byte, checks that restarting an existing database does not inject monitoring/deviation examples, and verifies unchanged audit head on a second initialisation. Historical participant payloads are preserved; legacy records resolve to the explicit primary site when needed.

The local service was backed up to `backups/pre-operations-upgrade-20261001.sqlite` before restart. Direct comparison after migration found zero changed study, participant or event payloads, six primary sites and a valid 33-entry audit chain (26 entries before migration). Backup/database files remain excluded from publication.

The updated Docker image `anvaya-ctms:operations-verified` built successfully. A temporary container with a read-only root, ephemeral data directory, non-root user and dropped capabilities passed login, six-site/four-forecast snapshot, Operations asset and scoped inspection/audit checks, then was removed. This confirms the updated package runs; it does not establish public hosting or institutional acceptance.

The synthetic forecast evaluation contains 300 studies with a 56-day observation period and separate 28-day holdout. Constant-rate interval coverage is 91.33%; an unforeseen 50% slowdown reduces coverage to 24%. Full probability/count errors, prior revision and baseline results are in [MASTER_STRATEGY_REVIEW.md](MASTER_STRATEGY_REVIEW.md), [current JSON](validation/forecast-evaluation.json) and [retained diagnostic](validation/forecast-prior-diagnostic.json). These results demonstrate assumptions and failure modes, not validated recruitment performance.

The exact production acceptance work is documented in [PRODUCTION_GAP_ANALYSIS.md](PRODUCTION_GAP_ANALYSIS.md) and [DEPLOYMENT.md](DEPLOYMENT.md).
