from flask import (
    Blueprint, abort, flash, g, redirect, render_template, url_for,
)

from app import db
from app.forms.team import InviteForm, TeamForm
from app.models import Team, TeamInvitation, TeamMember, User
from app.models.user_models import utc_now
from app.utils.auth import login_required

teams_bp = Blueprint("teams", __name__, url_prefix="/teams")


def _flash_errors(form):
    for errors in form.errors.values():
        flash(errors[0], "danger")


def _member(team_id, user_id):
    return db.session.get(TeamMember, (team_id, user_id))


def _team_for_member(team_id):
    """Teams are private: non-members get a 404."""
    team = db.get_or_404(Team, team_id)
    if _member(team_id, g.current_user.user_id) is None:
        abort(404)
    return team


def _team_for_owner(team_id):
    team = _team_for_member(team_id)
    if team.owner_id != g.current_user.user_id:
        abort(403)
    return team


def _my_pending_invitation(invitation_id):
    invitation = db.get_or_404(TeamInvitation, invitation_id)
    if (invitation.invited_user_id != g.current_user.user_id
            or invitation.status != "pending"):
        abort(404)
    return invitation


# =====================================================
# TEAMS: read
# =====================================================

@teams_bp.get("/")
@login_required
def index():
    uid = g.current_user.user_id
    teams = (Team.query.join(TeamMember)
             .filter(TeamMember.user_id == uid)
             .order_by(Team.created_at.desc()).all())
    pending = TeamInvitation.query.filter_by(
        invited_user_id=uid, status="pending").count()
    return render_template("teams/list.html", teams=teams,
                           pending_invitations=pending)


@teams_bp.get("/<int:team_id>")
@login_required
def detail(team_id):
    team = _team_for_member(team_id)
    is_owner = team.owner_id == g.current_user.user_id
    return render_template(
        "teams/detail.html",
        team=team,
        members=sorted(team.members, key=lambda m: m.joined_at),
        invitations=[i for i in team.invitations
                     if i.status == "pending"] if is_owner else [],
        is_owner=is_owner,
        invite_form=InviteForm() if is_owner else None,
    )


# =====================================================
# TEAMS: create / update / delete
# =====================================================

@teams_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    form = TeamForm()
    if form.validate_on_submit():
        user = g.current_user
        team = Team(
            team_name=form.team_name.data.strip(),
            description=(form.description.data or "").strip() or None,
            owner_id=user.user_id,
        )
        team.members = [TeamMember(user_id=user.user_id, team_role="owner")]
        db.session.add(team)
        db.session.commit()

        flash("Team created.", "success")
        return redirect(url_for("teams.detail", team_id=team.team_id))

    return render_template("teams/form.html", form=form, team=None)


@teams_bp.route("/<int:team_id>/edit", methods=["GET", "POST"])
@login_required
def edit(team_id):
    team = _team_for_owner(team_id)
    form = TeamForm(obj=team)

    if form.validate_on_submit():
        team.team_name = form.team_name.data.strip()
        team.description = (form.description.data or "").strip() or None
        db.session.commit()

        flash("Team updated.", "success")
        return redirect(url_for("teams.detail", team_id=team.team_id))

    return render_template("teams/form.html", form=form, team=team)


@teams_bp.post("/<int:team_id>/delete")
@login_required
def delete(team_id):
    team = _team_for_owner(team_id)
    db.session.delete(team)          # members and invitations cascade
    db.session.commit()

    flash("Team deleted.", "info")
    return redirect(url_for("teams.index"))


# =====================================================
# MEMBERS: leave / remove
# =====================================================

@teams_bp.post("/<int:team_id>/leave")
@login_required
def leave(team_id):
    team = _team_for_member(team_id)

    if team.owner_id == g.current_user.user_id:
        flash("The owner can't leave the team. Delete it instead.", "danger")
        return redirect(url_for("teams.detail", team_id=team_id))

    db.session.delete(_member(team_id, g.current_user.user_id))
    db.session.commit()

    flash("You left the team.", "info")
    return redirect(url_for("teams.index"))


@teams_bp.post("/<int:team_id>/members/<int:user_id>/remove")
@login_required
def remove_member(team_id, user_id):
    team = _team_for_owner(team_id)

    if user_id == team.owner_id:
        flash("The owner can't be removed.", "danger")
    else:
        membership = _member(team_id, user_id)
        if membership is None:
            abort(404)
        db.session.delete(membership)
        db.session.commit()
        flash("Member removed.", "info")

    return redirect(url_for("teams.detail", team_id=team_id))


# =====================================================
# INVITATIONS: send / cancel / list mine / accept / decline
# =====================================================

@teams_bp.post("/<int:team_id>/invite")
@login_required
def invite(team_id):
    team = _team_for_owner(team_id)
    form = InviteForm()
    back = redirect(url_for("teams.detail", team_id=team_id))

    if not form.validate_on_submit():
        _flash_errors(form)
        return back

    target = User.query.filter_by(
        username=form.username.data.strip(), is_active=True
    ).first()

    if target is None:
        flash("No active user with that username.", "danger")
    elif _member(team_id, target.user_id):
        flash(f"{target.username} is already a member.", "info")
    else:
        # One row per (team, user): re-inviting reuses it.
        invitation = TeamInvitation.query.filter_by(
            team_id=team_id, invited_user_id=target.user_id).first()

        if invitation and invitation.status == "pending":
            flash(f"{target.username} already has a pending invitation.",
                  "info")
        else:
            if invitation is None:
                invitation = TeamInvitation(
                    team_id=team_id,
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


@teams_bp.post("/invitations/<int:invitation_id>/cancel")
@login_required
def cancel_invitation(invitation_id):
    invitation = db.get_or_404(TeamInvitation, invitation_id)
    _team_for_owner(invitation.team_id)
    if invitation.status != "pending":
        abort(404)

    team_id = invitation.team_id
    db.session.delete(invitation)
    db.session.commit()

    flash("Invitation cancelled.", "info")
    return redirect(url_for("teams.detail", team_id=team_id))


@teams_bp.get("/invitations")
@login_required
def my_invitations():
    invitations = (TeamInvitation.query
                   .filter_by(invited_user_id=g.current_user.user_id,
                              status="pending")
                   .order_by(TeamInvitation.created_at.desc()).all())
    return render_template("teams/invitations.html", invitations=invitations)


@teams_bp.post("/invitations/<int:invitation_id>/accept")
@login_required
def accept_invitation(invitation_id):
    invitation = _my_pending_invitation(invitation_id)

    if _member(invitation.team_id, g.current_user.user_id) is None:
        db.session.add(TeamMember(
            team_id=invitation.team_id,
            user_id=g.current_user.user_id,
            team_role="member",
        ))
    invitation.status = "accepted"
    db.session.commit()

    flash("You joined the team.", "success")
    return redirect(url_for("teams.detail", team_id=invitation.team_id))


@teams_bp.post("/invitations/<int:invitation_id>/decline")
@login_required
def decline_invitation(invitation_id):
    invitation = _my_pending_invitation(invitation_id)
    invitation.status = "declined"
    db.session.commit()

    flash("Invitation declined.", "info")
    return redirect(url_for("teams.my_invitations"))