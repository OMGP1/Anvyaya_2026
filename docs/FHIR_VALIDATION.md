# FHIR R4 validation evidence

**Run date: 30 September 2026. Result: 306 synthetic resources checked by the official HL7 Java validator against FHIR R4 4.0.1, with 0 errors, 0 fatal issues, 100 warnings and 100 informational issues.** The process exited with code 0. The final run used cached definitions with HTTP access and the terminology service disabled. These qualifications are part of the result.

The unmodified machine report is [validation/fhir-output.json](validation/fhir-output.json). The reproducible runner is [scripts/validate_fhir.py](../scripts/validate_fhir.py). This is external-validator evidence for the current export, beyond the application's own reference and resource checks.

## What was actually tested

The runner created a new SQLite database in a temporary directory, called `server.initialize()` to populate fictional demonstration records, then called `server.bundle(conn, 'admin')`. The application database was never opened. The export contained six `ResearchStudy`, 100 `Patient`, 100 `ResearchSubject` and 100 `Consent` resources in one collection `Bundle`. Generated XHTML narratives were included in all 306 resources.

The validator ran locally. The initial preparation downloaded public definition packages; it did not upload the bundle. The final run added `-no-http-access` and reused those packages. `-tx n/a` disabled terminology-server validation throughout. No real patient records, CTRI participant data, external clinical system credentials or ABDM sandbox connections were involved.

The tool was the [HL7-maintained FHIR validator](https://github.com/hapifhir/org.hl7.fhir.core), pinned to [release 6.10.4](https://github.com/hapifhir/org.hl7.fhir.core/releases/tag/6.10.4), Git identifier `1b90fb13f77b`, built `2026-09-04T05:45:41.468Z`. It ran on Homebrew OpenJDK 24.0.2, macOS arm64, with a 2 GB heap limit. The command-line options were confirmed from this downloaded version's `-help` output.

## Results and remaining messages

| Severity | Count | Meaning and follow-up |
|---|---:|---|
| Fatal | 0 | No fatal issue reported in this run. |
| Error | 0 | No error reported against the loaded base R4 definitions under this configuration. |
| Warning | 100 | Every synthetic `Consent.policyRule` is text-only; the validator recommends a code from the Consent PolicyRule value set. A real deployment needs an institution-reviewed policy mapping. No policy code was invented to silence this warning. |
| Information | 100 | The `Consent.category` binding could not be confirmed without a terminology service. Full category terminology validation remains outstanding. |

An initial run also reported 306 missing-narrative warnings. Human-readable narratives were added to the export, and the final run above confirmed that those warnings disappeared. R4 describes narratives as a best-practice safeguard for human interpretation. [R4 DomainResource constraints](https://hl7.org/fhir/R4/domainresource.html#invs)

The remaining policy warning reflects a semantic limitation of the demonstration. R4 binds `Consent.policyRule` to an extensible value set and requires a policy or policy rule. The current text records the synthetic nature of the consent; it does not establish a clinically reviewed, computable institutional policy. [R4 Consent definitions](https://hl7.org/fhir/R4/consent-definitions.html#Consent.policyRule)

## Reproduce the run

Run from the repository root. The JAR and package cache remain outside the repository; Java is required. The Python runner uses only the standard library.

```sh
curl -L --fail --output /tmp/anvaya-validator-6.10.4.jar \
  https://github.com/hapifhir/org.hl7.fhir.core/releases/download/6.10.4/validator_cli.jar

# First use: permits public definition-package downloads; terminology is disabled.
python3 scripts/validate_fhir.py \
  --jar /tmp/anvaya-validator-6.10.4.jar \
  --cache-dir /tmp/anvaya-fhir-validation-home

# Cached replay: disables HTTP(S) as well as the terminology service.
python3 scripts/validate_fhir.py \
  --jar /tmp/anvaya-validator-6.10.4.jar \
  --cache-dir /tmp/anvaya-fhir-validation-home \
  --offline
```

The runner checks the JAR SHA-256 before importing the app, uses a new temporary database for every run, and returns a nonzero exit status for validator failure or any error/fatal issue. It saves the raw OperationOutcome and prints counts and hashes. It does not convert warnings into errors or hide informational issues. Its final Java invocation has this form:

```sh
java -Duser.home=/tmp/anvaya-fhir-validation-home -Xmx2g \
  -jar /tmp/anvaya-validator-6.10.4.jar <temporary-bundle.json> \
  -version 4.0.1 -tx n/a \
  -txCache /tmp/anvaya-fhir-validation-home/tx-cache \
  -output <temporary-outcome.json> -no-http-access
```

An empty offline cache cannot reproduce the check: download definitions first. The generated study dates and timestamps depend on run time, so fresh input hashes change. The downloaded CLI can resolve newer dependency packages when a new cache is populated; compare the printed package versions with this run's inventory before treating results as identical.

## Recorded artifact fingerprints

| Artifact | SHA-256 |
|---|---|
| Official 6.10.4 JAR, 200,928,617 bytes | `1106b9d58f9e363e47bea7c4fc065841e5fc91fe9d062775c3bfdd212bd653cc` |
| Temporary synthetic input for final run | `a3370a2742ed9826037131451d153c54640d9050d545695386b946c0d07d2334` |
| Saved OperationOutcome, 287,076 bytes | `642cba13f9d6b608912602547b157aa1a848a7aadce6f684de0cbecd82755c65` |
| Validated `server.bundle` function source | `27e668a6205144ceb705a4b27d07e35ff106c5ca5270b285554e333ba185aee8` |

The SHA-256 pin records the exact downloaded artifact used here; independent release-signature verification was not performed.

Definition packages present in the isolated cache:

```text
hl7.fhir.r4.core#4.0.1
hl7.fhir.xver-extensions#0.1.0
hl7.terminology.r4#6.2.0
hl7.fhir.uv.extensions.r4#5.2.0
hl7.terminology#7.4.0
hl7.fhir.uv.extensions.r5#5.2.0
hl7.terminology.r5#7.1.0
hl7.fhir.uv.extensions#5.3.0
```

These are packages loaded by this CLI; their presence does not change the requested export validation version from R4 4.0.1.

## Claim boundary for slides and reviews

**Supported wording:** “Our synthetic FHIR R4 export was checked with the official HL7 validator: 306 resources, zero errors; consent-policy warnings and disabled terminology checks are documented.”

This result is not an HL7 certification, ABDM approval, terminology-complete validation, electronic-consent validation or evidence of live HIS/EDC integration. It covers this seeded export and this validator configuration. Other workflow states, recipient-specific requirements, clinical meaning and a real receiving-system exchange need separate checks. HL7 explicitly explains that validation tools check computable constraints and that static resource validation alone does not prove complete conformance. [FHIR validation scope and limitations](https://hl7.org/fhir/R4/validation.html)

No ABDM implementation guide was supplied with `-ig`; therefore no ABDM profile validation is claimed. That remains separate work against the required [ABDM FHIR implementation guide](https://nrces.in/ndhm/fhir/r4/).

All linked primary sources were accessed on 30 September 2026.
