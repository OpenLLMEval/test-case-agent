from __future__ import annotations

import re

from testcase_agent.generators.base import BaseGenerator
from testcase_agent.models import (
    SourceUnit,
    TestCase,
    TestPriority,
    TestSuite,
    TestType,
)


class RuleBasedGenerator(BaseGenerator):
    """Generate structured test cases using deterministic heuristics."""

    def generate(self, source_path: str, language: str, units: list[SourceUnit]) -> TestSuite:
        cases: list[TestCase] = []
        counter = 1

        for unit in units:
            generated = self._cases_for_unit(unit, counter, language)
            cases.extend(generated)
            counter += len(generated)

        suite_name = self._suite_name(source_path)
        return TestSuite(
            name=suite_name,
            source=source_path,
            language=language,
            units=units,
            test_cases=cases,
            metadata={"generator": "rule_based"},
        )

    def _cases_for_unit(self, unit: SourceUnit, start_id: int, language: str) -> list[TestCase]:
        if unit.kind == "requirement":
            return self._requirement_cases(unit, start_id)

        cases = [self._happy_path(unit, start_id)]
        next_id = start_id + 1

        for param in unit.parameters:
            cases.append(self._null_or_empty_case(unit, param, next_id))
            next_id += 1
            cases.append(self._type_mismatch_case(unit, param, next_id))
            next_id += 1

        if self._looks_numeric(unit):
            cases.extend(self._boundary_cases(unit, next_id))
            next_id += 2

        cases.append(self._exception_case(unit, next_id))
        return cases

    def _requirement_cases(self, unit: SourceUnit, start_id: int) -> list[TestCase]:
        requirement = unit.docstring or unit.name
        return [
            TestCase(
                id=f"TC-{start_id:03d}",
                title=f"Verify requirement: {requirement[:80]}",
                description=f"Validate that the system satisfies: {requirement}",
                test_type=TestType.INTEGRATION,
                priority=TestPriority.HIGH,
                target=unit.name,
                preconditions=["System is deployed and accessible"],
                steps=[
                    "Set up the environment according to preconditions",
                    f"Execute the workflow described by: {requirement}",
                    "Observe system behavior and outputs",
                ],
                expected_result="Requirement is satisfied without errors",
                tags=["requirement", unit.metadata.get("section", "general")],
            ),
            TestCase(
                id=f"TC-{start_id + 1:03d}",
                title=f"Negative: requirement failure for {unit.name}",
                description=f"Validate graceful handling when requirement cannot be met: {requirement}",
                test_type=TestType.NEGATIVE,
                priority=TestPriority.MEDIUM,
                target=unit.name,
                preconditions=["System is deployed and accessible"],
                steps=[
                    "Induce a condition that violates the requirement",
                    "Attempt the same workflow",
                ],
                expected_result="System rejects invalid state with a clear, actionable error",
                tags=["requirement", "negative"],
            ),
        ]

    def _happy_path(self, unit: SourceUnit, case_id: int) -> TestCase:
        return TestCase(
            id=f"TC-{case_id:03d}",
            title=f"Happy path: {unit.name} with valid inputs",
            description=f"Verify {unit.name} returns expected output for typical valid inputs",
            test_type=TestType.UNIT,
            priority=TestPriority.CRITICAL,
            target=unit.name,
            preconditions=["Dependencies are mocked or stubbed as needed"],
            steps=[
                f"Prepare valid inputs for {unit.signature or unit.name}",
                f"Invoke {unit.name}",
                "Capture the return value or side effects",
            ],
            expected_result=f"{unit.name} completes successfully and returns the expected {unit.return_type or 'result'}",
            tags=["happy-path", unit.kind],
        )

    def _null_or_empty_case(self, unit: SourceUnit, param: str, case_id: int) -> TestCase:
        return TestCase(
            id=f"TC-{case_id:03d}",
            title=f"Edge: {unit.name} rejects null/empty `{param}`",
            description=f"Verify {unit.name} handles missing or empty `{param}` safely",
            test_type=TestType.EDGE,
            priority=TestPriority.HIGH,
            target=unit.name,
            steps=[
                f"Call {unit.name} with `{param}` set to None, null, or empty string",
            ],
            expected_result="Function raises a validation error or returns a safe default without crashing",
            test_data={param: None},
            tags=["edge", "null-input", param],
        )

    def _type_mismatch_case(self, unit: SourceUnit, param: str, case_id: int) -> TestCase:
        return TestCase(
            id=f"TC-{case_id:03d}",
            title=f"Negative: {unit.name} rejects invalid type for `{param}`",
            description=f"Verify {unit.name} rejects wrong-type input for `{param}`",
            test_type=TestType.NEGATIVE,
            priority=TestPriority.MEDIUM,
            target=unit.name,
            steps=[
                f"Call {unit.name} with `{param}` set to an incompatible type (e.g. string instead of int)",
            ],
            expected_result="Type error or validation error is raised before business logic executes",
            test_data={param: "__invalid_type__"},
            tags=["negative", "type-check", param],
        )

    def _boundary_cases(self, unit: SourceUnit, start_id: int) -> list[TestCase]:
        return [
            TestCase(
                id=f"TC-{start_id:03d}",
                title=f"Boundary: {unit.name} at minimum numeric input",
                description=f"Verify {unit.name} behavior at the lower boundary of numeric inputs",
                test_type=TestType.BOUNDARY,
                priority=TestPriority.MEDIUM,
                target=unit.name,
                steps=[f"Invoke {unit.name} with minimum allowed numeric values"],
                expected_result="Function handles minimum boundary without overflow or unexpected exceptions",
                test_data={"boundary": "min"},
                tags=["boundary", "min"],
            ),
            TestCase(
                id=f"TC-{start_id + 1:03d}",
                title=f"Boundary: {unit.name} at maximum numeric input",
                description=f"Verify {unit.name} behavior at the upper boundary of numeric inputs",
                test_type=TestType.BOUNDARY,
                priority=TestPriority.MEDIUM,
                target=unit.name,
                steps=[f"Invoke {unit.name} with maximum allowed numeric values"],
                expected_result="Function handles maximum boundary without overflow or unexpected exceptions",
                test_data={"boundary": "max"},
                tags=["boundary", "max"],
            ),
        ]

    def _exception_case(self, unit: SourceUnit, case_id: int) -> TestCase:
        return TestCase(
            id=f"TC-{case_id:03d}",
            title=f"Negative: {unit.name} propagates dependency failures",
            description=f"Verify {unit.name} surfaces errors when a dependency fails",
            test_type=TestType.NEGATIVE,
            priority=TestPriority.MEDIUM,
            target=unit.name,
            steps=[
                "Configure a mocked dependency to raise an exception",
                f"Invoke {unit.name}",
            ],
            expected_result="Exception is propagated or mapped to a domain-specific error",
            tags=["negative", "dependency-failure"],
        )

    def _looks_numeric(self, unit: SourceUnit) -> bool:
        hints = " ".join([unit.return_type or "", *unit.parameters]).lower()
        return any(token in hints for token in ("int", "float", "number", "amount", "count", "size", "limit"))

    def _suite_name(self, source_path: str) -> str:
        base = source_path.rsplit("/", 1)[-1]
        return re.sub(r"\.[^.]+$", "", base) + "_tests"
