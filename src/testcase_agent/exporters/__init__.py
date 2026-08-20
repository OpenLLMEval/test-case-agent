from __future__ import annotations

import json
from abc import ABC, abstractmethod

from testcase_agent.models import TestSuite


class BaseExporter(ABC):
    @abstractmethod
    def export(self, suite: TestSuite) -> str:
        raise NotImplementedError


class JsonExporter(BaseExporter):
    def export(self, suite: TestSuite) -> str:
        return json.dumps(suite.model_dump(), indent=2)


class MarkdownExporter(BaseExporter):
    def export(self, suite: TestSuite) -> str:
        lines = [
            f"# Test Suite: {suite.name}",
            "",
            f"- **Source:** `{suite.source}`",
            f"- **Language:** {suite.language or 'unknown'}",
            f"- **Total cases:** {len(suite.test_cases)}",
            "",
            "## Summary",
            "",
            "| Type | Count |",
            "| --- | ---: |",
        ]

        for test_type, count in sorted(suite.count_by_type.items()):
            lines.append(f"| {test_type} | {count} |")

        lines.extend(["", "## Test Cases", ""])

        for case in suite.test_cases:
            lines.extend(
                [
                    f"### {case.id}: {case.title}",
                    "",
                    f"- **Type:** {case.test_type.value}",
                    f"- **Priority:** {case.priority.value}",
                    f"- **Target:** `{case.target}`",
                    "",
                    case.description,
                    "",
                    "**Preconditions:**",
                ]
            )
            for item in case.preconditions or ["None"]:
                lines.append(f"- {item}")

            lines.extend(["", "**Steps:**"])
            for index, step in enumerate(case.steps, start=1):
                lines.append(f"{index}. {step}")

            lines.extend(
                [
                    "",
                    f"**Expected result:** {case.expected_result}",
                    "",
                ]
            )

        return "\n".join(lines)


class PytestExporter(BaseExporter):
    def export(self, suite: TestSuite) -> str:
        lines = [
            '"""Auto-generated pytest stubs from testcase-agent."""',
            "",
            "import pytest",
            "",
        ]

        grouped: dict[str, list] = {}
        for case in suite.test_cases:
            grouped.setdefault(case.target, []).append(case)

        for target, cases in grouped.items():
            safe_target = target.replace(".", "_").replace("-", "_")
            lines.append(f"class Test{self._pascal(safe_target)}:")
            lines.append(f'    """Tests for {target}."""')
            lines.append("")

            for case in cases:
                fn_name = self._test_function_name(case)
                lines.append(f"    def {fn_name}(self):")
                lines.append(f'        """{case.title}"""')
                lines.append("        # Preconditions")
                for precondition in case.preconditions:
                    lines.append(f"        # - {precondition}")
                lines.append("        # Arrange")
                if case.test_data:
                    for key, value in case.test_data.items():
                        lines.append(f"        {key} = {value!r}")
                lines.append("        # Act")
                for step in case.steps:
                    lines.append(f"        # {step}")
                lines.append("        # Assert")
                lines.append(f"        # Expected: {case.expected_result}")
                lines.append("        pytest.skip('Implement generated test case')")
                lines.append("")

            lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    def _pascal(self, value: str) -> str:
        parts = [part for part in value.split("_") if part]
        return "".join(part[:1].upper() + part[1:] for part in parts) or "Generated"

    def _test_function_name(self, case) -> str:
        slug = case.title.lower()
        slug = "".join(ch if ch.isalnum() else "_" for ch in slug)
        slug = "_".join(part for part in slug.split("_") if part)
        return f"test_{slug[:60]}"


EXPORTERS: dict[str, BaseExporter] = {
    "json": JsonExporter(),
    "markdown": MarkdownExporter(),
    "md": MarkdownExporter(),
    "pytest": PytestExporter(),
}


def export_suite(suite: TestSuite, format_name: str) -> str:
    exporter = EXPORTERS.get(format_name.lower())
    if exporter is None:
        supported = ", ".join(sorted(EXPORTERS))
        raise ValueError(f"Unsupported format '{format_name}'. Choose one of: {supported}")
    return exporter.export(suite)
