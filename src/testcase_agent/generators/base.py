from __future__ import annotations

from abc import ABC, abstractmethod

from testcase_agent.models import SourceUnit, TestCase, TestSuite


class BaseGenerator(ABC):
    @abstractmethod
    def generate(self, source_path: str, language: str, units: list[SourceUnit]) -> TestSuite:
        raise NotImplementedError
