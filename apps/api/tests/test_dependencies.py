# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from types import SimpleNamespace

from app.api.dependencies import (
    get_answer_service,
    get_application,
    get_conversation_service,
    get_document_service,
    get_model_catalog_service,
    get_upload_service,
)


def test_api_dependencies_return_composed_services() -> None:
    application = SimpleNamespace(
        conversation_service=object(),
        answer_service=object(),
        document_service=object(),
        upload_service=object(),
        model_catalog_service=object(),
    )
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(application=application))
    )

    resolved = get_application(request)  # type: ignore[arg-type]

    assert resolved is application
    assert get_conversation_service(resolved) is application.conversation_service  # type: ignore[arg-type]
    assert get_answer_service(resolved) is application.answer_service  # type: ignore[arg-type]
    assert get_document_service(resolved) is application.document_service  # type: ignore[arg-type]
    assert get_upload_service(resolved) is application.upload_service  # type: ignore[arg-type]
    assert get_model_catalog_service(resolved) is application.model_catalog_service  # type: ignore[arg-type]
