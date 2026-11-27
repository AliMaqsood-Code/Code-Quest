from flask import (
    Blueprint, abort, flash, g, redirect, render_template, request, url_for,
)

from app import db
from app.forms.problem import (
    DIFFICULTIES, CategoryForm, ProblemForm, TagForm, parse_tags,
)
from app.models import Problem, ProblemCategory, ProblemTag, ProblemVersion
from app.utils.auth import log_action, login_required, permission_required
from app.utils.contest import can_view_contest_problem

problems_bp = Blueprint("problems", __name__, url_prefix="/problems")


def _visible(problem):
    """Published public problems are open to everyone; others only to the
    author, users who can manage problems, and registered contest
    participants once the contest has started."""
    if problem.status == "published" and problem.visibility == "public":
        return True
    user = g.current_user
    if user is None:
        return False
    if problem.author_id == user.user_id or user.has_permission("problem.manage"):
        return True
    return problem.status != "draft" and can_view_contest_problem(user, problem)


def _get_visible(slug):
    problem = Problem.query.filter_by(slug=slug).first_or_404()
    if not _visible(problem):
        abort(404)
    return problem


def _apply_relations(problem, form):
    problem.categories = ProblemCategory.query.filter(
        ProblemCategory.category_id.in_(form.categories.data)
    ).all()

    tags = []
    for name in parse_tags(form.tags.data):
        tag = ProblemTag.query.filter_by(tag_name=name).first()
        if tag is None:
            tag = ProblemTag(tag_name=name)
            db.session.add(tag)
        tags.append(tag)
    problem.tags = tags


# =====================================================
# PROBLEMS: read
# =====================================================

@problems_bp.get("/")
def index():
    difficulty = request.args.get("difficulty")
    category_id = request.args.get("category", type=int)
    search = (request.args.get("q") or "").strip()

    query = Problem.query.filter_by(status="published", visibility="public")
    if difficulty in DIFFICULTIES:
        query = query.filter_by(difficulty=difficulty)
    if category_id:
        query = query.filter(
            Problem.categories.any(ProblemCategory.category_id == category_id)
        )
    if search:
        query = query.filter(Problem.title.ilike(f"%{search}%"))

    return render_template(
        "problems/list.html",
        problems=query.order_by(Problem.created_at.desc()).all(),
        categories=ProblemCategory.query.order_by(
            ProblemCategory.category_name
        ).all(),
        difficulty=difficulty,
        category_id=category_id,
        search=search,
    )


@problems_bp.get("/manage")
@permission_required("problem.manage")
def manage():
    problems = Problem.query.order_by(Problem.created_at.desc()).all()
    return render_template("problems/manage.html", problems=problems)


@problems_bp.get("/bookmarks")
@login_required
def bookmarks():
    problems = [p for p in g.current_user.bookmarked_problems if _visible(p)]
    return render_template("problems/bookmarks.html", problems=problems)


@problems_bp.get("/<slug>")
def detail(slug):
    problem = _get_visible(slug)
    user = g.current_user
    return render_template(
        "problems/detail.html",
        problem=problem,
        examples=sorted(problem.examples, key=lambda e: e.example_order),
        hints=sorted(problem.hints, key=lambda h: h.hint_order),
        bookmarked=user is not None and problem in user.bookmarked_problems,
    )


# =====================================================
# PROBLEMS: create / update / archive (problem.manage)
# =====================================================

@problems_bp.route("/new", methods=["GET", "POST"])
@permission_required("problem.manage")
def create():
    form = ProblemForm()
    if form.validate_on_submit():
        user = g.current_user
        problem = Problem(
            author_id=user.user_id,
            title=form.title.data.strip(),
            slug=form.final_slug,
            statement=form.statement.data,
            difficulty=form.difficulty.data,
            time_limit_ms=form.time_limit_ms.data,
            memory_limit_mb=form.memory_limit_mb.data,
            visibility=form.visibility.data,
            status=form.status.data,
        )
        _apply_relations(problem, form)
        problem.versions = [ProblemVersion(
            version_no=1,
            statement_snapshot=problem.statement,
            edited_by=user.user_id,
        )]
        db.session.add(problem)
        db.session.flush()
        log_action("problem.create", "problem", problem.problem_id,
                   user.user_id)
        db.session.commit()

        flash("Problem created.", "success")
        return redirect(url_for("problems.detail", slug=problem.slug))

    return render_template("problems/form.html", form=form, problem=None)


@problems_bp.route("/<slug>/edit", methods=["GET", "POST"])
@permission_required("problem.manage")
def edit(slug):
    problem = Problem.query.filter_by(slug=slug).first_or_404()
    form = ProblemForm(obj=problem, problem=problem)

    if request.method == "GET":
        form.categories.data = [c.category_id for c in problem.categories]
        form.tags.data = ", ".join(t.tag_name for t in problem.tags)

    if form.validate_on_submit():
        user = g.current_user
        statement_changed = form.statement.data != problem.statement

        problem.title = form.title.data.strip()
        problem.slug = form.final_slug
        problem.statement = form.statement.data
        problem.difficulty = form.difficulty.data
        problem.time_limit_ms = form.time_limit_ms.data
        problem.memory_limit_mb = form.memory_limit_mb.data
        problem.visibility = form.visibility.data
        problem.status = form.status.data
        _apply_relations(problem, form)

        if statement_changed:
            next_no = max((v.version_no for v in problem.versions),
                          default=0) + 1
            problem.versions.append(ProblemVersion(
                version_no=next_no,
                statement_snapshot=problem.statement,
                edited_by=user.user_id,
            ))

        log_action("problem.update", "problem", problem.problem_id,
                   user.user_id)
        db.session.commit()

        flash("Problem updated.", "success")
        return redirect(url_for("problems.detail", slug=problem.slug))

    return render_template("problems/form.html", form=form, problem=problem)


