from datetime import datetime, timezone

from app import db
from app.models import (
    Contest, ContestLeaderboardEntry, ContestProblem, ContestRegistration,
    Submission,
)
from app.models.user_models import utc_now

WRONG_STATUSES = {
    "wrong_answer", "runtime_error", "compile_error", "time_limit_exceeded",
}
PENALTY_PER_WRONG = 20 * 60          # seconds added per wrong attempt
FAR_FUTURE = datetime.max.replace(tzinfo=timezone.utc)


def as_utc(dt):
    """SQLite returns naive datetimes; treat them as UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def contest_phase(contest):
    if contest.status == "cancelled":
        return "cancelled"
    now = utc_now()
    if now < as_utc(contest.starts_at):
        return "upcoming"
    if now < as_utc(contest.ends_at):
        return "running"
    return "ended"


def is_registered(contest, user):
    return ContestRegistration.query.filter_by(
        contest_id=contest.contest_id, user_id=user.user_id
    ).first() is not None


def can_submit_to_contest(contest, problem, user):
    if contest_phase(contest) != "running" or not is_registered(contest, user):
        return False
    return ContestProblem.query.filter_by(
        contest_id=contest.contest_id, problem_id=problem.problem_id
    ).first() is not None


def can_view_contest_problem(user, problem):
    """Registered participants may open a contest's problem once it starts."""
    return db.session.query(ContestProblem.contest_id).join(
        Contest, Contest.contest_id == ContestProblem.contest_id
    ).join(
        ContestRegistration,
        ContestRegistration.contest_id == Contest.contest_id,
    ).filter(
        ContestProblem.problem_id == problem.problem_id,
        ContestRegistration.user_id == user.user_id,
        Contest.status != "cancelled",
        Contest.starts_at <= utc_now(),
    ).first() is not None


def recalc_leaderboard(contest):
    """Rebuild the cached leaderboard. The caller commits.

    Score = points of problems with an accepted submission inside the contest
    window. Ranking: score (high first), then penalty (low first), then time
    of the last accepted solution (earlier first), then user id.
    Penalty = seconds from start to each accepted solution, plus 20 minutes
    per earlier wrong attempt on that problem.
    """
    cid = contest.contest_id
    start, end = as_utc(contest.starts_at), as_utc(contest.ends_at)

    points = {cp.problem_id: cp.points
              for cp in ContestProblem.query.filter_by(contest_id=cid)}
    stats = {r.user_id: {}
             for r in ContestRegistration.query.filter_by(contest_id=cid)}

    submissions = (Submission.query.filter_by(contest_id=cid)
                   .order_by(Submission.submitted_at.asc(),
                             Submission.submission_id.asc()))
    for s in submissions:
        if s.user_id not in stats or s.problem_id not in points:
            continue
        submitted = as_utc(s.submitted_at)
        if not start <= submitted <= end:
            continue
        state = stats[s.user_id].setdefault(
            s.problem_id, {"wrong": 0, "solved_at": None}
        )
        if state["solved_at"] is not None:
            continue
        if s.status == "accepted":
            state["solved_at"] = submitted
        elif s.status in WRONG_STATUSES:
            state["wrong"] += 1

    rows = []
    for user_id, problems in stats.items():
        solved = [(pid, st) for pid, st in problems.items() if st["solved_at"]]
        rows.append({
            "user_id": user_id,
            "score": sum(points[pid] for pid, _ in solved),
            "solved": len(solved),
            "penalty": sum(
                int((st["solved_at"] - start).total_seconds())
                + st["wrong"] * PENALTY_PER_WRONG
                for _, st in solved
            ),
            "last": max((st["solved_at"] for _, st in solved), default=None),
        })
    rows.sort(key=lambda r: (-r["score"], r["penalty"],
                             r["last"] or FAR_FUTURE, r["user_id"]))

    existing = {e.user_id: e for e in
                ContestLeaderboardEntry.query.filter_by(contest_id=cid)}
    for rank, row in enumerate(rows, start=1):
        entry = existing.pop(row["user_id"], None)
        if entry is None:
            entry = ContestLeaderboardEntry(
                contest_id=cid, user_id=row["user_id"]
            )
            db.session.add(entry)
        entry.score = row["score"]
        entry.solved_count = row["solved"]
        entry.penalty_seconds = row["penalty"]
        entry.rank_position = rank
    for stale in existing.values():
        db.session.delete(stale)