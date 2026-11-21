from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField
from wtforms.validators import DataRequired, Length

from app.models import LanguageVersion, ProgrammingLanguage

STATUSES = [
    "queued", "running", "accepted", "wrong_answer",
    "runtime_error", "compile_error", "time_limit_exceeded",
]


class SubmissionForm(FlaskForm):
    language_version_id = SelectField("Language", coerce=int)
    source_code = TextAreaField("Code", validators=[
        DataRequired(), Length(max=100_000),
    ])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        versions = (
            LanguageVersion.query.join(ProgrammingLanguage)
            .filter(ProgrammingLanguage.is_enabled.is_(True))
            .order_by(ProgrammingLanguage.language_name,
                      LanguageVersion.version_label)
            .all()
        )
        self.language_version_id.choices = [
            (v.language_version_id,
             f"{v.language.language_name} {v.version_label}")
            for v in versions
        ]
        if not self.is_submitted():
            default = next((v for v in versions if v.is_default), None)
            if default:
                self.language_version_id.data = default.language_version_id


class ReviewForm(FlaskForm):
    status = SelectField("Result", choices=STATUSES)