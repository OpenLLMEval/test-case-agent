"""Test Case Generation Agent — analyze code and produce structured test cases."""

__version__ = "0.1.0"

from testcase_agent.agent import TestCaseGenerationAgent
from testcase_agent.models import TestCase, TestPriority, TestSuite, TestType

__all__ = [
    "TestCase",
    "TestCaseGenerationAgent",
    "TestPriority",
    "TestSuite",
    "TestType",
    "__version__",
]
