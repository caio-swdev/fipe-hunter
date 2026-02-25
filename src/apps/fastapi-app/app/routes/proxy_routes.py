"""
Proxy Routes

Server-side proxy for external images to bypass CDN hotlink protection.
"""
import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response


router = APIRouter(prefix="/proxy", tags=["proxy"])


@router.get("/image")
async def proxy_image(url: str = Query(..., description="External image URL to proxy")):
    """
    Proxy an external image through the server.

    Needed for marketplace CDNs (e.g. WebMotors) that block cross-origin requests.
    Adds a spoofed Referer so the CDN accepts the request.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(
                url,
                headers={
                    "Referer": "https://www.webmotors.com.br/",
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                },
            )
        if resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Image not found")
        content_type = resp.headers.get("content-type", "image/jpeg")
        return Response(
            content=resp.content,
            media_type=content_type,
            headers={"Cache-Control": "public, max-age=86400"},
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to fetch image")
