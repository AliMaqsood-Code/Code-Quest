from app import db


# =====================================================
# TABLE 9: PROGRAMMING_LANGUAGES
# Supported language catalogue
# =====================================================

class ProgrammingLanguage(db.Model):
    __tablename__ = "programming_languages"
    language_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    language_name = db.Column(db.String(40), nullable=False, unique=True)
    slug = db.Column(db.String(40), nullable=False, unique=True)
    is_enabled = db.Column(db.Boolean, nullable=False, default=True)

    # Relationships
    versions = db.relationship(
        "LanguageVersion",
        back_populates="language",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self):
        return f"<ProgrammingLanguage {self.language_name}>"


# =====================================================
# TABLE 10: LANGUAGE_VERSIONS
# Compiler/runtime versions available for each language
# =====================================================

class LanguageVersion(db.Model):
    __tablename__ = "language_versions"
    language_version_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    language_id = db.Column(
        db.Integer,
        db.ForeignKey("programming_languages.language_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    version_label = db.Column(db.String(40), nullable=False)
    runtime_image = db.Column(db.String(150), nullable=True)
    is_default = db.Column(db.Boolean, nullable=False, default=False)

    # Relationships
    language = db.relationship(
        "ProgrammingLanguage",
        back_populates="versions"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "language_id",
            "version_label",
            name="uq_language_version"
        ),
    )

    def __repr__(self):
        return f"<LanguageVersion {self.language_id} {self.version_label}>"