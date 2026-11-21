from app import db
from app.models.user_models import User, utc_now


# =====================================================
# BRIDGE TABLES
# TABLE 14: PROBLEM_CATEGORY_MAP
# TABLE 16: PROBLEM_TAG_MAP
# TABLE 50: USER_PROBLEM_BOOKMARKS
# =====================================================

problem_category_map = db.Table(
    "problem_category_map",
    db.Column(
        "problem_id", db.Integer,
        db.ForeignKey("problems.problem_id", ondelete="CASCADE"),
        primary_key=True
    ),
    db.Column(
        "category_id", db.Integer,
        db.ForeignKey("problem_categories.category_id", ondelete="CASCADE"),
        primary_key=True
    )
)

problem_tag_map = db.Table(
    "problem_tag_map",
    db.Column(
        "problem_id", db.Integer,
        db.ForeignKey("problems.problem_id", ondelete="CASCADE"),
        primary_key=True
    ),
    db.Column(
        "tag_id", db.Integer,
        db.ForeignKey("problem_tags.tag_id", ondelete="CASCADE"),
        primary_key=True
    )
)

user_problem_bookmarks = db.Table(
    "user_problem_bookmarks",
    db.Column(
        "user_id", db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    ),
    db.Column(
        "problem_id", db.Integer,
        db.ForeignKey("problems.problem_id", ondelete="CASCADE"),
        primary_key=True
    ),
    db.Column(
        "created_at", db.DateTime(timezone=True),
        nullable=False, default=utc_now
    )
)

# user.bookmarked_problems / problem.bookmarked_by
User.bookmarked_problems = db.relationship(
    "Problem",
    secondary=user_problem_bookmarks,
    backref="bookmarked_by"
)


# =====================================================
# TABLE 11: PROBLEMS
# =====================================================

class Problem(db.Model):
    __tablename__ = "problems"

    problem_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    author_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    title = db.Column(db.String(180), nullable=False)
    slug = db.Column(db.String(200), nullable=False, unique=True, index=True)
    statement = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(20), nullable=False, index=True)
    time_limit_ms = db.Column(db.Integer, nullable=False)
    memory_limit_mb = db.Column(db.Integer, nullable=False)
    visibility = db.Column(db.String(20), nullable=False, default="public")
    status = db.Column(db.String(20), nullable=False, default="draft")
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    # Relationships
    author = db.relationship("User", backref="authored_problems")

    versions = db.relationship(
        "ProblemVersion", back_populates="problem",
        cascade="all, delete-orphan", passive_deletes=True
    )
    hints = db.relationship(
        "ProblemHint", back_populates="problem",
        cascade="all, delete-orphan", passive_deletes=True
    )
    examples = db.relationship(
        "ProblemExample", back_populates="problem",
        cascade="all, delete-orphan", passive_deletes=True
    )
    test_cases = db.relationship(
        "TestCase", back_populates="problem",
        cascade="all, delete-orphan", passive_deletes=True
    )
    categories = db.relationship(
        "ProblemCategory", secondary=problem_category_map,
        back_populates="problems"
    )
    tags = db.relationship(
        "ProblemTag", secondary=problem_tag_map,
        back_populates="problems"
    )

    __table_args__ = (
        db.CheckConstraint(
            "difficulty IN ('easy', 'medium', 'hard')",
            name="ck_problem_difficulty"
        ),
        db.CheckConstraint(
            "visibility IN ('public', 'private')",
            name="ck_problem_visibility"
        ),
        db.CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="ck_problem_status"
        ),
        db.CheckConstraint(
            "time_limit_ms > 0 AND memory_limit_mb > 0",
            name="ck_problem_limits_positive"
        ),
    )

    def __repr__(self):
        return f"<Problem {self.slug}>"


# =====================================================
# TABLE 12: PROBLEM_VERSIONS
# =====================================================

