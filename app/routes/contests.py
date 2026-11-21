from datetime import timezone

from flask import (
    Blueprint, abort, flash, g, redirect, render_template, url_for,
)

from app import db
from app.forms.contest import (
    AnnouncementForm, ContestForm, ContestProblemEditForm, ContestProblemForm,
)
from app.models import (
    Contest, ContestAnnouncement, ContestLeaderboardEntry, ContestProblem,
    ContestRegistration,
)
from app.utils.auth import log_action, login_required, permission_required
from app.utils.contest import contest_phase, is_registered, recalc_leaderboard

contests_bp = Blueprint("contests", __name__, url_prefix="/contests")


def _is_manager():
    user = g.current_user
    return user is not None and user.has_permission("contest.manage")


def _utc(dt):
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def _get_contest(contest_id):
    contest = db.get_or_404(Contest, contest_id)
    if contest.status == "cancelled" and not _is_manager():
        abort(404)
    return contest


def _flash_errors(form):
    for errors in form.errors.values():
        flash(errors[0], "danger")


def _detail(contest_id):
    return redirect(url_for("contests.detail", contest_id=contest_id))


# =====================================================
# CONTESTS: read
# =====================================================

@contests_bp.get("/")
def index():
    query = Contest.query
    if not _is_manager():
        query = query.filter(Contest.visibility == "public",
                             Contest.status != "cancelled")
    contests = query.order_by(Contest.starts_at.desc()).all()
    return render_template(
        "contests/list.html",
        contests=contests,
        phases={c.contest_id: contest_phase(c) for c in contests},
        can_manage=_is_manager(),
    )


@contests_bp.get("/<int:contest_id>")
def detail(contest_id):
    contest = _get_contest(contest_id)
    user = g.current_user
    phase = contest_phase(contest)
    manager = _is_manager()
    registered = user is not None and is_registered(contest, user)

    show_problems = manager or (registered and phase in ("running", "ended"))
    all_problems = contest.contest_problems      # ordered by sequence_no

    return render_template(
        "contests/detail.html",
        contest=contest,
        phase=phase,
        registered=registered,
        registration_count=ContestRegistration.query.filter_by(
            contest_id=contest_id).count(),
        contest_problems=all_problems if show_problems else [],
        announcements=sorted(contest.announcements,
                             key=lambda a: a.published_at, reverse=True),
        can_manage=manager,
        problem_form=ContestProblemForm(
            exclude_ids=[cp.problem_id for cp in all_problems]
        ) if manager else None,
        announcement_form=AnnouncementForm() if manager else None,
    )


@contests_bp.get("/<int:contest_id>/leaderboard")
def leaderboard(contest_id):
    contest = _get_contest(contest_id)
    entries = (ContestLeaderboardEntry.query.filter_by(contest_id=contest_id)
               .order_by(ContestLeaderboardEntry.rank_position.asc()).all())
    return render_template(
        "contests/leaderboard.html",
        contest=contest,
        phase=contest_phase(contest),
        entries=entries,
        can_manage=_is_manager(),
    )


# =====================================================
# CONTESTS: create / update / cancel (contest.manage)
# =====================================================

@contests_bp.route("/new", methods=["GET", "POST"])
@permission_required("contest.manage")
def create():
    form = ContestForm()
    if form.validate_on_submit():
        contest = Contest(
            created_by=g.current_user.user_id,
            title=form.title.data.strip(),
            description=(form.description.data or "").strip() or None,
            starts_at=_utc(form.starts_at.data),
            ends_at=_utc(form.ends_at.data),
            visibility=form.visibility.data,
            status="scheduled",
        )
        db.session.add(contest)
        db.session.flush()
        log_action("contest.create", "contest", contest.contest_id,
                   g.current_user.user_id)
        db.session.commit()

        flash("Contest created.", "success")
        return _detail(contest.contest_id)

    return render_template("contests/form.html", form=form, contest=None)


@contests_bp.route("/<int:contest_id>/edit", methods=["GET", "POST"])
@permission_required("contest.manage")
def edit(contest_id):
    contest = db.get_or_404(Contest, contest_id)
    form = ContestForm(obj=contest)

    if form.validate_on_submit():
        contest.title = form.title.data.strip()
        contest.description = (form.description.data or "").strip() or None
        contest.starts_at = _utc(form.starts_at.data)
        contest.ends_at = _utc(form.ends_at.data)
        contest.visibility = form.visibility.data
        db.session.flush()
        recalc_leaderboard(contest)          # the time window may have moved
        log_action("contest.update", "contest", contest.contest_id,
                   g.current_user.user_id)
        db.session.commit()

        flash("Contest updated.", "success")
        return _detail(contest.contest_id)

    return render_template("contests/form.html", form=form, contest=contest)


@contests_bp.post("/<int:contest_id>/cancel")
@permission_required("contest.manage")
def toggle_cancel(contest_id):
    """Contests are never deleted; they are cancelled or restored."""
    contest = db.get_or_404(Contest, contest_id)
    contest.status = "scheduled" if contest.status == "cancelled" else "cancelled"
    log_action(f"contest.{contest.status}", "contest", contest.contest_id,
               g.current_user.user_id)
    db.session.commit()

    flash("Contest cancelled." if contest.status == "cancelled"
          else "Contest restored.", "info")
    return _detail(contest.contest_id)


