from __future__ import annotations

from abc import ABC, abstractmethod

from testcase_agent.models import AnalysisContext, SourceUnit


class BaseAnalyzer(ABC):
    @abstractmethod
    def supports(self, language: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def analyze(self, source_path: str, content: str) -> AnalysisContext:
        raise NotImplementedError


def detect_language(source_path: str, content: str) -> str:
    path = source_path.lower()
    if path.endswith(".py"):
        return "python"
    if path.endswith((".js", ".jsx", ".ts", ".tsx")):
        return "javascript"
    if path.endswith((".md", ".txt", ".rst")):
        return "requirements"
    if "def " in content or "class " in content:
        return "python"
    if "function " in content or "const " in content:
        return "javascript"
    return "requirements"
