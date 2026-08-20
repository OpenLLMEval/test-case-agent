from __future__ import annotations

import json
import os

from testcase_agent.generators.base import BaseGenerator
from testcase_agent.generators.rule_based import RuleBasedGenerator
from testcase_agent.models import SourceUnit, TestSuite


class LLMGenerator(BaseGenerator):
    """Optional LLM-backed generator. Falls back to rule-based when unavailable."""

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self.model = model
        self._fallback = RuleBasedGenerator()

    def generate(self, source_path: str, language: str, units: list[SourceUnit]) -> TestSuite:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            suite = self._fallback.generate(source_path, language, units)
            suite.metadata["llm_status"] = "skipped_no_api_key"
            return suite

        try:
            from openai import OpenAI
        except ImportError:
            suite = self._fallback.generate(source_path, language, units)
            suite.metadata["llm_status"] = "skipped_missing_openai_package"
            return suite

        client = OpenAI(api_key=api_key)
        prompt = self._build_prompt(source_path, language, units)

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior QA engineer. Return ONLY valid JSON matching "
                        "the TestSuite schema with fields: name, source, language, test_cases "
                        "(each with id, title, description, test_type, priority, target, "
                        "preconditions, steps, expected_result, test_data, tags)."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        raw = response.choices[0].message.content or "{}"
        payload = json.loads(raw)
        suite = TestSuite.model_validate(
            {
                "name": payload.get("name", RuleBasedGenerator()._suite_name(source_path)),
                "source": source_path,
                "language": language,
                "units": [unit.model_dump() for unit in units],
                "test_cases": payload.get("test_cases", []),
                "metadata": {"generator": "llm", "model": self.model},
            }
        )
        return suite

    def _build_prompt(self, source_path: str, language: str, units: list[SourceUnit]) -> str:
        unit_lines = []
        for unit in units:
            unit_lines.append(
                f"- {unit.name} ({unit.kind}): {unit.signature or ''} :: {unit.docstring or 'no docstring'}"
            )

        return (
            f"Generate comprehensive test cases for `{source_path}` ({language}).\n"
            "Cover happy path, edge cases, boundary values, negative cases, and security where relevant.\n"
            "Units under test:\n"
            + "\n".join(unit_lines)
        )


def get_generator(mode: str = "rule") -> BaseGenerator:
    if mode == "llm":
        return LLMGenerator()
    return RuleBasedGenerator()
