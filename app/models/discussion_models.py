from app import db
from app.models.user_models import utc_now


# =====================================================
# TABLE 30: DISCUSSIONS
# Threads attached to a problem (problem_id set) or general forum (NULL)
# =====================================================

class Discussion(db.Model):
    __tablename__ = "discussions"

    discussion_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    problem_id = db.Column(
        db.Integer,
        db.ForeignKey("problems.problem_id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    title = db.Column(db.String(180), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )
    is_locked = db.Column(db.Boolean, nullable=False, default=False)

    # Relationships
    user = db.relationship("User", backref="discussions")
    problem = db.relationship("Problem", backref="discussions")

    comments = db.relationship(
        "DiscussionComment",
        back_populates="discussion",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self):
        return f"<Discussion {self.title}>"


# =====================================================
# TABLE 31: DISCUSSION_COMMENTS
# Supports nested replies through parent_comment_id
# =====================================================

class DiscussionComment(db.Model):
    __tablename__ = "discussion_comments"

    comment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    discussion_id = db.Column(
        db.Integer,
        db.ForeignKey("discussions.discussion_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    parent_comment_id = db.Column(
        db.Integer,
        db.ForeignKey("discussion_comments.comment_id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )
    is_edited = db.Column(db.Boolean, nullable=False, default=False)

    # Relationships
    discussion = db.relationship("Discussion", back_populates="comments")
    user = db.relationship("User", backref="discussion_comments")

    replies = db.relationship(
        "DiscussionComment",
        backref=db.backref("parent", remote_side=[comment_id]),
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    reactions = db.relationship(
        "DiscussionReaction",
        back_populates="comment",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self):
        return f"<DiscussionComment {self.comment_id}>"


# =====================================================
# TABLE 32: DISCUSSION_REACTIONS
# One reaction per user / comment / type
# =====================================================

class DiscussionReaction(db.Model):
    __tablename__ = "discussion_reactions"

    reaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    comment_id = db.Column(
        db.Integer,
        db.ForeignKey("discussion_comments.comment_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    reaction_type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    comment = db.relationship("DiscussionComment", back_populates="reactions")
    user = db.relationship("User")

    __table_args__ = (
        db.UniqueConstraint(
            "comment_id", "user_id", "reaction_type",
            name="uq_reaction_comment_user_type"
        ),
    )

    def __repr__(self):
        return f"<DiscussionReaction {self.reaction_type}>"


# =====================================================
# TABLE 33: PUBLISHED_SOLUTIONS
# Editorial or community solutions for problems
# =====================================================

class PublishedSolution(db.Model):
    __tablename__ = "published_solutions"

    solution_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    problem_id = db.Column(
        db.Integer,
        db.ForeignKey("problems.problem_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    author_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    language_version_id = db.Column(
        db.Integer,
        db.ForeignKey("language_versions.language_version_id", ondelete="RESTRICT"),
        nullable=False
    )
    title = db.Column(db.String(160), nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    source_code = db.Column(db.Text, nullable=False)
    is_official = db.Column(db.Boolean, nullable=False, default=False)
    published_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    # Relationships
    problem = db.relationship("Problem", backref="solutions")
    author = db.relationship("User", backref="published_solutions")
    language_version = db.relationship("LanguageVersion")

    votes = db.relationship(
        "SolutionVote",
        back_populates="solution",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self):
        return f"<PublishedSolution {self.title}>"


# =====================================================
# TABLE 34: SOLUTION_VOTES
# Bridge with extra data (vote_value); one vote per user/solution
# =====================================================

class SolutionVote(db.Model):
    __tablename__ = "solution_votes"

    solution_id = db.Column(
        db.Integer,
        db.ForeignKey("published_solutions.solution_id", ondelete="CASCADE"),
        primary_key=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    )
    vote_value = db.Column(db.SmallInteger, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    solution = db.relationship("PublishedSolution", back_populates="votes")
    user = db.relationship("User", backref="solution_votes")

    __table_args__ = (
        db.CheckConstraint(
            "vote_value IN (-1, 1)",
            name="ck_solution_vote_value"
        ),
    )

    def __repr__(self):
        return f"<SolutionVote {self.solution_id}/{self.user_id} {self.vote_value}>"