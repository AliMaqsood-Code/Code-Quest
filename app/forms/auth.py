import re

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, Regexp, ValidationError,
)

from app.models import User


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[
        DataRequired(),
        Regexp(r"^[A-Za-z0-9_]{3,30}$",
               message="3-30 characters: letters, numbers or underscore."),
    ])
    email = StringField("Email", validators=[
        DataRequired(), Email(), Length(max=255),
    ])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm password", validators=[
        DataRequired(), EqualTo("password", message="Passwords must match."),
    ])

    def validate_username(self, field):
        if User.query.filter_by(username=field.data.strip()).first():
            raise ValidationError("Username is already taken.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError("Email is already registered.")

    def validate_password(self, field):
        pw = field.data
        if len(pw) < 8:
            raise ValidationError("Use at least 8 characters.")
        if len(pw.encode("utf-8")) > 72:
            raise ValidationError("Password is too long (72 bytes max).")
        if not re.search(r"[A-Za-z]", pw) or not re.search(r"\d", pw):
            raise ValidationError("Include at least one letter and one number.")


class LoginForm(FlaskForm):
    identifier = StringField("Username or email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])