from __future__ import annotations

from testcase_agent.analyzers.base import BaseAnalyzer, detect_language
from testcase_agent.analyzers.python_analyzer import PythonAnalyzer, RequirementsAnalyzer
from testcase_agent.models import AnalysisContext, SourceUnit

ANALYZERS: list[BaseAnalyzer] = [
    PythonAnalyzer(),
    RequirementsAnalyzer(),
]


def analyze_source(source_path: str, content: str) -> tuple[str, list[SourceUnit]]:
    language = detect_language(source_path, content)
    for analyzer in ANALYZERS:
        if analyzer.supports(language):
            context = analyzer.analyze(source_path, content)
            return language, context.units

    fallback = AnalysisContext(
        source_path=source_path,
        content=content,
        language=language,
        units=[
            SourceUnit(
                name="general_behavior",
                kind="requirement",
                docstring=content[:500],
                source_file=source_path,
            )
        ],
    )
    return language, fallback.units
