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
        self._ensure_git_repo()

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

    def _ensure_git_repo(self) -> None:
        """Initialisiert das Git-Repository, falls nicht vorhanden."""
        self._git_dir.mkdir(parents=True, exist_ok=True)

        if (self._git_dir / ".git").exists():
            return

        try:
            subprocess.run(
                ["git", "init"],
                cwd=str(self._git_dir),
                check=True,
                capture_output=True,
                timeout=10,
            )
            logger.info(f"Git-Repository in {self._git_dir} initialisiert")
        except subprocess.CalledProcessError as e:
            error_detail = self._format_process_output(e.stderr)
            raise ValueError(f"Git-Initialisierung fehlgeschlagen: {error_detail}") from e

    def _has_changes(self) -> bool:
        """Prüft, ob es uncommitted changes gibt."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(self._git_dir),
                check=True,
                capture_output=True,
                timeout=10,
                text=True,
            )
            return bool(result.stdout.strip())
        except subprocess.CalledProcessError:
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
            subprocess.run(
                ["git", "add", "-A"],
                cwd=str(self._git_dir),
                check=True,
                capture_output=True,
                timeout=10,
            )
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=str(self._git_dir),
                check=True,
                capture_output=True,
                timeout=10,
                text=True,
            )
            output = result.stdout
            if "[" in output and "]" in output:
                commit_info = output.split("[")[1].split("]")[0]
                commit_hash = commit_info.split()[1] if len(commit_info.split()) > 1 else "unknown"
            else:
                commit_hash = "unknown"

            logger.info(f"Checkpoint erstellt: {message} ({commit_hash})")
            return commit_hash
        except subprocess.CalledProcessError as e:
            stderr = self._format_process_output(e.stderr)
            stdout = self._format_process_output(e.stdout)
            combined_output = "\n".join(part for part in [stderr, stdout] if part)

            if "nothing to commit" in combined_output.lower():
                raise ValueError("Keine Änderungen vorhanden, Checkpoint nicht erstellt") from e

            raise ValueError(f"Commit fehlgeschlagen: {combined_output}") from e

    def save_checkpoint(self, label: str | None = None) -> str:
        """Speichert einen Checkpoint für den aktiven Spielstand."""
        if not self._has_changes():
            raise ValueError("Keine Änderungen vorhanden, Checkpoint nicht erstellt")

        message = label if label else self._generate_checkpoint_summary()
        return self._git_add_and_commit(message)

    def list_checkpoints(self) -> list[Checkpoint]:
        """Listet alle verfügbaren Checkpoints auf."""
        try:
            result = subprocess.run(
                ["git", "log", "--pretty=format:%H%n%ai%n%s"],
                cwd=str(self._git_dir),
                check=True,
                capture_output=True,
                timeout=10,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            logger.warning(f"Git-Log abfrage fehlgeschlagen: {e.stderr}")
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
        if self._has_changes():
            logger.info("Änderungen vorhanden, erstelle Auto-Backup...")
            try:
                self._git_add_and_commit(self._generate_checkpoint_summary() + " [auto-backup]")
            except ValueError as e:
                logger.warning(f"Auto-Backup fehlgeschlagen: {e}")

        try:
            result = subprocess.run(
                ["git", "log", "-1", "--pretty=format:%ai%n%s", commit_hash],
                cwd=str(self._git_dir),
                check=True,
                capture_output=True,
                timeout=10,
                text=True,
            )
            lines = result.stdout.strip().split("\n")
            commit_datetime = lines[0] if lines else ""
            commit_orig_message = lines[1] if len(lines) > 1 else ""
        except subprocess.CalledProcessError:
            commit_datetime = "unknown"
            commit_orig_message = "unknown"

        try:
            subprocess.run(
                ["git", "checkout", commit_hash, "--", "."],
                cwd=str(self._git_dir),
                check=True,
                capture_output=True,
                timeout=10,
            )

            if not self._has_changes():
                logger.info(f"Checkout von {commit_hash} ohne Änderungen – kein Revert-Commit nötig")
                return

            self._git_add_and_commit(f"[revert to] {commit_datetime} - {commit_orig_message}")
            logger.info(f"Checkpoint wiederhergestellt: {commit_hash}")
        except subprocess.CalledProcessError as e:
            error_detail = self._format_process_output(e.stderr)
            raise ValueError(f"Checkpoint-Wiederherstellung fehlgeschlagen: {error_detail}") from e
