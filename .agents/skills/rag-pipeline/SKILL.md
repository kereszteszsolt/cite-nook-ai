---
name: rag-pipeline
description: Implement or review one approved CiteNook indexing, retrieval, model, grounding, citation, or RAG deployment story.
---

# RAG pipeline

## Shared rules

- Save the original file before its job is committed.
- Keep queued, processing, ready, and failed states clear.
- Keep common extraction page-aware when the file supports pages.
- Keep the embedding model on the document and index items.
- Never mix incompatible embedding models or vector sizes.
- Number sources in a stable order as `S1`, `S2`, and so on.
- Use only current sources as proof for the answer.
- Reject missing or invalid source markers.
- Store the answer and its source proof together.
- Keep failure text short and useful.

## Release 0.5 backend rules

- One deployment builds one `DocumentIndexer` and one `SourceRetriever`.
- Native stays the default and keeps Release 0.4 data compatible.
- LlamaIndex owns node work, vector storage, delete, and retrieval only.
- The common answer service owns prompt, chat, citation, timing, and message storage.
- Do not use a LlamaIndex query engine for final answers in this release.
- Do not import LlamaIndex from common or native modules.
- Do not add dual writes, dual queries, hot switching, or silent fallback.
- Delete selected index data before common document cleanup finishes.

Ask before implementation and ask again before commit. Follow the story criteria in order. Use comments only when code cannot explain a hard reason; prefer one short sentence and allow at most three in a block. Keep docstrings to five short sentences, preserve required directives, and move plans, history, and proof to Markdown.
