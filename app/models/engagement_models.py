from app import db
from app.models.user_models import utc_now


# =====================================================
# TABLE 42: ACHIEVEMENTS
# Achievement definitions and unlock criteria
# =====================================================

class Achievement(db.Model):
    __tablename__ = "achievements"

    achievement_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    achievement_name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=False)
    badge_image_url = db.Column(db.String(500), nullable=True)
    points_reward = db.Column(db.Integer, nullable=False, default=0)
    criteria_json = db.Column(db.Text, nullable=False)

    earned_by = db.relationship(
        "UserAchievement",
        back_populates="achievement",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self):
        return f"<Achievement {self.achievement_name}>"


# =====================================================
# TABLE 43: USER_ACHIEVEMENTS
# Bridge with extra data (earned_at, progress_value)
# =====================================================

class UserAchievement(db.Model):
    __tablename__ = "user_achievements"

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    )
    achievement_id = db.Column(
        db.Integer,
        db.ForeignKey("achievements.achievement_id", ondelete="CASCADE"),
        primary_key=True
    )
    earned_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )
    progress_value = db.Column(db.Integer, nullable=True)

    user = db.relationship("User", backref="achievements")
    achievement = db.relationship("Achievement", back_populates="earned_by")

    def __repr__(self):
        return f"<UserAchievement {self.user_id}/{self.achievement_id}>"


# =====================================================
# TABLE 44: POINTS_TRANSACTIONS
# Ledger of points earned/deducted; history is preserved
# =====================================================

class PointsTransaction(db.Model):
    __tablename__ = "points_transactions"

    points_transaction_id = db.Column(
        db.Integer, primary_key=True, autoincrement=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    points_delta = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(120), nullable=False)
    reference_type = db.Column(db.String(40), nullable=True)
    reference_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    user = db.relationship("User", backref="points_transactions")

    def __repr__(self):
        return f"<PointsTransaction {self.user_id} {self.points_delta:+d}>"


# =====================================================
# TABLE 45: LEARNING_PATHS
# =====================================================

class LearningPath(db.Model):
    __tablename__ = "learning_paths"

    learning_path_id = db.Column(
        db.Integer, primary_key=True, autoincrement=True
    )
    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=True)
    difficulty = db.Column(db.String(20), nullable=True)
    is_published = db.Column(db.Boolean, nullable=False, default=False)

    creator = db.relationship("User", backref="learning_paths")

    steps = db.relationship(
        "LearningPathStep",
        back_populates="learning_path",
        order_by="LearningPathStep.sequence_no",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self):
        return f"<LearningPath {self.title}>"


# =====================================================
# TABLE 46: LEARNING_PATH_STEPS
# =====================================================

class LearningPathStep(db.Model):
    __tablename__ = "learning_path_steps"

    step_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    learning_path_id = db.Column(
        db.Integer,
        db.ForeignKey("learning_paths.learning_path_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    problem_id = db.Column(
        db.Integer,
        db.ForeignKey("problems.problem_id", ondelete="SET NULL"),
        nullable=True
    )
    step_title = db.Column(db.String(160), nullable=False)
    instructions = db.Column(db.Text, nullable=True)
    sequence_no = db.Column(db.Integer, nullable=False)

    learning_path = db.relationship("LearningPath", back_populates="steps")
    problem = db.relationship("Problem", backref="learning_steps")

    progress = db.relationship(
        "UserLearningProgress",
        back_populates="step",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    __table_args__ = (
        db.UniqueConstraint(
            "learning_path_id", "sequence_no", name="uq_path_step_order"
        ),
    )

    def __repr__(self):
        return f"<LearningPathStep {self.step_title}>"


# =====================================================
# TABLE 47: USER_LEARNING_PROGRESS
# Bridge: a user's status on each step
# =====================================================

class UserLearningProgress(db.Model):
    __tablename__ = "user_learning_progress"

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    )
    step_id = db.Column(
        db.Integer,
        db.ForeignKey("learning_path_steps.step_id", ondelete="CASCADE"),
        primary_key=True
    )
    status = db.Column(db.String(20), nullable=False, default="not_started")
    started_at = db.Column(db.DateTime(timezone=True), nullable=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    user = db.relationship("User", backref="learning_progress")
    step = db.relationship("LearningPathStep", back_populates="progress")

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('not_started', 'in_progress', 'completed')",
            name="ck_learning_progress_status"
        ),
    )

    def __repr__(self):
        return f"<UserLearningProgress {self.user_id}/{self.step_id} {self.status}>"


# =====================================================
# TABLE 48: NOTIFICATIONS
# =====================================================

class Notification(db.Model):
    __tablename__ = "notifications"

    notification_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    notification_type = db.Column(db.String(40), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    message = db.Column(db.Text, nullable=False)
    related_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )
    read_at = db.Column(db.DateTime(timezone=True), nullable=True, index=True)

    user = db.relationship("User", backref="notifications")

    def __repr__(self):
        return f"<Notification {self.notification_id} {self.notification_type}>"


# =====================================================
# TABLE 49: NOTIFICATION_PREFERENCES
# One-to-one with users; user_id is the primary key
# =====================================================

class NotificationPreference(db.Model):
    __tablename__ = "notification_preferences"

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    )
    email_enabled = db.Column(db.Boolean, nullable=False, default=True)
    contest_alerts = db.Column(db.Boolean, nullable=False, default=True)
    submission_alerts = db.Column(db.Boolean, nullable=False, default=True)
    discussion_alerts = db.Column(db.Boolean, nullable=False, default=True)

    user = db.relationship(
        "User",
        backref=db.backref(
            "notification_preferences",
            uselist=False,
            cascade="all, delete-orphan",
            passive_deletes=True
        )
    )

    def __repr__(self):
        return f"<NotificationPreference {self.user_id}>"