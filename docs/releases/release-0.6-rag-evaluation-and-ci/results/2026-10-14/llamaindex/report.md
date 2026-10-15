# CiteNook fixture run

Small synthetic fixture checks only; these are not retrieval recall, factual accuracy, or model-graded faithfulness scores. Key facts use case-insensitive whole-term matching.

- Status: passed
- Started: 2026-10-14T20:22:24.367085+00:00
- Backend: llamaindex
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
| amber-leader | pass | 10819 |
| amber-lens | pass | 11133 |
| amber-badge | pass | 15369 |
| birch-manager | pass | 17470 |
| birch-varieties | pass | 19731 |
| birch-room | pass | 17893 |
| copper-departure | pass | 11926 |
| copper-capacity | pass | 11064 |
| copper-destination | pass | 10984 |
| amber-price-unknown | pass | 12191 |
| birch-latitude-unknown | pass | 11415 |
| copper-ticket-unknown | pass | 12110 |

Cleanup errors: 0.
