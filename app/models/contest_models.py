from app import db
from app.models.user_models import utc_now


# =====================================================
# TABLE 25: CONTESTS
# Scheduled programming competitions
# =====================================================

class Contest(db.Model):
    __tablename__ = "contests"

    contest_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=True)
    starts_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    ends_at = db.Column(db.DateTime(timezone=True), nullable=False)
    visibility = db.Column(db.String(20), nullable=False, default="public")
    status = db.Column(db.String(20), nullable=False, default="scheduled")

    # Relationships
    creator = db.relationship("User", backref="created_contests")

    contest_problems = db.relationship(
        "ContestProblem",
        back_populates="contest",
        order_by="ContestProblem.sequence_no",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    registrations = db.relationship(
        "ContestRegistration",
        back_populates="contest",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    announcements = db.relationship(
        "ContestAnnouncement",
        back_populates="contest",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    leaderboard = db.relationship(
        "ContestLeaderboardEntry",
        back_populates="contest",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    __table_args__ = (
        db.CheckConstraint(
            "ends_at > starts_at",
            name="ck_contest_dates"
        ),
        db.CheckConstraint(
            "visibility IN ('public', 'private')",
            name="ck_contest_visibility"
        ),
    )

    def __repr__(self):
        return f"<Contest {self.title}>"


# =====================================================
# TABLE 26: CONTEST_PROBLEMS
# Bridge with extra data (points, order), so it's a model
# instead of a plain db.Table
# =====================================================

class ContestProblem(db.Model):
    __tablename__ = "contest_problems"

    contest_id = db.Column(
        db.Integer,
        db.ForeignKey("contests.contest_id", ondelete="CASCADE"),
        primary_key=True
    )
    problem_id = db.Column(
        db.Integer,
        db.ForeignKey("problems.problem_id", ondelete="RESTRICT"),
        primary_key=True
    )
    points = db.Column(db.Integer, nullable=False)
    sequence_no = db.Column(db.Integer, nullable=False)

    contest = db.relationship("Contest", back_populates="contest_problems")
    problem = db.relationship("Problem", backref="contest_links")

    __table_args__ = (
        db.CheckConstraint("points >= 0", name="ck_contest_problem_points"),
    )

    def __repr__(self):
        return f"<ContestProblem {self.contest_id}/{self.problem_id}>"


# =====================================================
# TABLE 27: CONTEST_REGISTRATIONS
# =====================================================

class ContestRegistration(db.Model):
    __tablename__ = "contest_registrations"

    registration_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    contest_id = db.Column(
        db.Integer,
        db.ForeignKey("contests.contest_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    registered_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    contest = db.relationship("Contest", back_populates="registrations")
    user = db.relationship("User", backref="contest_registrations")

    __table_args__ = (
        db.UniqueConstraint(
            "contest_id", "user_id", name="uq_contest_registration"
        ),
    )

    def __repr__(self):
        return f"<ContestRegistration {self.contest_id}/{self.user_id}>"


# =====================================================
# TABLE 28: CONTEST_ANNOUNCEMENTS
# =====================================================

class ContestAnnouncement(db.Model):
    __tablename__ = "contest_announcements"

    announcement_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    contest_id = db.Column(
        db.Integer,
        db.ForeignKey("contests.contest_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    author_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False
    )
    message = db.Column(db.Text, nullable=False)
    published_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    contest = db.relationship("Contest", back_populates="announcements")
    author = db.relationship("User")

    def __repr__(self):
        return f"<ContestAnnouncement {self.announcement_id}>"


# =====================================================
# TABLE 29: CONTEST_LEADERBOARD_ENTRIES
# Cached ranked score per contest/user
# =====================================================

class ContestLeaderboardEntry(db.Model):
    __tablename__ = "contest_leaderboard_entries"

    entry_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    contest_id = db.Column(
        db.Integer,
        db.ForeignKey("contests.contest_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    score = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    solved_count = db.Column(db.Integer, nullable=False, default=0)
    penalty_seconds = db.Column(db.Integer, nullable=False, default=0)
    rank_position = db.Column(db.Integer, nullable=True)

    contest = db.relationship("Contest", back_populates="leaderboard")
    user = db.relationship("User", backref="leaderboard_entries")

    __table_args__ = (
        db.UniqueConstraint(
            "contest_id", "user_id", name="uq_leaderboard_contest_user"
        ),
    )

    def __repr__(self):
        return f"<ContestLeaderboardEntry {self.contest_id}/{self.user_id}>"