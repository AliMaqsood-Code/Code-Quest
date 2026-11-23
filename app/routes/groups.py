from flask import (
    Blueprint, abort, flash, g, redirect, render_template, url_for,
)

from app import db
from app.forms.team import GroupForm, InviteForm, JoinGroupForm
from app.models import GroupInvitation, GroupMember, PrivateGroup, User
from app.models.user_models import utc_now
from app.utils.auth import login_required
from app.utils.tokenManagement import generate_token, hash_token

groups_bp = Blueprint("groups", __name__, url_prefix="/groups")


def _flash_errors(form):
    for errors in form.errors.values():
        flash(errors[0], "danger")


def _member(group_id, user_id):
    return db.session.get(GroupMember, (group_id, user_id))


def _group_for_member(group_id):
    """Private groups: non-members get a 404."""
    group = db.get_or_404(PrivateGroup, group_id)
    if _member(group_id, g.current_user.user_id) is None:
        abort(404)
    return group


def _group_for_owner(group_id):
    group = _group_for_member(group_id)
    if group.owner_id != g.current_user.user_id:
        abort(403)
    return group


def _my_pending_invitation(invitation_id):
    invitation = db.get_or_404(GroupInvitation, invitation_id)
    if (invitation.invited_user_id != g.current_user.user_id
            or invitation.status != "pending"):
        abort(404)
    return invitation


# =====================================================
# GROUPS: read
# =====================================================

@groups_bp.get("/")
@login_required
def index():
    uid = g.current_user.user_id
    groups = (PrivateGroup.query.join(GroupMember)
              .filter(GroupMember.user_id == uid)
              .order_by(PrivateGroup.created_at.desc()).all())
    pending = GroupInvitation.query.filter_by(
        invited_user_id=uid, status="pending").count()
    return render_template("groups/list.html", groups=groups,
                           pending_invitations=pending)


@groups_bp.get("/<int:group_id>")
@login_required
def detail(group_id):
    group = _group_for_member(group_id)
    is_owner = group.owner_id == g.current_user.user_id
    return render_template(
        "groups/detail.html",
        group=group,
        members=sorted(group.members, key=lambda m: m.joined_at),
        invitations=[i for i in group.invitations
                     if i.status == "pending"] if is_owner else [],
        is_owner=is_owner,
        has_invite_code=group.invite_code_hash is not None,
        invite_form=InviteForm() if is_owner else None,
    )


# =====================================================
# GROUPS: create / update / delete
# =====================================================

@groups_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    form = GroupForm()
    if form.validate_on_submit():
        user = g.current_user
        group = PrivateGroup(
            group_name=form.group_name.data.strip(),
            description=(form.description.data or "").strip() or None,
            owner_id=user.user_id,
        )
        group.members = [GroupMember(user_id=user.user_id,
                                     member_role="owner")]
        db.session.add(group)
        db.session.commit()

        flash("Group created.", "success")
        return redirect(url_for("groups.detail", group_id=group.group_id))

    return render_template("groups/form.html", form=form, group=None)


@groups_bp.route("/<int:group_id>/edit", methods=["GET", "POST"])
@login_required
def edit(group_id):
    group = _group_for_owner(group_id)
    form = GroupForm(obj=group)

    if form.validate_on_submit():
        group.group_name = form.group_name.data.strip()
        group.description = (form.description.data or "").strip() or None
        db.session.commit()

        flash("Group updated.", "success")
        return redirect(url_for("groups.detail", group_id=group.group_id))

    return render_template("groups/form.html", form=form, group=group)


@groups_bp.post("/<int:group_id>/delete")
@login_required
def delete(group_id):
    group = _group_for_owner(group_id)
    db.session.delete(group)         # members and invitations cascade
    db.session.commit()

    flash("Group deleted.", "info")
    return redirect(url_for("groups.index"))


# =====================================================
# MEMBERS: leave / remove
# =====================================================

@groups_bp.post("/<int:group_id>/leave")
@login_required
def leave(group_id):
    group = _group_for_member(group_id)

    if group.owner_id == g.current_user.user_id:
        flash("The owner can't leave the group. Delete it instead.", "danger")
        return redirect(url_for("groups.detail", group_id=group_id))

    db.session.delete(_member(group_id, g.current_user.user_id))
    db.session.commit()

    flash("You left the group.", "info")
    return redirect(url_for("groups.index"))


@groups_bp.post("/<int:group_id>/members/<int:user_id>/remove")
@login_required
def remove_member(group_id, user_id):
    group = _group_for_owner(group_id)

    if user_id == group.owner_id:
        flash("The owner can't be removed.", "danger")
    else:
        membership = _member(group_id, user_id)
        if membership is None:
            abort(404)
        db.session.delete(membership)
        db.session.commit()
        flash("Member removed.", "info")

    return redirect(url_for("groups.detail", group_id=group_id))


