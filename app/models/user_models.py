
from datetime import datetime, timezone

from app import db
from app.utils.hashing import hash_password, verify_password
from app.utils.tokenManagement import generate_token, hash_token


def utc_now():
    return datetime.now(timezone.utc)


# =====================================================
# TABLE 4: USER_ROLES
# Many-to-many relationship between users and roles
# =====================================================

user_roles = db.Table(
    "user_roles",

    db.Column(
        "user_id",
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    ),

    db.Column(
        "role_id",
        db.Integer,
        db.ForeignKey("roles.role_id", ondelete="CASCADE"),
        primary_key=True
    ),

    db.Column(
        "assigned_at",
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )
)


# =====================================================
# TABLE 5: ROLE_PERMISSIONS
# Many-to-many relationship between roles and permissions
# =====================================================

role_permissions = db.Table(
    "role_permissions",

    db.Column(
        "role_id",
        db.Integer,
        db.ForeignKey("roles.role_id", ondelete="CASCADE"),
        primary_key=True
    ),

    db.Column(
        "permission_id",
        db.Integer,
        db.ForeignKey("permissions.permission_id", ondelete="CASCADE"),
        primary_key=True
    )
)


# =====================================================
# TABLE 1: USERS
# Core login identity
# =====================================================

class User(db.Model):

    __tablename__ = "users"

    user_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    username = db.Column(
        db.String(30),
        nullable=False,
        unique=True,
        index=True
    )

    email = db.Column(
        db.String(255),
        nullable=False,
        unique=True,
        index=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    email_verified_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    # Relationships

    roles = db.relationship(
        "Role",
        secondary=user_roles,
        back_populates="users"
    )

    sessions = db.relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    audit_logs = db.relationship(
        "AuditLog",
        back_populates="actor",
        passive_deletes=True
    )

    # Password hashing

    def set_password(self, password):

        self.password_hash = hash_password(password)


    def check_password(self, password):

        return verify_password(
            password,
            self.password_hash
        )

    def has_role(self, role_name):

        return any(
            role.role_name == role_name
            for role in self.roles
        )

    def has_permission(self, permission_key):

        return any(
            permission.permission_key == permission_key
            for role in self.roles
            for permission in role.permissions
        )

    def __repr__(self):

        return f"<User {self.username}>"


# =====================================================
# TABLE 2: ROLES
# =====================================================

class Role(db.Model):

    __tablename__ = "roles"

    role_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    role_name = db.Column(
        db.String(40),
        nullable=False,
        unique=True
    )

    description = db.Column(
        db.String(255),
        nullable=True
    )

    # Relationships

    users = db.relationship(
        "User",
        secondary=user_roles,
        back_populates="roles"
    )

    permissions = db.relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles"
    )

    def __repr__(self):

        return f"<Role {self.role_name}>"


# =====================================================
# TABLE 3: PERMISSIONS
# =====================================================

class Permission(db.Model):

    __tablename__ = "permissions"

    permission_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    permission_key = db.Column(
        db.String(80),
        nullable=False,
        unique=True
    )

    description = db.Column(
        db.String(255),
        nullable=True
    )

    # Relationships

    roles = db.relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )

    def __repr__(self):

        return f"<Permission {self.permission_key}>"


# =====================================================
# TABLE 6: USER_SESSIONS
# Stores hashed session tokens
# =====================================================

class UserSession(db.Model):

    __tablename__ = "user_sessions"

    session_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    token_hash = db.Column(
        db.String(255),
        nullable=False,
        unique=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    expires_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False
    )

    revoked_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    user = db.relationship(
        "User",
        back_populates="sessions"
    )

    __table_args__ = (
        db.CheckConstraint(
            "expires_at > created_at",
            name="check_session_expiry"
        ),
    )

    def is_valid(self):

        return (
            self.revoked_at is None
            and self.expires_at > utc_now()
        )

    def revoke(self):

        self.revoked_at = utc_now()

    def __repr__(self):

        return f"<UserSession {self.session_id}>"


# =====================================================
# TABLE 51: AUDIT_LOGS
# Tracks important security and administrative actions
# =====================================================

class AuditLog(db.Model):

    __tablename__ = "audit_logs"

    audit_log_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    actor_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    action = db.Column(
        db.String(100),
        nullable=False
    )

    entity_type = db.Column(
        db.String(60),
        nullable=False
    )

    entity_id = db.Column(
        db.Integer,
        nullable=True
    )

    ip_address = db.Column(
        db.String(45),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True
    )

    actor = db.relationship(
        "User",
        back_populates="audit_logs"
    )

    def __repr__(self):

        return f"<AuditLog {self.action}>"
