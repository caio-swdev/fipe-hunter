"""
API Tests: GET /api/proxy/image

Tests the server-side image proxy that bypasses CDN hotlink protection
for external marketplace images (WebMotors, OLX, etc.).
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import httpx


@pytest.fixture(scope="module")
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c


def _make_httpx_response(status_code: int, content: bytes = b"", content_type: str = "image/jpeg"):
    """Build a minimal httpx.Response for mocking."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.content = content
    resp.headers = {"content-type": content_type}
    return resp


class TestProxyImageRoute:
    """Test suite for GET /api/proxy/image."""

    def test_proxy_returns_image_on_success(self, client):
        """
        Happy path: upstream CDN returns 200 → proxy forwards bytes and headers.
        """
        fake_image = b"\xff\xd8\xff\xe0" + b"\x00" * 100  # minimal JPEG magic bytes
        mock_resp = _make_httpx_response(200, content=fake_image, content_type="image/jpeg")

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)

        with patch("app.routes.proxy_routes.httpx.AsyncClient", return_value=mock_client):
            response = client.get(
                "/api/proxy/image",
                params={"url": "https://cdn.webmotors.com.br/fake/car.jpg"},
            )

        assert response.status_code == 200
        assert response.content == fake_image
        assert "image" in response.headers["content-type"]

    def test_proxy_sets_cache_control_header(self, client):
        """
        Proxy response must include Cache-Control: public, max-age=86400.
        """
        mock_resp = _make_httpx_response(200, content=b"img", content_type="image/webp")

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)

        with patch("app.routes.proxy_routes.httpx.AsyncClient", return_value=mock_client):
            response = client.get(
                "/api/proxy/image",
                params={"url": "https://cdn.webmotors.com.br/fake/car.webp"},
            )

        assert response.status_code == 200
        assert "max-age=86400" in response.headers.get("cache-control", "")

    def test_proxy_forwards_content_type_from_upstream(self, client):
        """
        content-type from upstream CDN is forwarded as-is (jpeg, webp, png).
        """
        for ct in ["image/webp", "image/png", "image/jpeg"]:
            mock_resp = _make_httpx_response(200, content=b"img", content_type=ct)

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_resp)

            with patch("app.routes.proxy_routes.httpx.AsyncClient", return_value=mock_client):
                response = client.get(
                    "/api/proxy/image",
                    params={"url": "https://cdn.webmotors.com.br/fake/car.img"},
                )

            assert response.status_code == 200
            assert response.headers["content-type"].startswith(ct)

    def test_proxy_returns_404_when_upstream_not_found(self, client):
        """
        Upstream 404 → proxy returns 404 with detail 'Image not found'.
        """
        mock_resp = _make_httpx_response(404)

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)

        with patch("app.routes.proxy_routes.httpx.AsyncClient", return_value=mock_client):
            response = client.get(
                "/api/proxy/image",
                params={"url": "https://cdn.webmotors.com.br/nonexistent.jpg"},
            )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_proxy_returns_404_when_upstream_returns_403(self, client):
        """
        Upstream 403 (hotlink blocked) → proxy returns 404.
        """
        mock_resp = _make_httpx_response(403)

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)

        with patch("app.routes.proxy_routes.httpx.AsyncClient", return_value=mock_client):
            response = client.get(
                "/api/proxy/image",
                params={"url": "https://cdn.webmotors.com.br/hotlink-blocked.jpg"},
            )

        assert response.status_code == 404

    def test_proxy_returns_502_on_network_error(self, client):
        """
        Network error (timeout, DNS failure) → proxy returns 502.
        """
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("DNS failed"))

        with patch("app.routes.proxy_routes.httpx.AsyncClient", return_value=mock_client):
            response = client.get(
                "/api/proxy/image",
                params={"url": "https://dead-cdn.example.com/car.jpg"},
            )

        assert response.status_code == 502
        assert "fetch" in response.json()["detail"].lower()

    def test_proxy_returns_502_on_timeout(self, client):
        """
        Read timeout → proxy returns 502.
        """
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=httpx.ReadTimeout("timed out"))

        with patch("app.routes.proxy_routes.httpx.AsyncClient", return_value=mock_client):
            response = client.get(
                "/api/proxy/image",
                params={"url": "https://slow-cdn.example.com/car.jpg"},
            )

        assert response.status_code == 502

    def test_proxy_missing_url_param_returns_422(self, client):
        """
        Missing required `url` query param → FastAPI validation returns 422.
        """
        response = client.get("/api/proxy/image")
        assert response.status_code == 422

    def test_proxy_sends_webmotors_referer_header(self, client):
        """
        Outgoing request to CDN must include WebMotors Referer to bypass hotlink protection.
        """
        mock_resp = _make_httpx_response(200, content=b"img")

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)

        with patch("app.routes.proxy_routes.httpx.AsyncClient", return_value=mock_client):
            client.get(
                "/api/proxy/image",
                params={"url": "https://cdn.webmotors.com.br/car.jpg"},
            )

        call_kwargs = mock_client.get.call_args
        headers_sent = call_kwargs.kwargs.get("headers", {})
        assert "webmotors.com.br" in headers_sent.get("Referer", "")