@problems_bp.post("/<slug>/archive")
@permission_required("problem.manage")
def archive(slug):
    problem = Problem.query.filter_by(slug=slug).first_or_404()
    problem.status = "archived"
    log_action("problem.archive", "problem", problem.problem_id,
               g.current_user.user_id)
    db.session.commit()

    flash("Problem archived.", "info")
    return redirect(url_for("problems.manage"))


# =====================================================
# BOOKMARKS (any logged-in user)
# =====================================================

@problems_bp.post("/<slug>/bookmark")
@login_required
def toggle_bookmark(slug):
    problem = _get_visible(slug)
    user = g.current_user

    if problem in user.bookmarked_problems:
        user.bookmarked_problems.remove(problem)
        flash("Bookmark removed.", "info")
    else:
        user.bookmarked_problems.append(problem)
        flash("Problem bookmarked.", "success")

    db.session.commit()
    return redirect(url_for("problems.detail", slug=slug))


# =====================================================
# CATEGORIES (problem.manage): list + create, edit, delete
# =====================================================

@problems_bp.route("/categories", methods=["GET", "POST"])
@permission_required("problem.manage")
def categories():
    form = CategoryForm()
    if form.validate_on_submit():
        category = ProblemCategory(
            category_name=form.category_name.data.strip(),
            description=form.description.data or None,
            parent_category_id=form.parent_category_id.data or None,
        )
        db.session.add(category)
        db.session.flush()
        log_action("category.create", "problem_category",
                   category.category_id, g.current_user.user_id)
        db.session.commit()

        flash("Category created.", "success")
        return redirect(url_for("problems.categories"))

    return render_template(
        "problems/categories.html",
        form=form,
        categories=ProblemCategory.query.order_by(
            ProblemCategory.category_name
        ).all(),
    )


@problems_bp.route("/categories/<int:category_id>/edit",
                   methods=["GET", "POST"])
@permission_required("problem.manage")
def edit_category(category_id):
    category = db.get_or_404(ProblemCategory, category_id)
    form = CategoryForm(obj=category, category=category)

    if request.method == "GET":
        form.parent_category_id.data = category.parent_category_id or 0

    if form.validate_on_submit():
        category.category_name = form.category_name.data.strip()
        category.description = form.description.data or None
        category.parent_category_id = form.parent_category_id.data or None
        log_action("category.update", "problem_category",
                   category.category_id, g.current_user.user_id)
        db.session.commit()

        flash("Category updated.", "success")
        return redirect(url_for("problems.categories"))

    return render_template("problems/category_form.html",
                           form=form, category=category)


@problems_bp.post("/categories/<int:category_id>/delete")
@permission_required("problem.manage")
def delete_category(category_id):
    category = db.get_or_404(ProblemCategory, category_id)
    log_action("category.delete", "problem_category",
               category.category_id, g.current_user.user_id)
    db.session.delete(category)
    db.session.commit()

    flash("Category deleted.", "info")
    return redirect(url_for("problems.categories"))


# =====================================================
# TAGS (problem.manage): list + create, edit, delete
# =====================================================

@problems_bp.route("/tags", methods=["GET", "POST"])
@permission_required("problem.manage")
def tags():
    form = TagForm()
    if form.validate_on_submit():
        tag = ProblemTag(tag_name=form.tag_name.data)
        db.session.add(tag)
        db.session.flush()
        log_action("tag.create", "problem_tag", tag.tag_id,
                   g.current_user.user_id)
        db.session.commit()

        flash("Tag created.", "success")
        return redirect(url_for("problems.tags"))

    return render_template(
        "problems/tags.html",
        form=form,
        tags=ProblemTag.query.order_by(ProblemTag.tag_name).all(),
    )


@problems_bp.route("/tags/<int:tag_id>/edit", methods=["GET", "POST"])
@permission_required("problem.manage")
def edit_tag(tag_id):
    tag = db.get_or_404(ProblemTag, tag_id)
    form = TagForm(obj=tag, tag=tag)

    if form.validate_on_submit():
        tag.tag_name = form.tag_name.data
        log_action("tag.update", "problem_tag", tag.tag_id,
                   g.current_user.user_id)
        db.session.commit()

        flash("Tag updated.", "success")
        return redirect(url_for("problems.tags"))

    return render_template("problems/tag_form.html", form=form, tag=tag)


@problems_bp.post("/tags/<int:tag_id>/delete")
@permission_required("problem.manage")
def delete_tag(tag_id):
    tag = db.get_or_404(ProblemTag, tag_id)
    log_action("tag.delete", "problem_tag", tag.tag_id,
               g.current_user.user_id)
    db.session.delete(tag)
    db.session.commit()

    flash("Tag deleted.", "info")
    return redirect(url_for("problems.tags"))