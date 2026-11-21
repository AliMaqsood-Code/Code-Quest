from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for,
)
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from app import db
from app.forms.auth import LoginForm, RegisterForm
from app.models import NotificationPreference, Role, User, UserProfile
from app.utils.auth import (
    end_session, log_action, login_required, start_session,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def safe_next(target):
    """Only allow redirects to paths on this site."""
    if (target and target.startswith("/")
            and not target.startswith("//") and "\\" not in target):
        return target
    return url_for("main.index")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if g.current_user:
        return redirect(url_for("main.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
        )
        user.set_password(form.password.data)
        user.roles = [Role.query.filter_by(role_name="user").one()]
        user.profile = UserProfile(display_name=user.username)
        user.notification_preferences = NotificationPreference()
        db.session.add(user)

        try:
            db.session.flush()
            log_action("user.register", "user", user.user_id, user.user_id)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Username or email is already in use.", "danger")
            return render_template("auth/register.html", form=form)

        flash("Account created. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.current_user:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.identifier.data.strip()
        user = User.query.filter(
            or_(User.username == identifier, User.email == identifier.lower())
        ).first()

        if user is None or not user.check_password(form.password.data):
            flash("Invalid username/email or password.", "danger")
        elif not user.is_active:
            flash("This account is deactivated.", "danger")
        else:
            start_session(user)
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(safe_next(request.args.get("next")))

    return render_template("auth/login.html", form=form)


@auth_bp.post("/logout")
@login_required
def logout():
    end_session()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))