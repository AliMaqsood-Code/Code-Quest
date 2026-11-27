from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length

from app.models import LanguageVersion, ProgrammingLanguage


class SolutionForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=160)])
    language_version_id = SelectField("Language", coerce=int)
    explanation = TextAreaField("Explanation", validators=[
        DataRequired(), Length(max=10_000),
    ])
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


class VoteForm(FlaskForm):
    vote_value = SelectField("Vote", coerce=int,
                             choices=[(1, "Upvote"), (-1, "Downvote")])