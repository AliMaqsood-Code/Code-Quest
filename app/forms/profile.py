from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, ValidationError


def http_url(form, field):
    value = (field.data or "").strip().lower()
    if not value.startswith(("http://", "https://")):
        raise ValidationError(
            "Enter a full URL starting with http:// or https://"
        )


class ProfileForm(FlaskForm):
    display_name = StringField("Display name", validators=[
        DataRequired(), Length(max=80),
    ])
    bio = TextAreaField("Bio", validators=[Optional(), Length(max=1000)])
    country = StringField("Country", validators=[Optional(), Length(max=80)])
    avatar_url = StringField("Avatar URL", validators=[
        Optional(), Length(max=500), http_url,
    ])
    github_url = StringField("GitHub URL", validators=[
        Optional(), Length(max=500), http_url,
    ])


class LinkForm(FlaskForm):
    label = StringField("Label", validators=[DataRequired(), Length(max=40)])
    url = StringField("URL", validators=[
        DataRequired(), Length(max=500), http_url,
    ])