# =====================================================
# INVITATIONS: send / cancel / list mine / accept / decline
# =====================================================

@groups_bp.post("/<int:group_id>/invite")
@login_required
def invite(group_id):
    group = _group_for_owner(group_id)
    form = InviteForm()
    back = redirect(url_for("groups.detail", group_id=group_id))

    if not form.validate_on_submit():
        _flash_errors(form)
        return back

    target = User.query.filter_by(
        username=form.username.data.strip(), is_active=True
    ).first()

    if target is None:
        flash("No active user with that username.", "danger")
    elif _member(group_id, target.user_id):
        flash(f"{target.username} is already a member.", "info")
    else:
        invitation = GroupInvitation.query.filter_by(
            group_id=group_id, invited_user_id=target.user_id).first()

        if invitation and invitation.status == "pending":
            flash(f"{target.username} already has a pending invitation.",
                  "info")
        else:
            if invitation is None:
                invitation = GroupInvitation(
                    group_id=group_id,
                    invited_user_id=target.user_id,
                    invited_by=g.current_user.user_id,
                )
                db.session.add(invitation)
            invitation.invited_by = g.current_user.user_id
            invitation.status = "pending"
            invitation.created_at = utc_now()
            db.session.commit()
            flash(f"Invitation sent to {target.username}.", "success")

    return back


@groups_bp.post("/invitations/<int:invitation_id>/cancel")
@login_required
def cancel_invitation(invitation_id):
    invitation = db.get_or_404(GroupInvitation, invitation_id)
    _group_for_owner(invitation.group_id)
    if invitation.status != "pending":
        abort(404)

    group_id = invitation.group_id
    db.session.delete(invitation)
    db.session.commit()

    flash("Invitation cancelled.", "info")
    return redirect(url_for("groups.detail", group_id=group_id))


@groups_bp.get("/invitations")
@login_required
def my_invitations():
    invitations = (GroupInvitation.query
                   .filter_by(invited_user_id=g.current_user.user_id,
                              status="pending")
                   .order_by(GroupInvitation.created_at.desc()).all())
    return render_template("groups/invitations.html",
                           invitations=invitations)


@groups_bp.post("/invitations/<int:invitation_id>/accept")
@login_required
def accept_invitation(invitation_id):
    invitation = _my_pending_invitation(invitation_id)

    if _member(invitation.group_id, g.current_user.user_id) is None:
        db.session.add(GroupMember(
            group_id=invitation.group_id,
            user_id=g.current_user.user_id,
            member_role="member",
        ))
    invitation.status = "accepted"
    db.session.commit()

    flash("You joined the group.", "success")
    return redirect(url_for("groups.detail", group_id=invitation.group_id))


@groups_bp.post("/invitations/<int:invitation_id>/decline")
@login_required
def decline_invitation(invitation_id):
    invitation = _my_pending_invitation(invitation_id)
    invitation.status = "declined"
    db.session.commit()

    flash("Invitation declined.", "info")
    return redirect(url_for("groups.my_invitations"))


# =====================================================
# INVITE CODE: generate / revoke (owner), join (anyone)
# =====================================================

@groups_bp.post("/<int:group_id>/code")
@login_required
def generate_code(group_id):
    """Create (or replace) the group's invite code. Only the hash is stored,
    so the raw code is shown on this response and never again."""
    group = _group_for_owner(group_id)
    raw_code, code_hash = generate_token()
    group.invite_code_hash = code_hash
    db.session.commit()

    return render_template("groups/invite_code.html",
                           group=group, code=raw_code)


@groups_bp.post("/<int:group_id>/code/revoke")
@login_required
def revoke_code(group_id):
    group = _group_for_owner(group_id)
    group.invite_code_hash = None
    db.session.commit()

    flash("Invite code revoked.", "info")
    return redirect(url_for("groups.detail", group_id=group_id))


@groups_bp.route("/join", methods=["GET", "POST"])
@login_required
def join():
    form = JoinGroupForm()
    if form.validate_on_submit():
        group = PrivateGroup.query.filter_by(
            invite_code_hash=hash_token(form.code.data.strip())
        ).first()

        if group is None:
            flash("Invalid or revoked invite code.", "danger")
        elif _member(group.group_id, g.current_user.user_id):
            flash("You are already in this group.", "info")
            return redirect(url_for("groups.detail", group_id=group.group_id))
        else:
            db.session.add(GroupMember(
                group_id=group.group_id,
                user_id=g.current_user.user_id,
                member_role="member",
            ))
            db.session.commit()
            flash(f"You joined {group.group_name}.", "success")
            return redirect(url_for("groups.detail", group_id=group.group_id))

    return render_template("groups/join.html", form=form)