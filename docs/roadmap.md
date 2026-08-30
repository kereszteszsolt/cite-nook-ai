# Roadmap

## Release 0.5: clean architecture and selectable RAG backends

This release cleans old story records, source comments, the web structure, and the Python structure. It keeps the current native RAG path and adds a LlamaIndex path behind the same app rules. Each deployment starts one backend.

See the [Release 0.5 plan](releases/release-0.5-clean-rag-backends/README.md).

## Release 0.6: backend evaluation

This release stays planned until both Release 0.5 deployments are stable. It will run the same test documents and questions against native and LlamaIndex, one deployment at a time.

The evaluation will call the normal CiteNook HTTP API. It will not add a third LlamaIndex implementation under an evaluation folder. Ragas may score faithfulness and factual quality, while retrieval checks and response time may be measured beside those scores.

Release 0.6 story IDs will be created only after its scope is reviewed and approved.

## Later options

Possible later work includes an OpenAI-compatible model provider, hybrid search, reranking, retrieval tracing, and a citation inspector. These items are not part of Release 0.5 or Release 0.6.
