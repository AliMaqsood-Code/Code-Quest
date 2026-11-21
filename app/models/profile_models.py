from app import db
from app.models.user_models import User, utc_now


# =====================================================
# TABLE 35: USER_FOLLOWS
# Bridge: users follow other users (self-referential)
# =====================================================

user_follows = db.Table(
    "user_follows",

    db.Column(
        "follower_id",
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    ),

    db.Column(
        "followed_id",
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    ),

    db.Column(
        "created_at",
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    ),

    db.CheckConstraint(
        "follower_id <> followed_id",
        name="ck_user_follows_not_self"
    )
)

# Attach the follow relationships to User without editing user_models.py
#   user.following -> users this user follows
#   user.followers -> users who follow this user
User.following = db.relationship(
    "User",
    secondary=user_follows,
    primaryjoin=User.user_id == user_follows.c.follower_id,
    secondaryjoin=User.user_id == user_follows.c.followed_id,
    backref="followers"
)


# =====================================================
# TABLE 7: USER_PROFILES
# Public/developer profile; one-to-one with users
# =====================================================

class UserProfile(db.Model):
    __tablename__ = "user_profiles"
    profile_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    display_name = db.Column(db.String(80), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    country = db.Column(db.String(80), nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    github_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    # Relationships

    user = db.relationship(
        "User",
        backref=db.backref(
            "profile",
            uselist=False,
            cascade="all, delete-orphan",
            passive_deletes=True
        )
    )

    links = db.relationship(
        "ProfileLink",
        back_populates="profile",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self):
        return f"<UserProfile {self.display_name}>"


# =====================================================
# TABLE 8: PROFILE_LINKS
# Additional external links on a developer profile
# =====================================================

class ProfileLink(db.Model):

    __tablename__ = "profile_links"

    link_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    profile_id = db.Column(
        db.Integer,
        db.ForeignKey("user_profiles.profile_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    label = db.Column(db.String(40), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    
    # Relationships
    profile = db.relationship("UserProfile", back_populates="links")

    def __repr__(self):
        return f"<ProfileLink {self.label}>"