from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from engine.client import client
from engine.logger import logger
from engine.storage import storage


@dataclass
class Checkpoint:
    """Repräsentation eines Spielstand-Checkpoints."""
    commit_hash: str
    commit_date: datetime
    commit_message: str


class HistoryService:
    """Verwaltung von Git-basierten Spielstand-Checkpoints."""

    def __init__(self) -> None:
        self._git_dir = storage.npc.base_runtime

    @staticmethod
    def _format_process_output(output: str | bytes | None) -> str:
        if output is None:
            return ""
        if isinstance(output, bytes):
            return output.decode("utf-8", errors="replace").strip()
        return output.strip()

    @staticmethod
    def _parse_git_datetime(value: str) -> datetime:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S %z")

    def _run_git(self, *args: str, text: bool = True) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                ["git", *args],
                cwd=str(self._git_dir),
                check=True,
                capture_output=True,
                timeout=10,
                text=text,
            )
        except subprocess.CalledProcessError as e:
            stderr = self._format_process_output(e.stderr)
            stdout = self._format_process_output(e.stdout)
            combined_output = "\n".join(part for part in [stderr, stdout] if part)
            raise ValueError(combined_output or str(e)) from e
        except OSError as e:
            raise ValueError(str(e)) from e

    def _ensure_git_repo(self) -> None:
        """Initialisiert das Git-Repository, falls nicht vorhanden."""
        try:
            self._git_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ValueError(f"Checkpoint-Speicher ist nicht verfügbar: {e}") from e

        if (self._git_dir / ".git").exists():
            return

        try:
            self._run_git("init")
            logger.info(f"Git-Repository in {self._git_dir} initialisiert")
        except ValueError as e:
            raise ValueError(f"Git-Initialisierung fehlgeschlagen: {e}") from e

    def _has_changes(self) -> bool:
        """Prüft, ob es uncommitted changes gibt."""
        try:
            result = self._run_git("status", "--porcelain")
            return bool(result.stdout.strip())
        except ValueError:
            return False

    def _generate_checkpoint_summary(self) -> str:
        """Generiert eine Kurzfassung (max 10 Wörter) aus dem aktuellen STM-Text mit dem LLM."""
        last_message = storage.npc.stm.text_latest.strip()

        if not last_message or last_message == "(keine Nachrichten)":
            return "Spielstand"

        prompt_template = Path(__file__).resolve().parents[2] / "prompts" / "checkpoint_summary.md"
        prompt = prompt_template.read_text(encoding="utf-8").replace("{{MESSAGE}}", last_message)

        try:
            summary = client.run_prompt_small(prompt)
            if len(summary) > 100:
                summary = summary[:97] + "..."
            return summary.strip()
        except Exception as e:
            logger.warning(f"Checkpoint-Zusammenfassung fehlgeschlagen: {e}")
            return (last_message[:30] + "...") if len(last_message) > 30 else last_message

    def _git_add_and_commit(self, message: str) -> str:
        """Staged alle Änderungen und erstellt einen Commit."""
        try:
            self._run_git("add", "-A")
            result = self._run_git("commit", "-m", message)
            output = result.stdout
            if "[" in output and "]" in output:
                commit_info = output.split("[")[1].split("]")[0]
                commit_hash = commit_info.split()[1] if len(commit_info.split()) > 1 else "unknown"
            else:
                commit_hash = "unknown"

            logger.info(f"Checkpoint erstellt: {message} ({commit_hash})")
            return commit_hash
        except ValueError as e:
            if "nothing to commit" in str(e).lower():
                raise ValueError("Keine Änderungen vorhanden, Checkpoint nicht erstellt") from e

            raise ValueError(f"Commit fehlgeschlagen: {e}") from e

    def save_checkpoint(self, label: str | None = None) -> str:
        """Speichert einen Checkpoint für den aktiven Spielstand."""
        self._ensure_git_repo()

        if not self._has_changes():
            raise ValueError("Keine Änderungen vorhanden, Checkpoint nicht erstellt")

        message = label if label else self._generate_checkpoint_summary()
        return self._git_add_and_commit(message)

    def list_checkpoints(self) -> list[Checkpoint]:
        """Listet alle verfügbaren Checkpoints auf."""
        try:
            self._ensure_git_repo()
        except ValueError as e:
            logger.warning(f"Checkpoint-Liste nicht verfügbar: {e}")
            return []

        try:
            result = self._run_git("log", "--pretty=format:%H%n%ai%n%s")
        except ValueError as e:
            logger.warning(f"Git-Log abfrage fehlgeschlagen: {e}")
            return []

        if not result.stdout.strip():
            return []

        checkpoints = []
        lines = result.stdout.strip().split("\n")

        i = 0
        while i + 2 < len(lines):
            commit_message = lines[i + 2].strip()
            checkpoints.append(
                Checkpoint(
                    commit_hash=lines[i].strip(),
                    commit_date=self._parse_git_datetime(lines[i + 1].strip()),
                    commit_message=commit_message,
                )
            )
            i += 3

        return checkpoints

    def restore_checkpoint(self, commit_hash: str) -> None:
        """Stellt einen älteren Spielstand wieder her."""
        self._ensure_git_repo()

        if self._has_changes():
            logger.info("Änderungen vorhanden, erstelle Auto-Backup...")
            try:
                self._git_add_and_commit(self._generate_checkpoint_summary() + " [auto-backup]")
            except ValueError as e:
                logger.warning(f"Auto-Backup fehlgeschlagen: {e}")

        try:
            result = self._run_git("log", "-1", "--pretty=format:%ai%n%s", commit_hash)
            lines = result.stdout.strip().split("\n")
            commit_datetime = lines[0] if lines else ""
            commit_orig_message = lines[1] if len(lines) > 1 else ""
        except ValueError:
            commit_datetime = "unknown"
            commit_orig_message = "unknown"

        try:
            self._run_git("checkout", commit_hash, "--", ".")

            if not self._has_changes():
                logger.info(f"Checkout von {commit_hash} ohne Änderungen – kein Revert-Commit nötig")
                return

            self._git_add_and_commit(f"[revert to] {commit_datetime} - {commit_orig_message}")
            logger.info(f"Checkpoint wiederhergestellt: {commit_hash}")
        except ValueError as e:
            raise ValueError(f"Checkpoint-Wiederherstellung fehlgeschlagen: {e}") from e
