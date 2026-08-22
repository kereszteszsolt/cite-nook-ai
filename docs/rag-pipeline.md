# RAG pipeline roadmap

MRA-001 contains only the runtime foundation. The document-to-answer path is added incrementally:

1. MRA-002 selects and persists Ollama chat and embedding models.
2. MRA-003 persists supported uploads.
3. MRA-004 extracts, chunks, and embeds documents in the worker. Implemented.
4. MRA-005 exposes processing state and document management. Implemented.
5. MRA-006 persists conversations and messages. Implemented.
6. MRA-007 retrieves compatible chunks and returns grounded answers with citations. Implemented.
7. MRA-008 lets users keep documents stored while excluding inactive ones from retrieval. Implemented.

Each story's acceptance criteria were checked only after its implementation and verification evidence were complete.