class ProblemVersion(db.Model):
    __tablename__ = "problem_versions"

    problem_version_id = db.Column(
        db.Integer, primary_key=True, autoincrement=True
    )
    problem_id = db.Column(
        db.Integer,
        db.ForeignKey("problems.problem_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    version_no = db.Column(db.Integer, nullable=False)
    statement_snapshot = db.Column(db.Text, nullable=False)
    edited_by = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    problem = db.relationship("Problem", back_populates="versions")
    editor = db.relationship("User")

    __table_args__ = (
        db.UniqueConstraint(
            "problem_id", "version_no", name="uq_problem_version"
        ),
    )

    def __repr__(self):
        return f"<ProblemVersion {self.problem_id} v{self.version_no}>"


# =====================================================
# TABLE 13: PROBLEM_CATEGORIES
# Self-referential hierarchy via parent_category_id
# =====================================================

class ProblemCategory(db.Model):
    __tablename__ = "problem_categories"

    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_name = db.Column(db.String(80), nullable=False, unique=True)
    description = db.Column(db.String(255), nullable=True)
    parent_category_id = db.Column(
        db.Integer,
        db.ForeignKey("problem_categories.category_id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    parent = db.relationship(
        "ProblemCategory",
        remote_side=[category_id],
        backref="children"
    )
    problems = db.relationship(
        "Problem", secondary=problem_category_map,
        back_populates="categories"
    )

    def __repr__(self):
        return f"<ProblemCategory {self.category_name}>"


# =====================================================
# TABLE 15: PROBLEM_TAGS
# =====================================================

class ProblemTag(db.Model):
    __tablename__ = "problem_tags"

    tag_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tag_name = db.Column(db.String(60), nullable=False, unique=True)

    problems = db.relationship(
        "Problem", secondary=problem_tag_map,
        back_populates="tags"
    )

    def __repr__(self):
        return f"<ProblemTag {self.tag_name}>"


# =====================================================
# TABLE 17: PROBLEM_HINTS
# =====================================================

class ProblemHint(db.Model):
    __tablename__ = "problem_hints"

    hint_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    problem_id = db.Column(
        db.Integer,
        db.ForeignKey("problems.problem_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    hint_order = db.Column(db.Integer, nullable=False)
    hint_text = db.Column(db.Text, nullable=False)

    problem = db.relationship("Problem", back_populates="hints")

    __table_args__ = (
        db.UniqueConstraint(
            "problem_id", "hint_order", name="uq_problem_hint_order"
        ),
    )

    def __repr__(self):
        return f"<ProblemHint {self.problem_id} #{self.hint_order}>"


# =====================================================
# TABLE 18: TEST_CASES
# =====================================================

class TestCase(db.Model):
    __tablename__ = "test_cases"
    __test__ = False  # stop pytest from collecting this as a test class

    test_case_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    problem_id = db.Column(
        db.Integer,
        db.ForeignKey("problems.problem_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    case_name = db.Column(db.String(80), nullable=False)
    input_data = db.Column(db.Text, nullable=False)
    expected_output = db.Column(db.Text, nullable=False)
    is_sample = db.Column(db.Boolean, nullable=False, default=False)
    is_hidden = db.Column(db.Boolean, nullable=False, default=True)
    weight = db.Column(db.Numeric(6, 2), nullable=False, default=1)

    problem = db.relationship("Problem", back_populates="test_cases")

    def __repr__(self):
        return f"<TestCase {self.case_name}>"


# =====================================================
# TABLE 19: PROBLEM_EXAMPLES
# =====================================================

class ProblemExample(db.Model):
    __tablename__ = "problem_examples"

    example_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    problem_id = db.Column(
        db.Integer,
        db.ForeignKey("problems.problem_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    example_order = db.Column(db.Integer, nullable=False)
    input_text = db.Column(db.Text, nullable=False)
    output_text = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text, nullable=True)

    problem = db.relationship("Problem", back_populates="examples")

    __table_args__ = (
        db.UniqueConstraint(
            "problem_id", "example_order", name="uq_problem_example_order"
        ),
    )

    def __repr__(self):
        return f"<ProblemExample {self.problem_id} #{self.example_order}>"