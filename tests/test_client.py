import httpx
from cryptoix import CryptoixClient, CryptoixAPIError


def test_auth_header_and_success_envelope():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer ak_live_xxxxxxxxxxxx"
        return httpx.Response(200, json={"ok": True, "data": {"hello": "world"}, "meta": {"request_id": "req_1"}})

    client = CryptoixClient(api_key="ak_live_xxxxxxxxxxxx", base_url="https://api.test/v1", client=httpx.Client(transport=httpx.MockTransport(handler)))
    assert client.list_balances() == {"hello": "world"}


def test_api_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"ok": False, "error": {"code": "missing_scope", "message": "Nope", "request_id": "req_2"}})

    client = CryptoixClient(api_key="ak_live_xxxxxxxxxxxx", base_url="https://api.test/v1", client=httpx.Client(transport=httpx.MockTransport(handler)))
    try:
        client.list_balances()
    except CryptoixAPIError as exc:
        assert exc.code == "missing_scope"
        assert exc.request_id == "req_2"
    else:
        raise AssertionError("expected CryptoixAPIError")
