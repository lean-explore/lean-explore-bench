# Search telemetry: privacy and legal assessment

Prepared on 31 October 2026 from research conducted on 30 October 2026.

LeanExplore can collect more useful evidence about search quality without building a history of each user's activity. Start with engine versions, ranked results, timings for each search stage and optional relevance feedback.

This is a preliminary assessment for planning, not a legal opinion or approval to activate collection. Confirm the controller, applicable jurisdictions and implementation with legal counsel before launch. These proposals do not authorise new uses of previously collected data.

This document contains policy analysis and proposed fields only. It contains no query records, export-derived statistics, examples from user searches or input fingerprints. Private inputs and all derived outputs must remain outside this repository.

## Current commitments

The privacy policy source reviewed in the LeanExplore web repository excludes accounts, IP addresses, session identifiers and precise timestamps from its de-identified query dataset. It retains the UTC day. It describes retention of up to 24 months for those queries, seven days for operational logs and normally 24 hours for IP addresses used for rate limiting.

These observations concern `app/frontend/src/views/legal/PrivacyPolicyView.vue` in the web repository snapshot reviewed on 30 October 2026. They do not verify which policy version is deployed. Check the deployed policy before making changes.

Adding session tracking or links to personal history requires reviewing the collection design and notice before launch. A policy update alone does not establish a lawful basis. Privacy promises also matter under US law, subject to the relevant regulator's jurisdiction. [FTC guidance](https://www.ftc.gov/business-guidance/privacy-security)

## Proposed metadata

These are design recommendations, not automatic legal exemptions. Treat individual events as potentially personal until their context and re-identification risk have been assessed.

| Data | What it would help answer | Suggested collection method |
| --- | --- | --- |
| Engine, model, index and corpus versions | Which configuration produced the result? | Generate on the server without a user identifier. |
| Retrieval, reranking and response times; error categories; cache hits | Where is the service slow or failing? | Aggregate counters and distributions. Exclude query text and sensitive error details. |
| Candidate count, returned count, filters and requested result limit | Are filters or retrieval stages removing useful candidates? | Minimise event detail and aggregate by day and version. |
| Public declaration identifiers, result positions and scores | What does the engine rank highly, and how does that change? | Do not link to accounts. Limit retention of detailed events. |
| Query length bands and flags for Lean syntax or identifier lookup | Which forms of request need better handling? | Compute on the server without retaining text extracts for these metrics. |
| Optional useful/not-useful feedback, selected result and its rank | Did the returned result help? | Use a short-lived token scoped to one search if correlation is needed. |
| Reformulations and task outcome | Why did the initial search fail? | Run a voluntary study with informed consent, temporary identifiers and a stated duration. |

Clicks are weak relevance signals: a user may click an unsuitable result. Explicit relevance judgments are more useful for benchmark scoring. A temporary token reduces linkability but does not by itself make an event anonymous.

Removing names and IP addresses is insufficient to establish anonymity. Query text can contain identifying details, local paths or confidential code. Hashing, encryption and random identifiers do not automatically anonymise records. Combinations of metadata can also identify someone. Assess singling out, linkability and inference risks before calling a dataset anonymous. [CNIL guidance](https://www.cnil.fr/fr/identifier-les-donnees-personnelles)

## Legal basis and consent

- Minimised technical metrics may be candidates for legitimate interests where the GDPR applies. Document the purpose, necessity and balance against users' rights. Possible future usefulness is not enough. Serving a search and keeping it for model training require separate purpose analysis. [European Commission guidance](https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/legal-grounds-processing-data_en)
- Browser tracking has additional rules. Cookies, local storage and other tracking mechanisms may require prior consent independently of the GDPR basis for subsequent processing. Italian guidance allows limited analytics exemptions under specific conditions. Do not assume they cover individual session histories or apply identically in other countries. For behavioural studies, an optional opt-in programme is the proposed starting point; this is not a claim that every click event always requires consent. [Italian Garante guidance](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/9677876)
- For additional full queries or proof states, offer a voluntary donation flow with a preview. Explain intended uses, including diagnosis, benchmarking, training and any publication. Consent from the submitting user does not automatically resolve third-party personal data or confidentiality issues. Purpose limitation and minimisation still apply. [GDPR Articles 5-7](https://www.cnil.fr/fr/reglement-europeen-protection-donnees/chapitre2)

## Collection design

1. Define the question each field answers, its purpose, lawful basis, access permissions and deletion deadline. Check whether aggregation can answer the same question without storing individual events.
2. Separate search-quality statistics, security logs and personal search history. Keep account IDs, IP addresses and authentication tokens out of evaluation data. Prevent accidental copies in proxy logs, error reporting and analytics providers.
3. Update the notice before new collection. Provide controls for anonymous users, API clients and MCP clients as well as signed-in users. Acknowledging a policy is not specific consent. Where legitimate interests apply, support the right to object; where consent applies, support withdrawal. [GDPR Articles 13 and 21](https://www.cnil.fr/fr/reglement-europeen-protection-donnees/chapitre3)
4. Start with a short retention period for detailed events, such as 30 days, subject to a documented need. This is a proposal, not a statutory deadline. Keep longer-lived aggregates only after checking disclosure risks. Small groups and unusual combinations can remain identifiable. Enforce deletion and account for backups and downstream copies.
5. Check provider roles, access agreements and international transfers. For transfers subject to GDPR transfer rules, the EU-US Data Privacy Framework covers participating organisations. Other cases need an appropriate mechanism, such as standard contractual clauses with the required assessment. A general statement that using the service means accepting US processing is not a substitute for that analysis. [European Commission guidance](https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/eu-us-data-transfers_en)

## Questions to resolve before launch

- Who determines the purposes and means of the new collection: the current operator, Numina, or both? The reviewed policy describes a US operator and US servers; the future arrangement has not been confirmed.
- Which jurisdictions apply? GDPR can apply to an operator outside the EU, but website accessibility from Europe alone is insufficient. Establishment, offering services and monitoring behaviour need assessment. [EDPB territorial-scope guidelines](https://www.edpb.europa.eu/sites/default/files/files/file1/edpb_guidelines_3_2018_territorial_scope_after_public_consultation_en_0.pdf)
- Does the operator meet the CCPA's applicability criteria? It has specific conditions and thresholds. Being outside its scope does not establish that all other privacy obligations are inapplicable. [California Privacy Protection Agency FAQ](https://www.cppa.ca.gov/faq.html)
- Which proposed events require consent or another basis in the applicable jurisdictions? What information and practical controls will each client expose?
- Can the same evaluation be done with less detail, and can deletion and separation from identity be verified?

The first implementation should focus on engine versions, ranked public results, stage timings and optional relevance feedback. Add session-level studies only after settling their purpose, controls and legal basis. Keep production data and all export-derived artifacts outside this repository.
