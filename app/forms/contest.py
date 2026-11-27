from flask_wtf import FlaskForm
from wtforms import (
    DateTimeLocalField, IntegerField, SelectField, StringField, TextAreaField,
)
from wtforms.validators import (
    DataRequired, Length, NumberRange, Optional, ValidationError,
)

from app.models import Problem


class ContestForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=160)])
    description = TextAreaField("Description",
                                validators=[Optional(), Length(max=5000)])
    starts_at = DateTimeLocalField("Starts at (UTC)",
                                   validators=[DataRequired()])
    ends_at = DateTimeLocalField("Ends at (UTC)", validators=[DataRequired()])
    visibility = SelectField("Visibility", choices=["public", "private"])

    def validate_ends_at(self, field):
        if self.starts_at.data and field.data <= self.starts_at.data:
            raise ValidationError("End time must be after the start time.")


class ContestProblemEditForm(FlaskForm):
    points = IntegerField("Points", validators=[
        DataRequired(), NumberRange(min=1, max=10000),
    ])
    sequence_no = IntegerField("Order", validators=[
        Optional(), NumberRange(min=1, max=1000),
    ])


class ContestProblemForm(ContestProblemEditForm):
    problem_id = SelectField("Problem", coerce=int)

    def __init__(self, *args, exclude_ids=(), **kwargs):
        super().__init__(*args, **kwargs)
        query = Problem.query.filter_by(status="published")
        if exclude_ids:
            query = query.filter(Problem.problem_id.notin_(exclude_ids))
        self.problem_id.choices = [
            (p.problem_id, p.title) for p in query.order_by(Problem.title)
        ]


class AnnouncementForm(FlaskForm):
    message = TextAreaField("Announcement", validators=[
        DataRequired(), Length(max=2000),
    ])