from flask import (
    Blueprint, abort, flash, g, redirect, render_template, url_for,
)

from app import db
from app.forms.profile import LinkForm, ProfileForm
from app.models import ProfileLink, User, UserProfile
from app.utils.auth import login_required

profile_bp = Blueprint("profile", __name__)

MAX_LINKS = 10


def _get_user(username):
    return User.query.filter_by(
        username=username, is_active=True
    ).first_or_404()


def _ensure_profile(user):
    """Registration creates a profile; this covers any user without one."""
    if user.profile is None:
        user.profile = UserProfile(display_name=user.username)
        db.session.commit()
    return user.profile


# =====================================================
# READ: public profile
# =====================================================

@profile_bp.get("/users/<username>")
def view(username):
    profile_user = _get_user(username)
    me = g.current_user
    profile = profile_user.profile

    return render_template(
        "profile/view.html",
        profile_user=profile_user,
        profile=profile,
        links=profile.links if profile else [],
        followers=profile_user.followers,
        following=profile_user.following,
        is_me=me is not None and me.user_id == profile_user.user_id,
        is_following=me is not None and profile_user in me.following,
    )


# =====================================================
# UPDATE: my profile
# =====================================================

@profile_bp.route("/account/profile", methods=["GET", "POST"])
@login_required
def edit():
    user = g.current_user
    profile = _ensure_profile(user)
    form = ProfileForm(obj=profile)

    if form.validate_on_submit():
        profile.display_name = form.display_name.data.strip()
        profile.bio = (form.bio.data or "").strip() or None
        profile.country = (form.country.data or "").strip() or None
        profile.avatar_url = (form.avatar_url.data or "").strip() or None
        profile.github_url = (form.github_url.data or "").strip() or None
        db.session.commit()

        flash("Profile updated.", "success")
        return redirect(url_for("profile.view", username=user.username))

    return render_template(
        "profile/edit.html",
        form=form,
        link_form=LinkForm(formdata=None),
        links=profile.links,
        max_links=MAX_LINKS,
    )


# =====================================================
# PROFILE LINKS: add / delete
# =====================================================

@profile_bp.post("/account/profile/links")
@login_required
def add_link():
    profile = _ensure_profile(g.current_user)
    form = LinkForm()

    if len(profile.links) >= MAX_LINKS:
        flash(f"You can add up to {MAX_LINKS} links.", "danger")
    elif form.validate_on_submit():
        profile.links.append(ProfileLink(
            label=form.label.data.strip(),
            url=form.url.data.strip(),
        ))
        db.session.commit()
        flash("Link added.", "success")
    else:
        for errors in form.errors.values():
            flash(errors[0], "danger")

    return redirect(url_for("profile.edit"))


@profile_bp.post("/account/profile/links/<int:link_id>/delete")
@login_required
def delete_link(link_id):
    link = db.get_or_404(ProfileLink, link_id)
    profile = g.current_user.profile

    # Only the owner can delete; anyone else gets a 404.
    if profile is None or link.profile_id != profile.profile_id:
        abort(404)

    db.session.delete(link)
    db.session.commit()
    flash("Link removed.", "info")
    return redirect(url_for("profile.edit"))


# =====================================================
# FOLLOW / UNFOLLOW
# =====================================================

@profile_bp.post("/users/<username>/follow")
@login_required
def follow(username):
    target = _get_user(username)
    me = g.current_user

    if target.user_id == me.user_id:
        flash("You can't follow yourself.", "danger")
    elif target not in me.following:
        me.following.append(target)
        db.session.commit()
        flash(f"You are now following {target.username}.", "success")

    return redirect(url_for("profile.view", username=username))


@profile_bp.post("/users/<username>/unfollow")
@login_required
def unfollow(username):
    target = _get_user(username)
    me = g.current_user

    if target in me.following:
        me.following.remove(target)
        db.session.commit()
        flash(f"You unfollowed {target.username}.", "info")

    return redirect(url_for("profile.view", username=username))