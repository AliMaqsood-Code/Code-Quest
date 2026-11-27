from datetime import timedelta
from functools import wraps

from flask import abort, flash, g, redirect, request, session, url_for

from app import db
from app.models import AuditLog, UserSession
from app.models.user_models import utc_now
from app.utils.tokenManagement import generate_token, hash_token
from app.models import AuditLog, Notification, UserSession

SESSION_DAYS = 7


def log_action(action, entity_type, entity_id=None, actor_id=None):
    db.session.add(AuditLog(
        actor_user_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=request.remote_addr,
    ))


def init_auth(app):
    """Load the logged-in user on every request and expose it to templates."""

    @app.before_request
    def load_current_user():
        g.current_user = None
        g.session = None

        token = session.get("token")
        if not token:
            return

        record = UserSession.query.filter(
            UserSession.token_hash == hash_token(token),
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > utc_now(),
        ).first()

        if record is None or not record.user.is_active:
            session.pop("token", None)
            return

        g.session = record
        g.current_user = record.user

    @app.context_processor
    def inject_current_user():
        user = g.get("current_user")
        nav_unread = 0
        if user is not None:
            nav_unread = Notification.query.filter(
                Notification.user_id == user.user_id,
                Notification.read_at.is_(None),
            ).count()
        return {"current_user": user, "nav_unread": nav_unread}


def start_session(user):
    raw_token, token_hash = generate_token()
    now = utc_now()
    db.session.add(UserSession(
        user_id=user.user_id,
        token_hash=token_hash,
        created_at=now,
        expires_at=now + timedelta(days=SESSION_DAYS),
    ))
    log_action("user.login", "user", user.user_id, user.user_id)
    db.session.commit()

    session.clear()               # drop any old session data
    session["token"] = raw_token
    session.permanent = True


def end_session():
    if g.get("session") is not None:
        g.session.revoke()
        log_action("user.logout", "user", g.current_user.user_id,
                   g.current_user.user_id)
        db.session.commit()
    session.clear()


def _to_login():
    flash("Please log in to continue.", "warning")
    next_url = request.path if request.method == "GET" else None
    return redirect(url_for("auth.login", next=next_url))


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if g.current_user is None:
            return _to_login()
        return view(*args, **kwargs)
    return wrapper


def permission_required(permission_key):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if g.current_user is None:
                return _to_login()
            if not g.current_user.has_permission(permission_key):
                abort(403)
            return view(*args, **kwargs)
        return wrapper
    return decorator