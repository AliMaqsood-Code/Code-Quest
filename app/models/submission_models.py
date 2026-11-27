from app import db
from app.models.user_models import utc_now


# =====================================================
# TABLE 20: SUBMISSIONS
# A user's attempt to solve a problem
# status: queued / running / accepted / wrong_answer / ...
# =====================================================

class Submission(db.Model):
    __tablename__ = "submissions"

    submission_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    problem_id = db.Column(
        db.Integer,
        db.ForeignKey("problems.problem_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    language_version_id = db.Column(
        db.Integer,
        db.ForeignKey("language_versions.language_version_id", ondelete="RESTRICT"),
        nullable=False
    )
    source_code = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="queued")
    submitted_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True
    )
    contest_id = db.Column(
        db.Integer,
        db.ForeignKey("contests.contest_id", ondelete="RESTRICT"),
        nullable=True,
        index=True
    )

    # Relationships
    user = db.relationship("User", backref="submissions")
    problem = db.relationship("Problem", backref="submissions")
    language_version = db.relationship("LanguageVersion", backref="submissions")
    contest = db.relationship("Contest", backref="submissions")

    files = db.relationship(
        "SubmissionFile",
        back_populates="submission",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    execution = db.relationship(
        "CodeExecution",
        back_populates="submission",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self):
        return f"<Submission {self.submission_id} {self.status}>"


# =====================================================
# TABLE 21: SUBMISSION_FILES
# Optional supporting files attached to a submission
# =====================================================

class SubmissionFile(db.Model):
    __tablename__ = "submission_files"

    submission_file_id = db.Column(
        db.Integer, primary_key=True, autoincrement=True
    )
    submission_id = db.Column(
        db.Integer,
        db.ForeignKey("submissions.submission_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    file_name = db.Column(db.String(255), nullable=False)
    storage_key = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    submission = db.relationship("Submission", back_populates="files")

    def __repr__(self):
        return f"<SubmissionFile {self.file_name}>"


# =====================================================
# TABLE 22: CODE_EXECUTIONS
# Execution job + aggregate result; one-to-one with submission
# =====================================================

class CodeExecution(db.Model):
    __tablename__ = "code_executions"

    execution_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    submission_id = db.Column(
        db.Integer,
        db.ForeignKey("submissions.submission_id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    started_at = db.Column(db.DateTime(timezone=True), nullable=True)
    finished_at = db.Column(db.DateTime(timezone=True), nullable=True)
    overall_result = db.Column(db.String(30), nullable=False, default="queued")
    total_runtime_ms = db.Column(db.Integer, nullable=True)
    peak_memory_kb = db.Column(db.Integer, nullable=True)
    exit_code = db.Column(db.Integer, nullable=True)

    submission = db.relationship("Submission", back_populates="execution")

    test_results = db.relationship(
        "ExecutionTestResult",
        back_populates="execution",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    logs = db.relationship(
        "ExecutionLog",
        back_populates="execution",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self):
        return f"<CodeExecution {self.execution_id} {self.overall_result}>"


# =====================================================
# TABLE 23: EXECUTION_TEST_RESULTS
# Per-test-case outcome for an execution
# =====================================================

class ExecutionTestResult(db.Model):
    __tablename__ = "execution_test_results"

    execution_test_result_id = db.Column(
        db.Integer, primary_key=True, autoincrement=True
    )
    execution_id = db.Column(
        db.Integer,
        db.ForeignKey("code_executions.execution_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    test_case_id = db.Column(
        db.Integer,
        db.ForeignKey("test_cases.test_case_id", ondelete="RESTRICT"),
        nullable=False
    )
    result_status = db.Column(db.String(30), nullable=False)
    runtime_ms = db.Column(db.Integer, nullable=True)
    memory_kb = db.Column(db.Integer, nullable=True)
    actual_output = db.Column(db.Text, nullable=True)

    execution = db.relationship("CodeExecution", back_populates="test_results")
    test_case = db.relationship("TestCase")

    __table_args__ = (
        db.UniqueConstraint(
            "execution_id", "test_case_id", name="uq_execution_test_case"
        ),
    )

    def __repr__(self):
        return f"<ExecutionTestResult {self.execution_id}/{self.test_case_id}>"


# =====================================================
# TABLE 24: EXECUTION_LOGS
# Compiler/runtime diagnostics for an execution
# =====================================================

class ExecutionLog(db.Model):
    __tablename__ = "execution_logs"

    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    execution_id = db.Column(
        db.Integer,
        db.ForeignKey("code_executions.execution_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    log_level = db.Column(db.String(20), nullable=False)
    log_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=utc_now
    )

    execution = db.relationship("CodeExecution", back_populates="logs")

    def __repr__(self):
        return f"<ExecutionLog {self.log_level}>"