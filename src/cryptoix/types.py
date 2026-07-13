from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict

AuthMode = Literal["bearer", "x-api-key"]
JsonDict = Dict[str, Any]


class RequestOptions(TypedDict, total=False):
    params: Dict[str, Any]
    headers: Dict[str, str]


class ApiErrorPayload(TypedDict, total=False):
    code: str
    message: str
    details: Dict[str, Any]
    request_id: str


class ApiMeta(TypedDict, total=False):
    request_id: str
    page: int
    per_page: int
    total: int
    total_pages: int


class ApiEnvelope(TypedDict, total=False):
    ok: bool
    data: Any
    meta: ApiMeta
    error: ApiErrorPayload