# =====================================================
# CONTEST PROBLEMS (contest.manage): add / update / remove
# =====================================================

@contests_bp.post("/<int:contest_id>/problems")
@permission_required("contest.manage")
def add_problem(contest_id):
    contest = db.get_or_404(Contest, contest_id)
    current = contest.contest_problems
    form = ContestProblemForm(exclude_ids=[cp.problem_id for cp in current])

    if form.validate_on_submit():
        next_seq = max((cp.sequence_no for cp in current), default=0) + 1
        db.session.add(ContestProblem(
            contest_id=contest_id,
            problem_id=form.problem_id.data,
            points=form.points.data,
            sequence_no=form.sequence_no.data or next_seq,
        ))
        db.session.commit()
        flash("Problem added to the contest.", "success")
    else:
        _flash_errors(form)

    return _detail(contest_id)


@contests_bp.post("/<int:contest_id>/problems/<int:problem_id>/update")
@permission_required("contest.manage")
def update_problem(contest_id, problem_id):
    cp = db.session.get(ContestProblem, (contest_id, problem_id))
    if cp is None:
        abort(404)

    form = ContestProblemEditForm()
    if form.validate_on_submit():
        cp.points = form.points.data
        if form.sequence_no.data:
            cp.sequence_no = form.sequence_no.data
        db.session.flush()
        recalc_leaderboard(cp.contest)       # points changed
        db.session.commit()
        flash("Contest problem updated.", "success")
    else:
        _flash_errors(form)

    return _detail(contest_id)


@contests_bp.post("/<int:contest_id>/problems/<int:problem_id>/remove")
@permission_required("contest.manage")
def remove_problem(contest_id, problem_id):
    cp = db.session.get(ContestProblem, (contest_id, problem_id))
    if cp is None:
        abort(404)

    contest = cp.contest
    db.session.delete(cp)
    db.session.flush()
    recalc_leaderboard(contest)
    db.session.commit()

    flash("Problem removed from the contest.", "info")
    return _detail(contest_id)


# =====================================================
# REGISTRATION (any logged-in user)
# =====================================================

@contests_bp.post("/<int:contest_id>/register")
@login_required
def register(contest_id):
    contest = _get_contest(contest_id)
    user = g.current_user

    if contest_phase(contest) not in ("upcoming", "running"):
        flash("Registration is closed for this contest.", "danger")
    elif is_registered(contest, user):
        flash("You are already registered.", "info")
    else:
        db.session.add(ContestRegistration(
            contest_id=contest_id, user_id=user.user_id
        ))
        db.session.flush()
        recalc_leaderboard(contest)
        db.session.commit()
        flash("You are registered for this contest.", "success")

    return _detail(contest_id)


@contests_bp.post("/<int:contest_id>/unregister")
@login_required
def unregister(contest_id):
    contest = _get_contest(contest_id)
    user = g.current_user

    if contest_phase(contest) != "upcoming":
        flash("You can only withdraw before the contest starts.", "danger")
    else:
        registration = ContestRegistration.query.filter_by(
            contest_id=contest_id, user_id=user.user_id
        ).first()
        if registration:
            db.session.delete(registration)
            db.session.flush()
            recalc_leaderboard(contest)
            db.session.commit()
            flash("You have withdrawn from the contest.", "info")

    return _detail(contest_id)


# =====================================================
# ANNOUNCEMENTS (contest.manage): create / delete
# =====================================================

@contests_bp.post("/<int:contest_id>/announcements")
@permission_required("contest.manage")
def add_announcement(contest_id):
    contest = db.get_or_404(Contest, contest_id)
    form = AnnouncementForm()

    if form.validate_on_submit():
        db.session.add(ContestAnnouncement(
            contest_id=contest.contest_id,
            author_id=g.current_user.user_id,
            message=form.message.data,
        ))
        db.session.commit()
        flash("Announcement posted.", "success")
    else:
        _flash_errors(form)

    return _detail(contest_id)


@contests_bp.post("/announcements/<int:announcement_id>/delete")
@permission_required("contest.manage")
def delete_announcement(announcement_id):
    announcement = db.get_or_404(ContestAnnouncement, announcement_id)
    contest_id = announcement.contest_id

    db.session.delete(announcement)
    db.session.commit()

    flash("Announcement deleted.", "info")
    return _detail(contest_id)


# =====================================================
# LEADERBOARD: manual rebuild (contest.manage)
# =====================================================

@contests_bp.post("/<int:contest_id>/leaderboard/refresh")
@permission_required("contest.manage")
def refresh_leaderboard(contest_id):
    contest = db.get_or_404(Contest, contest_id)
    recalc_leaderboard(contest)
    db.session.commit()

    flash("Leaderboard recalculated.", "success")
    return redirect(url_for("contests.leaderboard", contest_id=contest_id))