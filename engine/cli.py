from pathlib import Path

import typer
from PIL import Image

from engine.config import config
from engine.services.npc_service import NpcService

app = typer.Typer(
    no_args_is_help=True,
    help="Tools für Social Game.",
)


@app.callback()
def main() -> None:
    """Hilft beim Starten und Pruefen der wichtigsten Social-Game-Funktionen."""


@app.command("npc-create")
def create_npc(
    npc_name: str = typer.Argument(..., help="Name des neuen NPCs; daraus wird eine snake_case-ID erzeugt."),
) -> None:
    """Legt einen neuen NPC unter .overrides/npcs/<npc_id>/ an."""
    if not npc_name.strip():
        typer.echo("NPC-Name darf nicht leer sein.")
        raise typer.Exit(code=1)

    try:
        target_dir = NpcService().create_override(npc_name)
    except ValueError as error:
        typer.echo(str(error))
        raise typer.Exit(code=1)

    typer.echo(f"NPC angelegt: {target_dir}")
    typer.echo(f"id={target_dir.name}")



@app.command()
def hello():
    """Prueft, ob die CLI grundsaetzlich laeuft."""
    typer.echo("Hello from Social Game CLI")


@app.command("web")
def web(
    host: str = typer.Option("127.0.0.1", "--host", help="Host fuer die Web-GUI."),
    port: int = typer.Option(8000, "--port", help="Port fuer die Web-GUI."),
    reload: bool = typer.Option(False, "--reload", help="Auto-Reload fuer Entwicklung aktivieren."),
):
    """Startet die browserbasierte GUI."""
    from engine.web.app import run as run_web

    run_web(host=host, port=port, reload=reload)


@app.command("icons")
def icons(
    input_image: str = typer.Option(
        str(config.PROJECT_ROOT / "engine" / "web" / "static" / "icons" / "origin.png"),
        "--input",
        "-i",
        help="Pfad zum Ausgangsbild fuer die Icon-Generierung.",
    ),
):
    """Generiert Favicons und PWA-Icons."""
    input_path = Path(input_image).expanduser().resolve()
    output_dir = config.PROJECT_ROOT / "engine" / "web" / "static" / "icons"

    if not input_path.is_file():
        typer.echo(f"Eingabebild nicht gefunden: {input_path}")
        raise typer.Exit(code=1)

    typer.echo("→ Generiere Icons...")

    output_dir.mkdir(parents=True, exist_ok=True)

    source = Image.open(input_path).convert("RGBA")
    base = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    x = (1024 - source.width) // 2
    y = (1024 - source.height) // 2
    base.paste(source, (x, y), source)

    base_path = output_dir / "base.png"
    base.save(base_path, format="PNG")

    base.resize((192, 192), Image.Resampling.LANCZOS).save(output_dir / "icon-192.png", format="PNG")
    base.resize((512, 512), Image.Resampling.LANCZOS).save(output_dir / "icon-512.png", format="PNG")
    base.resize((180, 180), Image.Resampling.LANCZOS).save(output_dir / "apple-touch-icon.png", format="PNG")
    base.resize((32, 32), Image.Resampling.LANCZOS).save(output_dir / "favicon-32x32.png", format="PNG")
    base.resize((16, 16), Image.Resampling.LANCZOS).save(output_dir / "favicon-16x16.png", format="PNG")
    base.save(output_dir / "favicon.ico", format="ICO", sizes=[(64, 64), (48, 48), (32, 32), (16, 16)])

    typer.echo("Icons erfolgreich generiert.")


if __name__ == "__main__":
    app()
