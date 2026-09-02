# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from comment_rules import find_comment_rule_errors


class CommentRuleTests(unittest.TestCase):
    def audit(self, name: str, source: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / name
            path.write_text(source, encoding="utf-8")
            return find_comment_rule_errors(root, [root])

    def test_flags_long_python_comments_and_docstrings(self) -> None:
        errors = self.audit(
            "sample.py",
            '"""One. Two. Three. Four. Five. Six."""\n'
            "# One. Two. Three. Four.\n"
            "VALUE = 1\n",
        )

        self.assertEqual(len(errors), 2)
        self.assertIn("sample.py:1", errors[0])
        self.assertIn("maximum is 5", errors[0])
        self.assertIn("sample.py:2", errors[1])
        self.assertIn("maximum is 3", errors[1])

    def test_ignores_python_directives_and_string_content(self) -> None:
        errors = self.audit(
            "sample.py",
            "# SPDX-License-Identifier: Apache-2.0\n"
            "VALUE = '# One. Two. Three. Four.'  # type: ignore[assignment]\n"
            "OTHER = 2  # noqa: F401\n"
            "COVERED = 3  # pragma: no cover\n",
        )

        self.assertEqual(errors, [])

    def test_flags_typescript_prose_but_ignores_urls_and_directives(self) -> None:
        errors = self.audit(
            "sample.ts",
            "/* SPDX-License-Identifier: Apache-2.0 */\n"
            "// @vitest-environment jsdom\n"
            "// eslint-disable-next-line no-console\n"
            "const url = 'http://localhost:8000/api';\n"
            "// One. Two. Three. Four.\n",
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("sample.ts:5", errors[0])

    def test_groups_adjacent_line_comments(self) -> None:
        errors = self.audit(
            "sample.ts",
            "// One.\n"
            "// Two.\n"
            "// Three.\n"
            "// Four.\n",
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("sample.ts:1", errors[0])

    def test_flags_long_sql_comment_blocks(self) -> None:
        errors = self.audit(
            "sample.sql",
            "-- SPDX-License-Identifier: Apache-2.0\n"
            "/* One. Two. Three. Four. */\n"
            "SELECT 1;\n",
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("sample.sql:2", errors[0])

    def test_directive_cannot_hide_prose_in_the_same_block(self) -> None:
        errors = self.audit(
            "sample.ts",
            "/*\n"
            " * SPDX-License-Identifier: Apache-2.0\n"
            " * One. Two. Three. Four.\n"
            " */\n",
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("sample.ts:1", errors[0])

    def test_accepts_three_comment_sentences_and_five_docstring_sentences(self) -> None:
        errors = self.audit(
            "sample.py",
            '"""One. Two. Three. Four. Five."""\n'
            "# One. Two. Three.\n"
            "VALUE = 1\n",
        )

        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
