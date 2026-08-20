from __future__ import annotations

from pathlib import Path

from testcase_agent.analyzers import analyze_source
from testcase_agent.exporters import export_suite
from testcase_agent.generators import get_generator
from testcase_agent.models import TestSuite


class TestCaseGenerationAgent:
    """Orchestrates analysis, generation, and export of test cases."""

    def __init__(self, mode: str = "rule") -> None:
        self.mode = mode
        self.generator = get_generator(mode)

    def generate_from_file(self, source_path: str | Path) -> TestSuite:
        path = Path(source_path)
        content = path.read_text(encoding="utf-8")
        return self.generate_from_text(str(path), content)

    def generate_from_text(self, source_path: str, content: str) -> TestSuite:
        language, units = analyze_source(source_path, content)
        if not units:
            raise ValueError(f"No testable units found in {source_path}")

        suite = self.generator.generate(source_path, language, units)
        suite.metadata.setdefault("agent_mode", self.mode)
        suite.metadata["unit_count"] = len(units)
        return suite

    def generate_and_export(self, source_path: str | Path, format_name: str = "markdown") -> str:
        suite = self.generate_from_file(source_path)
        return export_suite(suite, format_name)
