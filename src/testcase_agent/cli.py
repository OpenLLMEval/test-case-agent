from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from testcase_agent import __version__
from testcase_agent.agent import TestCaseGenerationAgent
from testcase_agent.exporters import export_suite

console = Console()


@click.group()
@click.version_option(__version__, prog_name="testcase-agent")
def main() -> None:
    """Generate structured test cases from source code or requirements."""


@main.command("generate")
@click.argument("source", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--format",
    "format_name",
    type=click.Choice(["json", "markdown", "md", "pytest"], case_sensitive=False),
    default="markdown",
    show_default=True,
    help="Output format for generated test cases.",
)
@click.option(
    "--mode",
    type=click.Choice(["rule", "llm"], case_sensitive=False),
    default="rule",
    show_default=True,
    help="Generation strategy. LLM mode requires OPENAI_API_KEY.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Write output to a file instead of stdout.",
)
@click.option("--summary/--no-summary", default=True, show_default=True)
def generate(source: Path, format_name: str, mode: str, output: Path | None, summary: bool) -> None:
    """Analyze SOURCE and generate test cases."""
    agent = TestCaseGenerationAgent(mode=mode)

    with console.status(f"Analyzing [bold]{source}[/bold]..."):
        suite = agent.generate_from_file(source)

    exported = export_suite(suite, format_name)

    if output:
        output.write_text(exported, encoding="utf-8")
        console.print(f"[green]Wrote[/green] {len(suite.test_cases)} test cases to {output}")
    else:
        console.print(exported)

    if summary:
        _print_summary(suite)


@main.command("analyze")
@click.argument("source", type=click.Path(exists=True, dir_okay=False, path_type=Path))
def analyze(source: Path) -> None:
    """Show discovered units under test without generating cases."""
    agent = TestCaseGenerationAgent()
    suite = agent.generate_from_file(source)

    table = Table(title=f"Units in {source.name}")
    table.add_column("Name")
    table.add_column("Kind")
    table.add_column("Signature")
    table.add_column("Line", justify="right")

    for unit in suite.units:
        table.add_row(
            unit.name,
            unit.kind,
            unit.signature or "-",
            str(unit.line_number or "-"),
        )

    console.print(table)
    console.print(f"[bold]{len(suite.units)}[/bold] units, [bold]{len(suite.test_cases)}[/bold] generated cases")


def _print_summary(suite) -> None:
    table = Table(title="Generation Summary")
    table.add_column("Metric")
    table.add_column("Value", justify="right")

    table.add_row("Suite", suite.name)
    table.add_row("Units analyzed", str(len(suite.units)))
    table.add_row("Test cases", str(len(suite.test_cases)))
    table.add_row("Generator", suite.metadata.get("generator", suite.metadata.get("agent_mode", "unknown")))

    for test_type, count in sorted(suite.count_by_type.items()):
        table.add_row(f"Type: {test_type}", str(count))

    console.print()
    console.print(table)


if __name__ == "__main__":
    main()
