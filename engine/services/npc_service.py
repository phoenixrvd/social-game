from pathlib import Path

import yaml

from engine.config import config
from engine.services.id_normalizer import normalize_to_snake_id


class NpcService:
    @staticmethod
    def _normalize_id(npc_name: str) -> tuple[str, str]:
        cleaned_name = npc_name.strip()
        npc_id = normalize_to_snake_id(cleaned_name)
        if not npc_id:
            raise ValueError("NPC-Name ergibt keine gueltige ID.")
        return cleaned_name, npc_id

    def create_override(self, npc_name: str) -> Path:
        cleaned_name, npc_id = self._normalize_id(npc_name)
        target_dir = config.OVERRIDES_NPC_DIR / npc_id

        if target_dir.is_dir():
            return target_dir

        target_dir.mkdir(parents=True, exist_ok=False)
        payload = yaml.safe_dump({"name": cleaned_name}, allow_unicode=True, sort_keys=False)
        (target_dir / "character.yaml").write_text(payload, encoding="utf-8")
        return target_dir

