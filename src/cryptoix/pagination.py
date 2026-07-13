from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class Pagination:
    page: int = 1
    per_page: int = 25

    def to_params(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {"page": self.page, "per_page": self.per_page}
        if extra:
            params.update({k: v for k, v in extra.items() if v is not None})
        return params
