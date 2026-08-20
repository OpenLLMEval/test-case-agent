from __future__ import annotations

from pathlib import Path

import pytest

from testcase_agent import TestCaseGenerationAgent
from testcase_agent.analyzers import analyze_source
from testcase_agent.exporters import export_suite
from testcase_agent.models import TestType


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_analyze_python_module_finds_functions_and_methods():
    source = EXAMPLES / "sample_module.py"
    content = source.read_text(encoding="utf-8")
    language, units = analyze_source(str(source), content)

    assert language == "python"
    names = {unit.name for unit in units}
    assert "add" in names
    assert "divide" in names
    assert "UserService.create_user" in names


def test_analyze_requirements_extracts_bullets():
    source = EXAMPLES / "requirements.md"
    content = source.read_text(encoding="utf-8")
    language, units = analyze_source(str(source), content)

    assert language == "requirements"
    assert len(units) >= 5
    assert any("email" in (unit.docstring or "") for unit in units)


def test_rule_based_generation_produces_multiple_case_types():
    agent = TestCaseGenerationAgent(mode="rule")
    suite = agent.generate_from_file(EXAMPLES / "sample_module.py")

    assert len(suite.units) >= 3
    assert len(suite.test_cases) >= 10
    assert TestType.UNIT in {case.test_type for case in suite.test_cases}
    assert TestType.EDGE in {case.test_type for case in suite.test_cases}


def test_requirements_generation_creates_integration_and_negative_cases():
    agent = TestCaseGenerationAgent(mode="rule")
    suite = agent.generate_from_file(EXAMPLES / "requirements.md")

    assert len(suite.test_cases) == len(suite.units) * 2
    assert all(case.test_type.value in {"integration", "negative"} for case in suite.test_cases)


def test_markdown_exporter_renders_suite_header():
    agent = TestCaseGenerationAgent(mode="rule")
    suite = agent.generate_from_file(EXAMPLES / "sample_module.py")
    output = export_suite(suite, "markdown")

    assert "# Test Suite:" in output
    assert "Happy path" in output


def test_pytest_exporter_emits_skipped_stubs():
    agent = TestCaseGenerationAgent(mode="rule")
    suite = agent.generate_from_file(EXAMPLES / "sample_module.py")
    output = export_suite(suite, "pytest")

    assert "import pytest" in output
    assert "pytest.skip('Implement generated test case')" in output


def test_json_exporter_returns_valid_json():
    agent = TestCaseGenerationAgent(mode="rule")
    suite = agent.generate_from_file(EXAMPLES / "sample_module.py")
    output = export_suite(suite, "json")

    assert '"test_cases"' in output
    assert '"target": "add"' in output


def test_llm_mode_falls_back_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    agent = TestCaseGenerationAgent(mode="llm")
    suite = agent.generate_from_file(EXAMPLES / "sample_module.py")

    assert suite.metadata.get("llm_status") == "skipped_no_api_key"
    assert len(suite.test_cases) > 0


def test_generate_from_text_with_custom_path():
    agent = TestCaseGenerationAgent(mode="rule")
    suite = agent.generate_from_text("inline.py", "def ping(): return True\n")

    assert suite.source == "inline.py"
    assert any(unit.name == "ping" for unit in suite.units)


def test_empty_python_file_raises():
    agent = TestCaseGenerationAgent(mode="rule")
    with pytest.raises(ValueError, match="No testable units"):
        agent.generate_from_text("empty.py", "\n")
