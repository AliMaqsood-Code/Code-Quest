from app import db
from app.models.user_models import utc_now


# =====================================================
# TABLE 36: TEAMS
# =====================================================

class Team(db.Model):
    __tablename__ = "teams"

    team_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    team_name = db.Column(db.String(100), nullable=False)
    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    # Relationships
    owner = db.relationship("User", backref="owned_teams")

    members = db.relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    invitations = db.relationship(
        "TeamInvitation",
        back_populates="team",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self):
        return f"<Team {self.team_name}>"


# =====================================================
# TABLE 37: TEAM_MEMBERS
# Bridge with extra data (team_role, joined_at)
# =====================================================

class TeamMember(db.Model):
    __tablename__ = "team_members"

    team_id = db.Column(
        db.Integer,
        db.ForeignKey("teams.team_id", ondelete="CASCADE"),
        primary_key=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    )
    team_role = db.Column(db.String(20), nullable=False, default="member")
    joined_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    team = db.relationship("Team", back_populates="members")
    user = db.relationship("User", backref="team_memberships")

    def __repr__(self):
        return f"<TeamMember {self.team_id}/{self.user_id}>"


# =====================================================
# TABLE 38: TEAM_INVITATIONS
# Two FKs point to users, so each relationship names its FK
# =====================================================

class TeamInvitation(db.Model):
    __tablename__ = "team_invitations"

    team_invitation_id = db.Column(
        db.Integer, primary_key=True, autoincrement=True
    )
    team_id = db.Column(
        db.Integer,
        db.ForeignKey("teams.team_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    invited_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    invited_by = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    status = db.Column(db.String(20), nullable=False, default="pending")
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    team = db.relationship("Team", back_populates="invitations")
    invited_user = db.relationship(
        "User",
        foreign_keys=[invited_user_id],
        backref="team_invitations_received"
    )
    inviter = db.relationship(
        "User",
        foreign_keys=[invited_by],
        backref="team_invitations_sent"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "team_id", "invited_user_id", name="uq_team_invitation"
        ),
    )

    def __repr__(self):
        return f"<TeamInvitation {self.team_id}/{self.invited_user_id}>"


# =====================================================
# TABLE 39: PRIVATE_GROUPS
# =====================================================

class PrivateGroup(db.Model):
    __tablename__ = "private_groups"

    group_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_name = db.Column(db.String(100), nullable=False)
    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    description = db.Column(db.Text, nullable=True)
    invite_code_hash = db.Column(db.String(255), nullable=True, unique=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    # Relationships
    owner = db.relationship("User", backref="owned_groups")

    members = db.relationship(
        "GroupMember",
        back_populates="group",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    invitations = db.relationship(
        "GroupInvitation",
        back_populates="group",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self):
        return f"<PrivateGroup {self.group_name}>"


# =====================================================
# TABLE 40: GROUP_MEMBERS
# Bridge with extra data (member_role, joined_at)
# =====================================================

class GroupMember(db.Model):
    __tablename__ = "group_members"

    group_id = db.Column(
        db.Integer,
        db.ForeignKey("private_groups.group_id", ondelete="CASCADE"),
        primary_key=True
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    )
    member_role = db.Column(db.String(20), nullable=False, default="member")
    joined_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    group = db.relationship("PrivateGroup", back_populates="members")
    user = db.relationship("User", backref="group_memberships")

    def __repr__(self):
        return f"<GroupMember {self.group_id}/{self.user_id}>"


# =====================================================
# TABLE 41: GROUP_INVITATIONS
# =====================================================

class GroupInvitation(db.Model):
    __tablename__ = "group_invitations"

    group_invitation_id = db.Column(
        db.Integer, primary_key=True, autoincrement=True
    )
    group_id = db.Column(
        db.Integer,
        db.ForeignKey("private_groups.group_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    invited_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    invited_by = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    status = db.Column(db.String(20), nullable=False, default="pending")
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    group = db.relationship("PrivateGroup", back_populates="invitations")
    invited_user = db.relationship(
        "User",
        foreign_keys=[invited_user_id],
        backref="group_invitations_received"
    )
    inviter = db.relationship(
        "User",
        foreign_keys=[invited_by],
        backref="group_invitations_sent"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "group_id", "invited_user_id", name="uq_group_invitation"
        ),
    )

    def __repr__(self):
        return f"<GroupInvitation {self.group_id}/{self.invited_user_id}>"