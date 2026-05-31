import os
from pathlib import Path
import subprocess
import tempfile
import time

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
    from engine.api.app import run as run_web

    run_web(host=host, port=port, reload=reload)


def _etm_ui_env(host: str, port: int) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "WORKING_DIR": str(storage.npc.etm_dir),
            "HOST": host,
            "PORT": str(port),
            "LLM_BINDING": "openai",
            "EMBEDDING_BINDING": "openai",
            "LLM_BINDING_HOST": config.MODEL_BASE_URL,
            "EMBEDDING_BINDING_HOST": config.MODEL_BASE_URL,
            "LLM_BINDING_API_KEY": config.MODEL_API_KEY,
            "EMBEDDING_BINDING_API_KEY": config.MODEL_API_KEY,
            "LLM_MODEL": config.MODEL_LLM_SMALL,
            "EMBEDDING_MODEL": config.MODEL_EMBEDDING,
            "EMBEDDING_DIM": str(config.MODEL_EMBEDDING_DIMENSIONS),
            "WEBUI_TITLE": f"Social Game ETM: {storage.session.npc_id}/{storage.session.scene_id}",
        }
    )
    return env


def _etm_watch_signature(etm_dir: Path) -> tuple[tuple[str, int, int], ...]:
    tracked = (
        "graph_chunk_entity_relation.graphml",
        "kv_store_text_chunks.json",
        "kv_store_full_docs.json",
        "kv_store_doc_status.json",
        "vdb_chunks.json",
    )
    signature: list[tuple[str, int, int]] = []
    for name in tracked:
        path = etm_dir / name
        if not path.exists():
            signature.append((name, -1, -1))
            continue
        stat = path.stat()
        signature.append((name, int(stat.st_mtime_ns), stat.st_size))
    return tuple(signature)


def _stop_process(process: subprocess.Popen) -> None:
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _run_etm_ui_watch(host: str, port: int, interval_seconds: float) -> None:
    env = _etm_ui_env(host, port)
    baseline = _etm_watch_signature(storage.npc.etm_dir)

    while True:
        process = subprocess.Popen(["lightrag-server"], env=env)
        typer.echo("ETM-UI Watch aktiv. Bei ETM-Indexaenderungen wird der Server neu gestartet.")
        try:
            restarted = _poll_until_change_or_exit(process, interval_seconds, baseline)
        except KeyboardInterrupt:
            if process.poll() is None:
                _stop_process(process)
            raise

        if not restarted:
            if process.returncode == 0:
                return
            raise subprocess.CalledProcessError(process.returncode, ["lightrag-server"])

        baseline = _etm_watch_signature(storage.npc.etm_dir)
        typer.echo("ETM-Indexaenderung erkannt, starte ETM-UI neu...")
        _stop_process(process)


def _poll_until_change_or_exit(
    process: subprocess.Popen,
    interval_seconds: float,
    baseline: tuple,
) -> bool:
    """Wartet bis sich der ETM-Index ändert (True) oder der Prozess beendet (False)."""
    while process.poll() is None:
        time.sleep(interval_seconds)
        current = _etm_watch_signature(storage.npc.etm_dir)
        if current != baseline:
            return True
    return False


@app.command("etm-ui")
def etm_ui(
    host: str = typer.Option("127.0.0.1", "--host", help="Host fuer die LightRAG ETM-UI."),
    port: int = typer.Option(9621, "--port", help="Port fuer die LightRAG ETM-UI."),
    watch: bool = typer.Option(False, "--watch", help="Startet ETM-UI im Watch-Modus mit Auto-Neustart bei ETM-Indexaenderungen."),
    watch_interval_seconds: float = typer.Option(2.0, "--watch-interval", min=0.2, help="Polling-Intervall fuer --watch in Sekunden."),
):
    """Startet die LightRAG-WebUI fuer den aktiven ETM-Kontext."""
    storage.npc.etm_dir.mkdir(parents=True, exist_ok=True)
    typer.echo(f"ETM-UI: http://{host}:{port}")
    typer.echo(f"ETM-Daten: {storage.npc.etm_dir}")
    if watch:
        _run_etm_ui_watch(host, port, watch_interval_seconds)
        return
    subprocess.run(["lightrag-server"], check=True, env=_etm_ui_env(host, port))


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
    return sorted(video.get() for npc in storage.list_npcs for video in npc.video_candidates if video.is_file())


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
