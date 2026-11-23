from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for,
)

from app import db
from app.forms.engagement import PreferencesForm
from app.models import Notification, NotificationPreference
from app.models.user_models import utc_now
from app.utils.auth import login_required

notifications_bp = Blueprint("notifications", __name__,
                             url_prefix="/notifications")


def _mine(notification_id):
    from flask import abort
    notification = db.get_or_404(Notification, notification_id)
    if notification.user_id != g.current_user.user_id:
        abort(404)
    return notification


def _unread(user_id):
    return Notification.query.filter_by(user_id=user_id, read_at=None)


@notifications_bp.get("/")
@login_required
def index():
    uid = g.current_user.user_id
    query = Notification.query.filter_by(user_id=uid)
    if request.args.get("unread"):
        query = query.filter(Notification.read_at.is_(None))

    return render_template(
        "notifications/list.html",
        notifications=query.order_by(Notification.created_at.desc())
        .limit(100).all(),
        unread_count=_unread(uid).count(),
    )


@notifications_bp.post("/<int:notification_id>/read")
@login_required
def mark_read(notification_id):
    notification = _mine(notification_id)
    if notification.read_at is None:
        notification.read_at = utc_now()
        db.session.commit()

    target = notification.related_url or ""
    if target.startswith("/") and not target.startswith("//") \
            and "\\" not in target:
        return redirect(target)
    return redirect(url_for("notifications.index"))


@notifications_bp.post("/read-all")
@login_required
def mark_all_read():
    _unread(g.current_user.user_id).update({"read_at": utc_now()})
    db.session.commit()

    flash("All notifications marked as read.", "info")
    return redirect(url_for("notifications.index"))


@notifications_bp.post("/<int:notification_id>/delete")
@login_required
def delete(notification_id):
    db.session.delete(_mine(notification_id))
    db.session.commit()

    flash("Notification deleted.", "info")
    return redirect(url_for("notifications.index"))


@notifications_bp.route("/preferences", methods=["GET", "POST"])
@login_required
def preferences():
    user = g.current_user
    prefs = user.notification_preferences
    if prefs is None:
        prefs = NotificationPreference(user_id=user.user_id)
        db.session.add(prefs)
        db.session.commit()

    form = PreferencesForm(obj=prefs)
    if form.validate_on_submit():
        prefs.email_enabled = form.email_enabled.data
        prefs.contest_alerts = form.contest_alerts.data
        prefs.submission_alerts = form.submission_alerts.data
        prefs.discussion_alerts = form.discussion_alerts.data
        db.session.commit()

        flash("Preferences saved.", "success")
        return redirect(url_for("notifications.preferences"))

    return render_template("notifications/preferences.html", form=form)