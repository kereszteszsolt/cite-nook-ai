---
name: rag-pipeline
description: Implement or review CiteNook document ingestion and grounded answering. Use for upload persistence, worker jobs, extraction, chunking, Ollama embeddings/chat, pgvector retrieval, prompts, references, or document status changes.
---

# RAG pipeline

## Ingestion invariants

- Save the original file before queueing work.
- Keep queued, processing, ready, and failed states explicit.
- Extract only supported PDF, DOCX, TXT, and Markdown files.
- Chunk deterministically and retain page numbers when the format provides them.
- Store the embedding model on documents and chunks.
- Never mix vector dimensions/models in one retrieval query.
- Make failed jobs visible and keep their error message bounded.

## Answering invariants

- Embed the question with the conversation's embedding model.
- Retrieve only ready chunks embedded with that same model.
- Number sources deterministically as `S1`, `S2`, and so on.
- Tell the chat model to use only supplied sources and cite them.
- Return structured citations with document, page, chunk, snippet, and score.
- Persist the selected chat/embedding models on the conversation.
- If sources are missing or insufficient, fail clearly or state insufficiency; never invent a citation.

Prefer the official Ollama Python client and direct pgvector/SQLAlchemy operations. Do not introduce LangChain or another orchestration framework unless a later story requires behavior that the current small services cannot express cleanly.
