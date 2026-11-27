from flask_wtf import FlaskForm
from wtforms import (
    BooleanField, IntegerField, SelectField, StringField, TextAreaField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from app.models import Problem

PROGRESS_STATUSES = ["not_started", "in_progress", "completed"]


class LearningPathForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=160)])
    description = TextAreaField("Description",
                                validators=[Optional(), Length(max=5000)])
    difficulty = SelectField("Difficulty", choices=[
        ("", "Any"), ("easy", "easy"), ("medium", "medium"), ("hard", "hard"),
    ])
    is_published = BooleanField("Published")


class StepForm(FlaskForm):
    step_title = StringField("Step title", validators=[
        DataRequired(), Length(max=160),
    ])
    instructions = TextAreaField("Instructions",
                                 validators=[Optional(), Length(max=5000)])
    sequence_no = IntegerField("Order", validators=[
        Optional(), NumberRange(min=1, max=1000),
    ])
    problem_id = SelectField("Problem", coerce=int, default=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.problem_id.choices = [(0, "No problem")] + [
            (p.problem_id, p.title)
            for p in Problem.query.filter_by(status="published")
            .order_by(Problem.title)
        ]


class ProgressForm(FlaskForm):
    status = SelectField("Status", choices=PROGRESS_STATUSES)


class PreferencesForm(FlaskForm):
    email_enabled = BooleanField("Email notifications")
    contest_alerts = BooleanField("Contest alerts")
    submission_alerts = BooleanField("Submission alerts")
    discussion_alerts = BooleanField("Discussion alerts")