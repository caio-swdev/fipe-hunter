"""
Session Middleware

Assigns an anonymous session_id cookie to every browser that doesn't have one.
Injects request.state.session_id for downstream route handlers.

Cookie settings:
  - HttpOnly: JS cannot read it (XSS protection)
  - SameSite=Lax: Sent on same-site navigation, not on cross-site POSTs
  - max_age=31536000: 1-year TTL (persistent session)

last_seen_at is only updated when > 5 minutes old to avoid a DB write on
every request under SQLite's global write lock.
"""
import uuid
from datetime import datetime, timedelta

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy.exc import IntegrityError

from fipe_infra.database.session import SessionLocal
from fipe_infra.database.models import SessionModel

_UPDATE_COOLDOWN = timedelta(minutes=5)


class SessionMiddleware(BaseHTTPMiddleware):
    """Manages anonymous HttpOnly cookie sessions."""

    async def dispatch(self, request: Request, call_next) -> Response:
        session_id = request.cookies.get("session_id")
        new_session = False

        if not session_id:
            session_id = str(uuid.uuid4())
            new_session = True
            self._create_session(session_id, request)
        else:
            self._touch_session(session_id)

        request.state.session_id = session_id
        response: Response = await call_next(request)

        if new_session:
            response.set_cookie(
                key="session_id",
                value=session_id,
                max_age=31536000,
                httponly=True,
                samesite="lax",
            )

        return response

    def _create_session(self, session_id: str, request: Request) -> None:
        ip = request.client.host if request.client else None
        db = SessionLocal()
        try:
            row = SessionModel(session_id=session_id, ip_address=ip)
            db.add(row)
            db.commit()
        except IntegrityError:
            db.rollback()
        finally:
            db.close()

    def _touch_session(self, session_id: str) -> None:
        db = SessionLocal()
        try:
            row = db.query(SessionModel).filter_by(session_id=session_id).first()
            if row and (datetime.utcnow() - row.last_seen_at) > _UPDATE_COOLDOWN:
                row.last_seen_at = datetime.utcnow()
                db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
