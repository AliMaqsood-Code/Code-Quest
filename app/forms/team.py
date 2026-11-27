from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class TeamForm(FlaskForm):
    team_name = StringField("Team name", validators=[
        DataRequired(), Length(max=100),
    ])
    description = TextAreaField("Description",
                                validators=[Optional(), Length(max=1000)])


class GroupForm(FlaskForm):
    group_name = StringField("Group name", validators=[
        DataRequired(), Length(max=100),
    ])
    description = TextAreaField("Description",
                                validators=[Optional(), Length(max=1000)])


class InviteForm(FlaskForm):
    username = StringField("Username", validators=[
        DataRequired(), Length(max=30),
    ])


class JoinGroupForm(FlaskForm):
    code = StringField("Invite code", validators=[
        DataRequired(), Length(max=200),
    ])