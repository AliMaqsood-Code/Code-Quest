from flask import Blueprint, g, render_template
from sqlalchemy import func

from app import db
from app.models import Contest, Notification, Problem, Submission
from app.utils.auth import login_required
from app.utils.contest import contest_phase
from app.utils.engagement import total_points

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    return render_template("home.html")


@main_bp.get("/dashboard")
@login_required
def dashboard():
    uid = g.current_user.user_id

    # Distinct problems solved (accepted), split by difficulty
    solved_rows = (
        db.session.query(
            Problem.difficulty,
            func.count(func.distinct(Submission.problem_id)),
        )
        .join(Submission, Submission.problem_id == Problem.problem_id)
        .filter(Submission.user_id == uid, Submission.status == "accepted")
        .group_by(Problem.difficulty)
        .all()
    )
    by_difficulty = {difficulty: count for difficulty, count in solved_rows}

    recent_submissions = (
        Submission.query.filter_by(user_id=uid)
        .order_by(Submission.submitted_at.desc())
        .limit(5)
        .all()
    )

    # Running or upcoming public contests (at most 3)
    candidates = (
        Contest.query.filter(
            Contest.visibility == "public", Contest.status != "cancelled"
        )
        .order_by(Contest.starts_at.asc())
        .all()
    )
    phases = {c.contest_id: contest_phase(c) for c in candidates}
    contests = [
        c for c in candidates if phases[c.contest_id] in ("running", "upcoming")
    ][:3]

    unread = (
        Notification.query.filter(
            Notification.user_id == uid, Notification.read_at.is_(None)
        )
        .order_by(Notification.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "dashboard.html",
        solved=sum(by_difficulty.values()),
        by_difficulty=by_difficulty,
        total_problems=Problem.query.filter_by(
            status="published", visibility="public"
        ).count(),
        total_submissions=Submission.query.filter_by(user_id=uid).count(),
        pending=Submission.query.filter_by(user_id=uid, status="queued").count(),
        points=total_points(uid),
        recent_submissions=recent_submissions,
        contests=contests,
        phases=phases,
        unread=unread,
    )