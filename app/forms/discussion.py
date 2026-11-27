from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional
from wtforms.widgets import HiddenInput

REACTIONS = ["like", "helpful", "insightful"]


class DiscussionForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=180)])
    body = TextAreaField("Body", validators=[
        DataRequired(), Length(max=10_000),
    ])


class CommentForm(FlaskForm):
    body = TextAreaField("Comment", validators=[
        DataRequired(), Length(max=5_000),
    ])
    # Set when replying to another comment; empty for a top-level comment.
    parent_comment_id = IntegerField(
        widget=HiddenInput(), validators=[Optional()]
    )


class ReactionForm(FlaskForm):
    reaction_type = SelectField("Reaction", choices=REACTIONS)