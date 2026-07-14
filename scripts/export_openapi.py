from __future__ import annotations

import json

from engine.api.app import app


print(json.dumps(app.openapi()))
