from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TestType(str, Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    EDGE = "edge"
    NEGATIVE = "negative"
    BOUNDARY = "boundary"
    SECURITY = "security"
    PERFORMANCE = "performance"


class TestPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SourceUnit(BaseModel):
    """A function, method, or requirement entry under test."""

    name: str
    kind: str = Field(description="function | method | class | requirement")
    signature: str | None = None
    docstring: str | None = None
    parameters: list[str] = Field(default_factory=list)
    return_type: str | None = None
    source_file: str | None = None
    line_number: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TestCase(BaseModel):
    id: str
    title: str
    description: str
    test_type: TestType
    priority: TestPriority = TestPriority.MEDIUM
    target: str = Field(description="Function, method, or requirement name under test")
    preconditions: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    expected_result: str
    test_data: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class TestSuite(BaseModel):
    name: str
    source: str
    language: str | None = None
    units: list[SourceUnit] = Field(default_factory=list)
    test_cases: list[TestCase] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def count_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for case in self.test_cases:
            key = case.test_type.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    @property
    def count_by_priority(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for case in self.test_cases:
            key = case.priority.value
            counts[key] = counts.get(key, 0) + 1
        return counts


class AnalysisContext(BaseModel):
    source_path: str
    content: str
    language: str
    units: list[SourceUnit] = Field(default_factory=list)
