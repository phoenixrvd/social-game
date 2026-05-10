from pathlib import Path
import subprocess
import tempfile

import typer
from PIL import Image

from engine.config import config
from engine.storage import storage

app = typer.Typer(
    no_args_is_help=True,
    help="Tools für Social Game.",
)


@app.callback()
def main() -> None:
    """Hilft beim Starten und Pruefen der wichtigsten Social-Game-Funktionen."""


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


def _npc_video_paths() -> list[Path]:
    return sorted(npc.video.get() for npc in storage.list_npcs if npc.video.is_file())


def _remove_audio_track(video_path: Path) -> None:
    with tempfile.NamedTemporaryFile(dir=video_path.parent, suffix=".mp4", delete=False) as temp_file:
        output_path = Path(temp_file.name)

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(video_path), "-an", "-c:v", "copy", str(output_path)],
            check=True,
        )
        output_path.replace(video_path)
    finally:
        if output_path.exists():
            output_path.unlink()


@app.command("npc-videos-strip-audio")
def npc_videos_strip_audio():
    """Entfernt Audiospuren aus allen NPC-Videos."""
    video_paths = _npc_video_paths()
    try:
        for video_path in video_paths:
            typer.echo(f"→ Entferne Audio: {video_path.relative_to(config.PROJECT_ROOT)}")
            _remove_audio_track(video_path)
    except FileNotFoundError:
        typer.echo("ffmpeg nicht gefunden. Bitte ffmpeg installieren und erneut ausfuehren.")
        raise typer.Exit(code=1)

    typer.echo(f"Audiospuren aus {len(video_paths)} NPC-Video(s) entfernt.")


if __name__ == "__main__":
    app()
