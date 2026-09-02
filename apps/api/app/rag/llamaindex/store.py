# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from hashlib import sha256
from typing import Any, Protocol

from llama_index.core.schema import BaseNode
from llama_index.core.vector_stores.types import BasePydanticVectorStore
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

LLAMAINDEX_SCHEMA = "citenook_llamaindex"
TABLE_PREFIX = "citenook_nodes"


class NodeStore(Protocol):
    def add(self, nodes: list[BaseNode]) -> list[str]: ...

    def delete(self, ref_doc_id: str) -> None: ...


class NodeStoreFactory(Protocol):
    def write_store(self, embedding_model: str, dimension: int) -> NodeStore: ...

    def existing_stores(
        self,
        session: Session,
        embedding_model: str,
    ) -> list[NodeStore]: ...


class RetrievalStoreFactory(Protocol):
    def read_store(
        self,
        session: Session,
        embedding_model: str,
        dimension: int,
    ) -> BasePydanticVectorStore | None: ...


class PostgresNodeStoreFactory:
    def __init__(self, database_url: str) -> None:
        url = make_url(database_url)
        self._connection_string = url.set(
            drivername="postgresql+psycopg2"
        ).render_as_string(hide_password=False)
        self._async_connection_string = url.set(
            drivername="postgresql+asyncpg"
        ).render_as_string(hide_password=False)

    def write_store(self, embedding_model: str, dimension: int) -> NodeStore:
        return self._store(
            table_name=table_name(embedding_model, dimension),
            dimension=dimension,
            perform_setup=True,
        )

    def existing_stores(
        self,
        session: Session,
        embedding_model: str,
    ) -> list[NodeStore]:
        prefix = f"data_{table_prefix(embedding_model)}"
        names = session.scalars(
            text(
                "SELECT tablename FROM pg_catalog.pg_tables "
                "WHERE schemaname = :schema_name "
                "AND left(tablename, :prefix_length) = :prefix "
                "ORDER BY tablename"
            ),
            {
                "schema_name": LLAMAINDEX_SCHEMA,
                "prefix": prefix,
                "prefix_length": len(prefix),
            },
        ).all()
        stores: list[NodeStore] = []
        for persisted_name in names:
            suffix = str(persisted_name).removeprefix(prefix)
            if not suffix.isdigit() or int(suffix) <= 0:
                continue
            stores.append(
                self._store(
                    table_name=str(persisted_name).removeprefix("data_"),
                    dimension=int(suffix),
                    perform_setup=False,
                )
            )
        return stores

    def read_store(
        self,
        session: Session,
        embedding_model: str,
        dimension: int,
    ) -> PGVectorStore | None:
        persisted_name = f"data_{table_name(embedding_model, dimension)}"
        exists = session.scalar(
            text(
                "SELECT EXISTS ("
                "SELECT 1 FROM pg_catalog.pg_tables "
                "WHERE schemaname = :schema_name AND tablename = :table_name"
                ")"
            ),
            {
                "schema_name": LLAMAINDEX_SCHEMA,
                "table_name": persisted_name,
            },
        )
        if not exists:
            return None
        return self._store(
            table_name=persisted_name.removeprefix("data_"),
            dimension=dimension,
            perform_setup=False,
        )

    def _store(
        self,
        *,
        table_name: str,
        dimension: int,
        perform_setup: bool,
    ) -> PGVectorStore:
        return PGVectorStore(
            connection_string=self._connection_string,
            async_connection_string=self._async_connection_string,
            table_name=table_name,
            schema_name=LLAMAINDEX_SCHEMA,
            embed_dim=dimension,
            hybrid_search=False,
            use_jsonb=True,
            perform_setup=perform_setup,
            initialization_fail_on_error=True,
            indexed_metadata_keys={
                ("document_id", "uuid"),
                ("embedding_model", "text"),
                ("ordinal", "integer"),
            },
            customize_query_fn=_stable_query_order,
        )


def _stable_query_order(statement: Any, table: Any, **_: Any) -> Any:
    return statement.order_by(
        text("(metadata_->>'ordinal')::integer ASC"),
        table.node_id.asc(),
    )


def table_prefix(embedding_model: str) -> str:
    digest = sha256(embedding_model.encode("utf-8")).hexdigest()[:16]
    return f"{TABLE_PREFIX}_{digest}_d"


def table_name(embedding_model: str, dimension: int) -> str:
    if dimension <= 0:
        raise ValueError("The embedding dimension must be positive.")
    return f"{table_prefix(embedding_model)}{dimension}"
