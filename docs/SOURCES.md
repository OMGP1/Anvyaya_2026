# Source register

Research snapshot: **29–30 September 2026**. Primary sources are preferred. This is a product-research evidence register, not an institutional legal determination. Links support the stated facts; proposed software designs and pilot targets are our recommendations. No AIIA staff interviews or access to actual participant records took place.

## Problem, institutional context and trial conduct

| ID | Primary source | Verified relevance | Limit on use |
|---|---|---|---|
| S01 | [SIH 2026 problem statements](https://sih.gov.in/sih2026PS), search **26046** | Official AIIA CTMS problem, Ministry of Ayush, software, MedTech / BioTech / HealthTech. Requests staged implementation, role-based oversight, interoperability, safety and integrity. | Describes the requested solution; it is not proof of measured current inefficiency or actual AIIA trial counts. |
| S02 | [AIIA pharmacovigilance page](https://archive.aiia.gov.in/pharmacovigilance/) | AIIA’s national coordinating role for ASU&H pharmacovigilance and the three-tier network. | Archived page gives five intermediary and 99 peripheral centres. Do not call those verified September 2026 counts. |
| S03 | [CTRI FAQ](https://ctri.nic.in/Clinicaltrials/faq.php) and [CTRI home](https://ctri.nic.in/) | Prospective registration before first enrolment; CTRI accepts traditional medicine and observational studies. A REF application number is not completed registration. | No public write API has been established by this research. Do not promise automated CTRI filing. |
| S04 | [GCP-ASU guidelines, March 2013](https://ccras.nic.in/wp-content/uploads/2025/09/3.-ASU-GCP-Guidelines.pdf) | Official ASU clinical-trial conduct guidance. Grounds protocol, product quality, consent, records and oversight requirements. | Application needs study-specific institutional interpretation; software alone cannot certify compliance. |
| S05 | [ICMR ethical guidelines index](https://ethics.ncdirindia.org/icmr_ethical_guidelines.aspx) and [2017 guidelines PDF](https://ethics.ncdirindia.org/asset/pdf/ICMR_National_Ethical_Guidelines.pdf) | Ethics review and informed-consent framework. Index also lists 2025 integrative-medicine guidance and 2026 multicentre single-review guidance. | Newer guidance must be reviewed when selecting a real study; 2017 is not the only potentially relevant document. |
| S06 | [CDSCO NDCT rules PDF](https://cdsco.gov.in/opencms/resources/UploadCDSCOWeb/2022/new_DC_rules/23NEW%20DRUGS%20AND%20CLINICAL%20TRIALS%20RULES%2C%202019.pdf) and [amendments index](https://www.cdsco.gov.in/opencms/opencms/en/Acts-and-rules/New-Drugs/) | Rule 25(v): registration before first enrolment. Rule 42(1): initial SAE report within 24 hours of occurrence. Rule 25(x) / investigator duties: analysed report within 14 days of occurrence. | Rule 42 has actor- and outcome-specific branches, including knowledge/report receipt anchors. The prototype is not a complete executable NDCT rulebook. Check later amendments before implementation. |
| S07 | [WHO Trial Registration Data Set](https://www.who.int/tools/clinical-trials-registry-platform/network/who-data-set) | Current page identifies version 1.3.1 and **24 items**, including ethics review, completion, results and IPD-sharing statement. | Corrects the plan’s historical 20-item description. CTRI has its own fields and process. |

## Privacy, integrity and operations

| ID | Primary source | Verified relevance | Limit on use |
|---|---|---|---|
| S08 | [DPDP Act 2023](https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf) | Personal-data framework; Section 10 SDF designation; Section 16 transfer provisions; Section 17 includes a conditional research exemption. | Clinical research is not automatically exempt, automatically an SDF, or automatically subject to a universal data-localisation duty under this Act. |
| S09 | [Act commencement notification, G.S.R. 843(E)](https://www.meity.gov.in/static/uploads/2025/11/c56ceae6c383460ca69577428d36828b.pdf) | Notification dated 13 November 2025; commencement occurs in immediate, one-year and eighteen-month groups. | Gazette cover and upload references include different dates. Use the instrument’s relative periods, not an unqualified “fully effective in 2025” statement. |
| S10 | [Final DPDP Rules 2025, G.S.R. 846(E)](https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf) | Rule 1 specifies phased commencement. Includes notice, security, breach, rights and designated-SDF requirements. Rule 13 ties annual assessment/audit duties to notification as an SDF. | At this research date, later commencement tranches have not elapsed. Confirm corrigenda and institution-specific applicability. These are final rules, not the January 2025 draft. |
| S11 | [CERT-In directions, 28 April 2022](https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf) | Clause ii: listed cyber incidents within six hours of noticing/being informed. Clause iv: rolling 180-day ICT logs within India. Clause i: clock synchronisation. | Cyber incident clocks differ from clinical SAE clocks. 180 days is not the universal retention period for trial source data or essential documents. Official PDF was downloaded and inspected locally after browser retrieval timed out. |
| S12 | [MHRA GxP data integrity guidance](https://www.gov.uk/government/publications/guidance-on-gxp-data-integrity) | Primary international data-integrity reference for auditability and ALCOA concepts. | UK guidance is used as a design reference, not presented as Indian legislation. Hashing alone does not implement every ALCOA+ attribute. |
| S13 | [ISO/IEC 27001:2022](https://www.iso.org/standard/27001) | Information-security management system standard with scoped organisational controls. | A certified cloud supplier does not confer certification on this application. No certification is claimed. |
| S14 | [NICSI cloud](https://nicsi.nic.in/nicsi/nicsi-cloud/) and [vendor listing](https://nicsi.nic.in/nicsi/empanelled-vendors/?service=Cloud+%2F+Data+Center+Services) | Government procurement/hosting ecosystem and empanelled suppliers. | Verify exact offering, facility, validity and contract before selecting a provider. An India region alone is not procurement approval. |
| S15 | [AWS MeitY page](https://aws.amazon.com/compliance/MeitY/) and [Microsoft MeitY page](https://learn.microsoft.com/en-us/compliance/regulatory/offering-meity-india) | Provider-authored descriptions of MeitY offerings and assurance. | Supplier statements need comparison with current official empanelment and customer contracts; no price or compliance guarantee inferred. |

## Interoperability and terminology

| ID | Primary source | Verified relevance | Limit on use |
|---|---|---|---|
| S16 | [FHIR R4 ResearchStudy](https://hl7.org/fhir/R4/researchstudy.html) | Research metadata and status resource. | Use R4 structures, not R5 field assumptions. Core FHIR research resources are not ABDM clinical documents. |
| S17 | [FHIR R4 ResearchSubject](https://hl7.org/fhir/R4/researchsubject.html), [Consent](https://hl7.org/fhir/R4/consent.html), [Bundle](https://hl7.org/fhir/R4/bundle.html) | Subject-study linkage, consent representation and bundle structure. | Structural prototype checks are not equivalent to official profile/terminology conformance testing. |
| S18 | [NRCeS FHIR implementation guide for ABDM](https://nrces.in/ndhm/fhir/r4/) | Current published banner observed: **6.5.0, active**, based on FHIR R4. Composition-based clinical artefacts and DocumentBundle. | Not evidence of this prototype’s ABDM integration. HIP/HIU consent exchange and sandbox onboarding remain separate work. |
| S19 | [CDASH 2.1 page](https://www.cdisc.org/standards/foundational/cdash/cdash-2-1) | Standardised collection and traceability into SDTM variables. | Version is a researched reference, not an assertion that this prototype is CDASH-conformant. |
| S20 | [CDISC SDTM](https://www.cdisc.org/standards/foundational/sdtm) | Standard organisation and representation of study tabulation data. | CSV column names alone do not prove SDTM conformity or submission readiness. |
| S21 | [CDISC ADaM](https://www.cdisc.org/standards/foundational/adam) | Analysis datasets and traceability to tabulation/results. | ADaM requires a statistical analysis plan and reviewed derivations. No analysis-ready package is implemented. |
| S22 | [CDISC Define-XML](https://www.cdisc.org/standards/data-exchange/define-xml) | Machine-readable dataset metadata used with SDTM and ADaM. | XML that merely lists columns is not a valid Define-XML submission. Version pinning and schema validation are future acceptance gates. |
| S23 | [MedDRA terms](https://tools.meddra.org/wbb/eula.htm), [2026 access fact sheet](https://files.meddra.org/www/Website%20Files/Fact%20Sheets/meddra_factsheet1_accessing_meddra-10%20May%202026.pdf), [data-sharing statement](https://files.meddra.org/www/Website%20Files/Welcome%20Pages/001418%20Statement%20on%20MedDRA%20Data%20Sharing.pdf) | Terminology and tools have subscription/licensing conditions. | Do not scrape and bundle a dictionary or upload licensed terminology to an AI service without reviewing the applicable terms. The updated demo can review codes from fictional supplied terms; it ships no licensed dictionary. |
| S24 | [UMC vigiMethods](https://edit.who-umc.org/science/vigimethods/) | Statistical signal work and data-quality/duplicate-management methods. | Not a justification to infer causality or validate a detector on tiny synthetic counts. WHODrug dictionary access is a separate dependency. |

## Research precedents and alternatives

| ID | Primary source | Finding used | Appropriate interpretation |
|---|---|---|---|
| S25 | [Leroux, Metke-Jimenez & Lawley, 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5606031/), DOI 10.1186/s13326-017-0148-7 | Investigates ODM/FHIR mappings and semantic/context limitations. | Supports explicit mapping and provenance. Does not establish an automatic lossless FHIR-to-SDTM conversion. |
| S26 | [Gulden et al., 2021, JMIR Medical Informatics](https://pmc.ncbi.nlm.nih.gov/articles/PMC7837997/), e20470 | Implemented FHIR-based trial-registry architecture using ResearchStudy and REST exchange. | Valid architecture precedent. Their system and deployment are not our measured performance baseline. |
| S27 | [Combi et al., MagiCoder, arXiv:1612.03762](https://arxiv.org/abs/1612.03762) | Existing work on encoding ADR narratives to MedDRA. | Existence/method relevance verified; no numerical accuracy benchmark is claimed for our app or extracted without a matched evaluation. |
| S28 | [REDCap technical overview](https://projectredcap.org/wp-content/uploads/2025/01/REDCapTechnicalOverview.pdf), [technical requirements](https://projectredcap.org/software/requirements/) | Established data capture, user rights, logs and integration capabilities. Explicitly distinguishes software from study-process validation. | Do not claim competitors lack RBAC or audit trails. Integration may be preferable to replacing EDC. |
| S29 | [OpenClinica solutions](https://www.openclinica.com/solutions/) and [REST documentation](https://docs.openclinica.com/3-1-technical-documents/rest-api-specifications/) | Established EDC and documented integration surface. | REST page is version-specific. Inspect the actual customer edition and current API before committing to a connector. |
| S30 | [ICH E6(R3), Principles and Annex 1, January 2025](https://database.ich.org/sites/default/files/ICH_E6%28R3%29_Step4_FinalGuideline_2025_0106.pdf) | International GCP reference relevant to contemporary system/data governance. | Adoption and applicable Indian requirements must be assessed; this is not a replacement for GCP-ASU or a claim that the referenced document covers every later annex. |

## Evidence discipline for the presentation

- Use **“the SIH problem statement describes…”** for spreadsheet fragmentation and reporting risk. No local time-and-motion study was done.
- Use **“the prototype demonstrates…”** for tested software behaviours.
- Use **“we propose to measure…”** for time saved, reporting timeliness, usability and adoption.
- Use **“planned, subject to access and validation”** for external integrations and certified operations.
- Treat Prakriti, batch traceability and procedure logs as protocol-defined data, not proof of efficacy or a validated diagnostic model.
- Recheck regulations, profiles and supplier status before a real deployment. These documents capture a dated research snapshot.

## Production-gap research additions — 30 September 2026

The linked [production gap analysis](PRODUCTION_GAP_ANALYSIS.md) places each source beside its specific interpretation, implementation delta and acceptance evidence. These additions do not renumber the earlier register or the presentation’s separate reference labels.

- [CDISC SDTMIG 3.4](https://www.cdisc.org/standards/foundational/sdtmig/sdtmig-v3-4), [controlled terminology](https://www.cdisc.org/standards/terminology/controlled-terminology) and [CORE](https://www.cdisc.org/core): compatible versions, governed terminology and rules checks.
- [FDA Study Data Technical Conformance Guide](https://www.fda.gov/media/153632/download): concrete XPORT and submission examples; not automatically binding on Indian Ayurveda research.
- [HL7 SMART Backend Services](https://hl7.org/fhir/smart-app-launch/backend-services.html) and [OAuth 2.0 RFC 6749](https://www.rfc-editor.org/rfc/rfc6749): partner-supported authentication design, not evidence of a connected partner or research-use consent.
- [MedDRA support documentation](https://www.meddra.org/how-to-use/support-documentation) and [UMC WHODrug Global](https://who-umc.org/whodrug/whodrug-global/what-is-whodrug-global/): distinct terminology purposes, rights and human coding governance.
- [Waitress documentation](https://docs.pylonsproject.org/projects/waitress/en/stable/) and [Caddy reverse proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy): delivered serving configuration; public DNS/TLS and institutional security acceptance remain separate.
- [Official HL7 validator release 6.10.4](https://github.com/hapifhir/org.hl7.fhir.core/releases/tag/6.10.4): the pinned tool used for our [FHIR validation evidence](FHIR_VALIDATION.md), including its unresolved warnings and disabled terminology checks.
