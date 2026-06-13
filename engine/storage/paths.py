from __future__ import annotations

from pathlib import Path

from engine.config import config


class PathResolver:
    def runtime_npc_scene_dir(self, npc_id: str, scene_id: str) -> Path:
        return config.DATA_NPC_DIR / npc_id / scene_id

    def ordered_unique_paths(self, *paths: Path) -> tuple[Path, ...]:
        ordered: list[Path] = []
        for path in paths:
            if path in ordered:
                continue
            ordered.append(path)
        return tuple(ordered)

    def candidate_paths(
        self,
        *,
        override_path: Path,
        default_path: Path,
        runtime_path: Path | None = None,
        fallback_path: Path | None = None,
    ) -> tuple[Path, ...]:
        paths: list[Path] = []
        if runtime_path is not None:
            paths.append(runtime_path)
        paths.extend([override_path, default_path])
        if fallback_path is not None:
            paths.append(fallback_path)
        return self.ordered_unique_paths(*paths)

    def prompt_file(self, filename: str) -> Path:
        return self.preferred_file((
            config.OVERRIDES_PROMPTS_DIR / filename,
            config.PROJECT_ROOT / "prompts" / filename,
        ))

    def npc_original_file(self, npc_id: str, filename: str) -> Path:
        return self.preferred_file(
            self.candidate_paths(
                override_path=config.OVERRIDES_NPC_DIR / npc_id / filename,
                default_path=config.NPC_DIR / npc_id / filename,
                fallback_path=config.NPC_DIR / config.DEFAULT_NPC_ID / filename,
            )
        )

    def npc_file(self, npc_id: str, scene_id: str, filename: str) -> Path:
        return self.preferred_file(
            self.candidate_paths(
                runtime_path=self.runtime_npc_scene_dir(npc_id, scene_id) / filename,
                override_path=config.OVERRIDES_NPC_DIR / npc_id / filename,
                default_path=config.NPC_DIR / npc_id / filename,
                fallback_path=config.NPC_DIR / config.DEFAULT_NPC_ID / filename,
            )
        )

    def avatar_file(self, avatar_id: str, filename: str) -> Path:
        return self.preferred_file(
            self.ordered_unique_paths(
                config.OVERRIDES_AVATAR_DIR / avatar_id / filename,
                config.AVATAR_DIR / avatar_id / filename,
            )
        )

    def user_profile_candidates(self, npc_id: str, scene_id: str) -> tuple[Path, ...]:
        """Return candidates for user profile with priority: runtime-active > overrides > default."""
        filename = "user_profile.md"
        runtime_path = self.runtime_npc_scene_dir(npc_id, scene_id) / filename
        override_path = config.OVERRIDES_NPC_DIR / filename
        default_path = config.NPC_DIR / filename
        return self.ordered_unique_paths(runtime_path, override_path, default_path)

    def npc_scene_original_file(self, npc_id: str, scene_id: str, filename: str) -> Path:
        npc_base = config.NPC_DIR / npc_id
        npc_override_base = config.OVERRIDES_NPC_DIR / npc_id
        npc_default_base = config.NPC_DIR / config.DEFAULT_NPC_ID
        return self.preferred_file(
            self.ordered_unique_paths(
                npc_override_base / filename,
                npc_override_base / "scenes" / scene_id / filename,
                npc_base / "scenes" / scene_id / filename,
                npc_base / filename,
                npc_default_base / "scenes" / scene_id / filename,
                npc_default_base / filename,
            )
        )

    def scene_file_candidates(self, scene_id: str, filename: str) -> tuple[Path, ...]:
        return self.candidate_paths(
            override_path=config.OVERRIDES_SCENE_DIR / scene_id / filename,
            default_path=config.SCENE_DIR / scene_id / filename,
            fallback_path=config.SCENE_DIR / config.DEFAULT_SCENE_ID / filename,
        )

    def scene_original_file(self, scene_id: str, filename: str) -> Path:
        return self.preferred_file(self.scene_file_candidates(scene_id, filename))

    def scene_file(self, npc_id: str, scene_id: str, filename: str) -> Path:
        return self.preferred_file(
            self.candidate_paths(
                runtime_path=self.runtime_npc_scene_dir(npc_id, scene_id) / filename,
                override_path=config.OVERRIDES_SCENE_DIR / scene_id / filename,
                default_path=config.SCENE_DIR / scene_id / filename,
                fallback_path=config.SCENE_DIR / config.DEFAULT_SCENE_ID / filename,
            )
        )

    @staticmethod
    def first_existing_file(candidates: tuple[Path, ...]) -> Path | None:
        for path in candidates:
            if path.is_file():
                return path
        return None

    def preferred_file(self, candidates: tuple[Path, ...]) -> Path:
        return self.first_existing_file(candidates) or candidates[-1]

    @staticmethod
    def npc_exists(npc_id: str) -> bool:
        return (config.OVERRIDES_NPC_DIR / npc_id).is_dir() or (config.NPC_DIR / npc_id).is_dir()

    @staticmethod
    def scene_exists(scene_id: str) -> bool:
        return (config.OVERRIDES_SCENE_DIR / scene_id).is_dir() or (config.SCENE_DIR / scene_id).is_dir()

    @staticmethod
    def avatar_exists(avatar_id: str) -> bool:
        return (config.OVERRIDES_AVATAR_DIR / avatar_id).is_dir() or (config.AVATAR_DIR / avatar_id).is_dir()

    @staticmethod
    def _collect_dir_ids(*roots: Path) -> list[str]:
        ids: set[str] = set()
        for root in roots:
            if not root.exists():
                continue
            ids.update(entry.name for entry in root.iterdir() if entry.is_dir())
        return sorted(ids)

    def list_npc_ids(self) -> list[str]:
        return self._collect_dir_ids(config.OVERRIDES_NPC_DIR, config.NPC_DIR)

    def list_avatar_ids(self) -> list[str]:
        return self._collect_dir_ids(config.OVERRIDES_AVATAR_DIR, config.AVATAR_DIR)

    def list_scene_ids(self) -> list[str]:
        return self._collect_dir_ids(config.OVERRIDES_SCENE_DIR, config.SCENE_DIR)


path_resolver = PathResolver()
