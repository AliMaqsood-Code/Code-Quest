import json

from sqlalchemy import func

from app import db
from app.models import (
    Achievement, Notification, NotificationPreference, PointsTransaction,
    Submission, UserAchievement,
)

SOLVE_POINTS = {"easy": 10, "medium": 20, "hard": 30}

# Notification types a user can switch off in their preferences.
PREFERENCE_FIELD = {
    "contest": "contest_alerts",
    "submission": "submission_alerts",
    "discussion": "discussion_alerts",
}


def notify(user_id, notification_type, title, message, related_url=None):
    """Queue a notification (caller commits), unless the user opted out."""
    prefs = db.session.get(NotificationPreference, user_id)
    field = PREFERENCE_FIELD.get(notification_type)
    if prefs is not None and field and not getattr(prefs, field):
        return None

    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title[:160],
        message=message,
        related_url=related_url[:500] if related_url else None,
    )
    db.session.add(notification)
    return notification


def total_points(user_id):
    return db.session.query(
        func.coalesce(func.sum(PointsTransaction.points_delta), 0)
    ).filter(PointsTransaction.user_id == user_id).scalar()


def award_for_accepted(submission):
    """Points for the first accepted solution of a problem, then check
    achievements. Safe to call repeatedly. The caller commits."""
    user_id = submission.user_id
    problem = submission.problem

    already = PointsTransaction.query.filter_by(
        user_id=user_id, reason="problem_solved",
        reference_type="problem", reference_id=problem.problem_id,
    ).first()
    if already is None:
        db.session.add(PointsTransaction(
            user_id=user_id,
            points_delta=SOLVE_POINTS.get(problem.difficulty, 10),
            reason="problem_solved",
            reference_type="problem",
            reference_id=problem.problem_id,
        ))

    db.session.flush()
    _check_achievements(user_id)


def _check_achievements(user_id):
    solved = db.session.query(
        func.count(func.distinct(Submission.problem_id))
    ).filter(
        Submission.user_id == user_id, Submission.status == "accepted"
    ).scalar()

    earned = {ua.achievement_id
              for ua in UserAchievement.query.filter_by(user_id=user_id)}

    for achievement in Achievement.query.all():
        if achievement.achievement_id in earned:
            continue
        try:
            criteria = json.loads(achievement.criteria_json)
            needed = int(criteria.get("value", 0))
        except (ValueError, TypeError, AttributeError):
            continue

        if criteria.get("type") == "solved_count" and 0 < needed <= solved:
            db.session.add(UserAchievement(
                user_id=user_id,
                achievement_id=achievement.achievement_id,
                progress_value=solved,
            ))
            if achievement.points_reward:
                db.session.add(PointsTransaction(
                    user_id=user_id,
                    points_delta=achievement.points_reward,
                    reason="achievement",
                    reference_type="achievement",
                    reference_id=achievement.achievement_id,
                ))
            notify(user_id, "achievement",
                   f"Achievement unlocked: {achievement.achievement_name}",
                   achievement.description, "/achievements/")