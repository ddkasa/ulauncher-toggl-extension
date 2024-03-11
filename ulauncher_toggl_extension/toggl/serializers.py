from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from typing import Any

from .dataclasses import TogglTracker, TProject


class CustomSerializer(json.JSONEncoder):
    def encode(self, obj: Any) -> str:
        if isinstance(obj, list):
            new_obj = []
            for item in obj:
                if isinstance(item, (TProject, TogglTracker)):
                    name = type(item).__name__
                    item = asdict(item)
                    item["data type"] = name
                new_obj.append(item)

            return super().encode(new_obj)
        return super().encode(obj)

    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class CustomDeserializer(json.JSONDecoder):
    def decode(self, obj: Any, **kwargs) -> Any:  # type: ignore[override]
        obj = super().decode(obj, **kwargs)

        decoded_obj: list[Any] = []
        for item in obj:
            if isinstance(item, dict):
                dt = item.get("data type")
                if dt is not None:
                    item.pop("data type")
                    if dt == "TProject":
                        item = TProject(**item)
                    elif dt == "TogglTracker":
                        item = TogglTracker(**item)

            elif isinstance(item, str):
                item = datetime.fromisoformat(item)
                decoded_obj.insert(0, item)
                continue

            decoded_obj.append(item)

        return decoded_obj


__all__ = (
    "CustomSerializer",
    "CustomDeserializer",
    "TProject",
    "TogglTracker",
)
