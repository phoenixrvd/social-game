from pathlib import Path

import typer
from PIL import Image

from engine.config import config
from engine.llm.client import hello_llm
from engine.services.character_image_service import CharacterImageService
from engine.stores.session_store import SessionStore
from engine.updater.schedule import AVAILABLE_UPDATERS, UPDATER_CLASSES
from engine.updater.updater import AbstractUpdater

app = typer.Typer(
    no_args_is_help=True,
    help="Werkzeuge fuer Web-GUI, Session, Updater und LLM-Pruefung im Social Game.",
)
def resolve_updater(updater_name: str) -> AbstractUpdater:
    key = updater_name.strip().lower()
    updater_cls = dict(UPDATER_CLASSES).get(key)
    if updater_cls is not None:
        return updater_cls()

    raise typer.BadParameter(f"Unbekannter Updater '{updater_name}'. Verfuegbar: {AVAILABLE_UPDATERS}")


def _character_image_service() -> CharacterImageService:
    return CharacterImageService()


@app.callback()
def main() -> None:
    """Hilft beim Starten und Pruefen der wichtigsten Social-Game-Funktionen."""


@app.command("session-set")
def set_session_context(
    npc: str | None = typer.Option(
        None,
        "--npc",
        help="ID des NPCs fuer den globalen Session-Kontext.",
    ),
    scene: str | None = typer.Option(
        None,
        "--scene",
        help="ID der Szene fuer den globalen Session-Kontext.",
    ),
):
    """Setzt den globalen Session-Kontext und speichert ihn in .data/session.yaml."""
    if npc is None and scene is None:
        typer.echo("Mindestens --npc oder --scene muss angegeben werden.")
        raise typer.Exit(code=1)

    saved = SessionStore().save(npc=npc, scene=scene)
    typer.echo("Session-Kontext gespeichert.")
    typer.echo(f"npc={saved.npc_id}")
    typer.echo(f"scene={saved.scene_id}")


@app.command()
def hello():
    """Prueft, ob die CLI grundsaetzlich laeuft."""
    typer.echo("Hello from Social Game CLI")


@app.command("hallo-llm")
def hallo_llm():
    """Prueft die Verbindung zum Sprachmodell."""
    answer = hello_llm()
    typer.echo(answer)


@app.command("web")
def web(
    host: str = typer.Option("127.0.0.1", "--host", help="Host fuer die Web-GUI."),
    port: int = typer.Option(8000, "--port", help="Port fuer die Web-GUI."),
    reload: bool = typer.Option(False, "--reload", help="Auto-Reload fuer Entwicklung aktivieren."),
):
    """Startet die browserbasierte GUI."""
    from engine.web.app import run as run_web

    run_web(host=host, port=port, reload=reload)


@app.command("image-revert")
def image_revert():
    """Setzt das Charakterbild auf das letzte Backup zurueck."""
    _character_image_service().revert()


@app.command("image-merge-scene")
def image_merge_scene() -> None:
    """Fuegt aktives Charakterbild und Szenenbild zu einem neuen Laufzeitbild zusammen."""
    _character_image_service().merge_with_scene()


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


@app.command("update")
def update(
    updatername: str = typer.Argument(
        ...,
        help=f"Name des Updaters. Verfuegbar: {AVAILABLE_UPDATERS}.",
    ),
):
    """Fuehrt den gewaehlten Updater einmal ueber `schedule()` aus."""
    updater = resolve_updater(updatername)
    updater.schedule()


if __name__ == "__main__":
    app()
