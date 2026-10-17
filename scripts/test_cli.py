"""Quick interactive CLI to test the Analyst agent."""
from rich.console import Console
from rich.panel import Panel
from src.agent.analyst import analyze

console = Console()


def main() -> None:
    console.print(Panel.fit(
        "[bold cyan]Shockwave CLI[/bold cyan]\n"
        "Supply-Chain Risk Analyst — fragt den Graph.\n"
        "Beispiele:\n"
        "  - Welche versteckten Risiken hat Apple?\n"
        "  - Was passiert wenn TSMC 6 Monate ausfaellt?\n"
        "  - Zeig mir die abhaengigsten Firmen von ASML.",
        border_style="cyan",
    ))

    while True:
        try:
            q = console.input("\n[bold green]Frage>[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q or q in {"exit", "quit"}:
            break
        try:
            result = analyze(q)
        except Exception as e:
            console.print(f"[red]Fehler:[/red] {e}")
            continue
        console.print(Panel(result["final_text"], title=f"Analyst ({result['turns']} turns)", border_style="green"))


if __name__ == "__main__":
    main()
