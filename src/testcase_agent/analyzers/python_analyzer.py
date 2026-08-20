from __future__ import annotations

import ast
import re
from typing import Any

from testcase_agent.analyzers.base import BaseAnalyzer
from testcase_agent.models import AnalysisContext, SourceUnit


class PythonAnalyzer(BaseAnalyzer):
    def supports(self, language: str) -> bool:
        return language == "python"

    def analyze(self, source_path: str, content: str) -> AnalysisContext:
        tree = ast.parse(content, filename=source_path)
        units: list[SourceUnit] = []

        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                units.append(self._function_unit(node, source_path, kind="function"))
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and not item.name.startswith("_"):
                        units.append(
                            self._function_unit(
                                item,
                                source_path,
                                kind="method",
                                class_name=node.name,
                            )
                        )

        return AnalysisContext(
            source_path=source_path,
            content=content,
            language="python",
            units=units,
        )

    def _function_unit(
        self,
        node: ast.FunctionDef,
        source_path: str,
        kind: str,
        class_name: str | None = None,
    ) -> SourceUnit:
        params = [arg.arg for arg in node.args.args if arg.arg not in {"self", "cls"}]
        return_type = self._annotation(node.returns)
        signature = self._build_signature(node.name, params, return_type, class_name)
        name = f"{class_name}.{node.name}" if class_name else node.name

        return SourceUnit(
            name=name,
            kind=kind,
            signature=signature,
            docstring=ast.get_docstring(node),
            parameters=params,
            return_type=return_type,
            source_file=source_path,
            line_number=node.lineno,
            metadata={"class_name": class_name} if class_name else {},
        )

    def _build_signature(
        self,
        name: str,
        params: list[str],
        return_type: str | None,
        class_name: str | None,
    ) -> str:
        prefix = f"{class_name}." if class_name else ""
        joined = ", ".join(params)
        signature = f"{prefix}{name}({joined})"
        if return_type:
            signature += f" -> {return_type}"
        return signature

    def _annotation(self, node: ast.expr | None) -> str | None:
        if node is None:
            return None
        try:
            return ast.unparse(node)
        except Exception:
            return None


class RequirementsAnalyzer(BaseAnalyzer):
    _bullet = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+(.+)$")
    _heading = re.compile(r"^#{1,6}\s+(.+)$")

    def supports(self, language: str) -> bool:
        return language == "requirements"

    def analyze(self, source_path: str, content: str) -> AnalysisContext:
        units: list[SourceUnit] = []
        current_section = "General"

        for index, line in enumerate(content.splitlines(), start=1):
            heading = self._heading.match(line)
            if heading:
                current_section = heading.group(1).strip()
                continue

            bullet = self._bullet.match(line)
            if bullet:
                requirement = bullet.group(1).strip()
                units.append(
                    SourceUnit(
                        name=self._slug(requirement),
                        kind="requirement",
                        docstring=requirement,
                        source_file=source_path,
                        line_number=index,
                        metadata={"section": current_section},
                    )
                )

        return AnalysisContext(
            source_path=source_path,
            content=content,
            language="requirements",
            units=units,
        )

    def _slug(self, text: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower()).strip("_")
        return slug[:60] or "requirement"
