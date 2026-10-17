# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import sys
from typing import Any


def create_judge(config: Any) -> DeepEvalJudge:
    if "deepeval" in sys.modules:
        raise RuntimeError("Run the judge in a fresh CLI process to apply privacy settings first.")
    os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "1"
    os.environ["DEEPEVAL_UPDATE_WARNING_OPT_IN"] = "0"
    os.environ["DEEPEVAL_DISABLE_DOTENV"] = "1"
    try:
        return DeepEvalJudge(config)
    except ImportError as error:
        raise RuntimeError(
            "Install the optional judge extra: uv sync --locked --extra judge."
        ) from error


class DeepEvalJudge:
    def __init__(self, config: Any) -> None:
        from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
        from deepeval.models import OllamaModel
        from deepeval.test_case import LLMTestCase

        self.config = config
        self.test_case = LLMTestCase
        self.metrics = {
            "answer relevancy": AnswerRelevancyMetric,
            "cited-excerpt faithfulness": FaithfulnessMetric,
        }
        self.model = OllamaModel(
            model=config.model,
            base_url=config.base_url,
            temperature=config.temperature,
            timeout=config.request_timeout,
            follow_redirects=False,
            trust_env=False,
        )

    def measure(self, name: str, question: str, answer: str, snippets: list[str]) -> dict[str, Any]:
        metric = self.metrics[name](
            model=self.model,
            threshold=self.config.threshold,
            include_reason=True,
            async_mode=False,
            strict_mode=False,
            eval_mode="llm",
        )
        test_case = self.test_case(
            input=question,
            actual_output=answer,
            retrieval_context=snippets if name == "cited-excerpt faithfulness" else None,
        )
        metric.measure(test_case, _show_indicator=False)
        if metric.error:
            raise RuntimeError(metric.error)
        return {
            "score": metric.score,
            "judgeReason": metric.reason,
            "usage": {
                "reportedEvaluationCost": metric.evaluation_cost,
                "tokens": None,
                "note": "DeepEval Ollama adapter does not expose token usage; cost may be unknown.",
            },
        }
