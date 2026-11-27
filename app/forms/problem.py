import re

from flask_wtf import FlaskForm
from wtforms import (
    IntegerField, SelectField, SelectMultipleField, StringField, TextAreaField,
)
from wtforms.validators import (
    DataRequired, Length, NumberRange, Optional, Regexp, ValidationError,
)

from app import db
from app.models import Problem, ProblemCategory, ProblemTag

DIFFICULTIES = ["easy", "medium", "hard"]
VISIBILITIES = ["public", "private"]
STATUSES = ["draft", "published", "archived"]
RESERVED_SLUGS = {"new", "manage", "bookmarks", "categories", "tags"}


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def parse_tags(text):
    names = []
    for raw in (text or "").split(","):
        name = re.sub(r"\s+", "-", raw.strip().lower())
        if name and name not in names:
            names.append(name)
    return names


class ProblemForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=180)])
    slug = StringField("Slug (optional)", validators=[
        Optional(), Length(max=200),
        Regexp(r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
               message="Lowercase letters, numbers and hyphens only."),
    ])
    statement = TextAreaField("Statement", validators=[DataRequired()])
    difficulty = SelectField("Difficulty", choices=DIFFICULTIES)
    time_limit_ms = IntegerField("Time limit (ms)", default=1000, validators=[
        DataRequired(), NumberRange(min=1, max=10000),
    ])
    memory_limit_mb = IntegerField("Memory limit (MB)", default=256, validators=[
        DataRequired(), NumberRange(min=1, max=1024),
    ])
    visibility = SelectField("Visibility", choices=VISIBILITIES)
    status = SelectField("Status", choices=STATUSES)
    categories = SelectMultipleField("Categories", coerce=int)
    tags = StringField("Tags (comma separated)",
                       validators=[Optional(), Length(max=300)])

    def __init__(self, *args, problem=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.problem = problem
        self.final_slug = None
        self.categories.choices = [
            (c.category_id, c.category_name)
            for c in ProblemCategory.query.order_by(ProblemCategory.category_name)
        ]

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False

        self.final_slug = self.slug.data or slugify(self.title.data)
        if not self.final_slug or self.final_slug in RESERVED_SLUGS:
            self.slug.errors.append("Choose a different slug.")
            return False

        taken = Problem.query.filter_by(slug=self.final_slug)
        if self.problem:
            taken = taken.filter(Problem.problem_id != self.problem.problem_id)
        if taken.first():
            self.slug.errors.append("This slug is already in use.")
            return False

        if any(len(t) > 60 for t in parse_tags(self.tags.data)):
            self.tags.errors.append("Each tag must be 60 characters or fewer.")
            return False
        return True


class CategoryForm(FlaskForm):
    category_name = StringField("Name", validators=[DataRequired(), Length(max=80)])
    description = StringField("Description",
                              validators=[Optional(), Length(max=255)])
    parent_category_id = SelectField("Parent category", coerce=int, default=0)

    def __init__(self, *args, category=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.category = category
        query = ProblemCategory.query.order_by(ProblemCategory.category_name)
        if category:
            query = query.filter(
                ProblemCategory.category_id != category.category_id
            )
        self.parent_category_id.choices = [(0, "None")] + [
            (c.category_id, c.category_name) for c in query
        ]

    def validate_category_name(self, field):
        taken = ProblemCategory.query.filter_by(category_name=field.data.strip())
        if self.category:
            taken = taken.filter(
                ProblemCategory.category_id != self.category.category_id
            )
        if taken.first():
            raise ValidationError("Category name already exists.")

    def validate_parent_category_id(self, field):
        # The new parent must not be this category or one of its descendants.
        if not self.category or not field.data:
            return
        parent = db.session.get(ProblemCategory, field.data)
        while parent is not None:
            if parent.category_id == self.category.category_id:
                raise ValidationError("A category cannot sit under itself.")
            parent = parent.parent


class TagForm(FlaskForm):
    tag_name = StringField("Tag", validators=[
        DataRequired(), Length(max=60),
        Regexp(r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
               message="Lowercase letters, numbers and hyphens only."),
    ])

    def __init__(self, *args, tag=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tag = tag

    def validate_tag_name(self, field):
        taken = ProblemTag.query.filter_by(tag_name=field.data)
        if self.tag:
            taken = taken.filter(ProblemTag.tag_id != self.tag.tag_id)
        if taken.first():
            raise ValidationError("Tag already exists.")