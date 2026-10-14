# CiteNook fixture run

Small synthetic fixture checks only; these are not retrieval recall, factual accuracy, or model-graded faithfulness scores. Key facts use case-insensitive whole-term matching.

- Status: passed
- Started: 2026-10-14T20:17:13.569115+00:00
- Backend: native
- Chat model: `llama3.1:8b`
- Embedding model: `qwen3-embedding:0.6b`
- RAG_TOP_K: 5 (operator-supplied, not API-verified)
- Suite: `citenook-small-rag-v1` / `3896a8fd81ef0ee754d769b60b2c47742bfb0ae30ce15fef61d2f7b0d092ed5a`
- Fixture checks passed: 12/12 attempted (12 planned)
- expectedSources: 12/12 checked
- keyFacts: 9/9 checked
- noAnswer: 3/3 checked

| Case | Fixture check | API response time (ms) |
| --- | --- | ---: |
| amber-leader | pass | 14473 |
| amber-lens | pass | 11648 |
| amber-badge | pass | 11355 |
| birch-manager | pass | 13863 |
| birch-varieties | pass | 12490 |
| birch-room | pass | 12461 |
| copper-departure | pass | 11866 |
| copper-capacity | pass | 11207 |
| copper-destination | pass | 11131 |
| amber-price-unknown | pass | 12770 |
| birch-latitude-unknown | pass | 11805 |
| copper-ticket-unknown | pass | 12762 |

Cleanup errors: 0.
