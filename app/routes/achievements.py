from flask import Blueprint, g, render_template

from app.models import Achievement, PointsTransaction, UserAchievement
from app.utils.auth import login_required
from app.utils.engagement import total_points

achievements_bp = Blueprint("achievements", __name__,
                            url_prefix="/achievements")


@achievements_bp.get("/")
@login_required
def index():
    uid = g.current_user.user_id
    return render_template(
        "achievements/index.html",
        achievements=Achievement.query.order_by(
            Achievement.points_reward, Achievement.achievement_name).all(),
        earned={ua.achievement_id: ua
                for ua in UserAchievement.query.filter_by(user_id=uid)},
        total_points=total_points(uid),
        history=PointsTransaction.query.filter_by(user_id=uid)
        .order_by(PointsTransaction.created_at.desc()).limit(50).all(),
    )