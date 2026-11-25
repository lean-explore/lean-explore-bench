# Search telemetry: privacy and legal assessment

Prepared on 31 October 2026 from research conducted on 30 October 2026.

This note proposes which additional data LeanExplore could collect to measure search quality
without building a history of each user's activity, and which legal questions must be settled
first. It is a preliminary assessment for planning, not a legal opinion, and it approves no
collection and no new use of existing data.

## Current commitments

The privacy policy in the LeanExplore web repository
(`app/frontend/src/views/legal/PrivacyPolicyView.vue`, snapshot of 30 October 2026) describes
a de-identified query dataset without accounts, IP addresses, session identifiers or precise
timestamps; only the UTC day is kept. It states retention of up to 24 months for those
queries, seven days for operational logs and normally 24 hours for IP addresses used for rate
limiting. Whether this version is deployed was not verified.

Session tracking or links to personal history would need a new design and notice. A policy
update alone does not establish a lawful basis, and privacy promises also matter under US law
([FTC guidance](https://www.ftc.gov/business-guidance/privacy-security)).

## Proposed data

| Data | Question | Collection |
|---|---|---|
| Engine, model, index and corpus versions | Which configuration produced the result? | Server-side, no user identifier |
| Stage timings, error categories, cache hits | Where is the service slow or failing? | Aggregate counters, no query text |
| Candidate and returned counts, filters, limit | Do stages remove useful candidates? | Aggregated by day and version |
| Public declaration identifiers, positions, scores | What ranks highly? | No account link, short retention |
| Query length bands, flags for Lean syntax | Which query forms need work? | Computed server-side, no text kept |
| Optional feedback, selected result and its rank | Did the result help? | Short-lived token scoped to one search |
| Reformulations and task outcome | Why did the first search fail? | Voluntary study with consent |

The proposed first step is versions, ranked public results, stage timings and optional
feedback. Clicks are weak relevance signals; explicit judgments are more useful for scoring.

Removing names and IP addresses does not make data anonymous. Query text can contain
identifying details, local paths or confidential code, and hashing does not anonymise records
([CNIL guidance](https://www.cnil.fr/fr/identifier-les-donnees-personnelles)).

## Legal basis

- Where the GDPR applies, minimised technical metrics may rest on documented legitimate
  interests. Serving a search and keeping it for model training are separate purposes
  ([European Commission](https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/legal-grounds-processing-data_en)).
- Cookies, local storage and similar mechanisms may require prior consent whatever the GDPR
  basis; Italian guidance exempts some analytics
  ([Garante](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/9677876)).
  Behavioural studies are therefore proposed as opt-in.
- Additional full queries or proof states would come from voluntary donation with a preview.
  The donor's consent does not cover third-party data ([GDPR Articles 5-7](https://www.cnil.fr/fr/reglement-europeen-protection-donnees/chapitre2)).

## Design requirements

1. Each field has a stated purpose, lawful basis and deletion deadline, and is collected
   only if aggregates cannot answer the question.
2. Account IDs, IP addresses and tokens stay out of evaluation data, which is kept apart
   from security logs and personal search history.
3. The notice is updated before collection starts. Anonymous, API and MCP users can also
   object or withdraw consent
   ([GDPR Articles 13 and 21](https://www.cnil.fr/fr/reglement-europeen-protection-donnees/chapitre3)).
4. Detailed events are kept briefly; 30 days is a proposal, not a statutory figure.
5. International transfers need a mechanism: the EU-US Data Privacy Framework for
   participating organisations, otherwise for example standard contractual clauses
   ([European Commission](https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/eu-us-data-transfers_en)).

## Open questions

- Who controls the new collection: the current operator, Numina, or both?
- Does the GDPR apply? Accessibility from Europe alone is insufficient
  ([EDPB guidelines](https://www.edpb.europa.eu/sites/default/files/files/file1/edpb_guidelines_3_2018_territorial_scope_after_public_consultation_en_0.pdf)).
- Does the operator meet the CCPA thresholds ([CPPA FAQ](https://www.cppa.ca.gov/faq.html))?
