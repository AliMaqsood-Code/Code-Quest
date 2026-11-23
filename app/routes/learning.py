from flask import (
    Blueprint, abort, flash, g, redirect, render_template, url_for,
)
from sqlalchemy import func

from app import db
from app.forms.engagement import (
    PROGRESS_STATUSES, LearningPathForm, ProgressForm, StepForm,
)
from app.models import (
    LearningPath, LearningPathStep, UserLearningProgress,
)
from app.models.user_models import utc_now
from app.utils.auth import log_action, login_required, permission_required

learning_bp = Blueprint("learning", __name__, url_prefix="/learning-paths")


def _is_manager():
    user = g.current_user
    return user is not None and user.has_permission("problem.manage")


def _get_path(path_id):
    path = db.get_or_404(LearningPath, path_id)
    if not path.is_published and not _is_manager():
        abort(404)
    return path


def _flash_errors(form):
    for errors in form.errors.values():
        flash(errors[0], "danger")


def _detail(path_id):
    return redirect(url_for("learning.detail", path_id=path_id))


# =====================================================
# LEARNING PATHS: read
# =====================================================

@learning_bp.get("/")
def index():
    query = LearningPath.query
    if not _is_manager():
        query = query.filter_by(is_published=True)
    paths = query.order_by(LearningPath.title).all()

    completed_counts = {}
    if g.current_user is not None:
        rows = db.session.query(
            LearningPathStep.learning_path_id, func.count()
        ).join(
            UserLearningProgress,
            UserLearningProgress.step_id == LearningPathStep.step_id,
        ).filter(
            UserLearningProgress.user_id == g.current_user.user_id,
            UserLearningProgress.status == "completed",
        ).group_by(LearningPathStep.learning_path_id).all()
        completed_counts = dict(rows)

    return render_template(
        "learning/list.html",
        paths=paths,
        step_counts={p.learning_path_id: len(p.steps) for p in paths},
        completed_counts=completed_counts,
        can_manage=_is_manager(),
    )


@learning_bp.get("/<int:path_id>")
def detail(path_id):
    path = _get_path(path_id)
    user = g.current_user
    manager = _is_manager()

    progress = {}
    if user is not None:
        progress = {
            p.step_id: p
            for p in UserLearningProgress.query.join(LearningPathStep).filter(
                LearningPathStep.learning_path_id == path.learning_path_id,
                UserLearningProgress.user_id == user.user_id,
            )
        }

    return render_template(
        "learning/detail.html",
        path=path,
        steps=path.steps,                        # ordered by sequence_no
        progress=progress,                       # {step_id: progress row}
        completed=sum(1 for p in progress.values() if p.status == "completed"),
        total=len(path.steps),
        open_problem_ids={
            s.problem_id for s in path.steps
            if s.problem and s.problem.status == "published"
            and s.problem.visibility == "public"
        },
        progress_statuses=PROGRESS_STATUSES,
        can_manage=manager,
        step_form=StepForm() if manager else None,
    )


# =====================================================
# LEARNING PATHS: create / update / delete (problem.manage)
# =====================================================

@learning_bp.route("/new", methods=["GET", "POST"])
@permission_required("problem.manage")
def create():
    form = LearningPathForm()
    if form.validate_on_submit():
        path = LearningPath(
            created_by=g.current_user.user_id,
            title=form.title.data.strip(),
            description=(form.description.data or "").strip() or None,
            difficulty=form.difficulty.data or None,
            is_published=form.is_published.data,
        )
        db.session.add(path)
        db.session.flush()
        log_action("learning_path.create", "learning_path",
                   path.learning_path_id, g.current_user.user_id)
        db.session.commit()

        flash("Learning path created.", "success")
        return _detail(path.learning_path_id)

    return render_template("learning/form.html", form=form, path=None)


@learning_bp.route("/<int:path_id>/edit", methods=["GET", "POST"])
@permission_required("problem.manage")
def edit(path_id):
    path = db.get_or_404(LearningPath, path_id)
    form = LearningPathForm(obj=path)
    if form.validate_on_submit():
        path.title = form.title.data.strip()
        path.description = (form.description.data or "").strip() or None
        path.difficulty = form.difficulty.data or None
        path.is_published = form.is_published.data
        log_action("learning_path.update", "learning_path",
                   path.learning_path_id, g.current_user.user_id)
        db.session.commit()

        flash("Learning path updated.", "success")
        return _detail(path.learning_path_id)

    return render_template("learning/form.html", form=form, path=path)


@learning_bp.post("/<int:path_id>/delete")
@permission_required("problem.manage")
def delete(path_id):
    path = db.get_or_404(LearningPath, path_id)
    log_action("learning_path.delete", "learning_path",
               path.learning_path_id, g.current_user.user_id)
    db.session.delete(path)          # steps and progress cascade
    db.session.commit()

    flash("Learning path deleted.", "info")
    return redirect(url_for("learning.index"))


# =====================================================
# STEPS: add / update / delete (problem.manage)
# =====================================================

@learning_bp.post("/<int:path_id>/steps")
@permission_required("problem.manage")
def add_step(path_id):
    path = db.get_or_404(LearningPath, path_id)
    form = StepForm()

    if form.validate_on_submit():
        taken = {s.sequence_no for s in path.steps}
        sequence_no = form.sequence_no.data or max(taken, default=0) + 1
        if sequence_no in taken:
            flash("Another step already uses that position.", "danger")
        else:
            db.session.add(LearningPathStep(
                learning_path_id=path_id,
                problem_id=form.problem_id.data or None,
                step_title=form.step_title.data.strip(),
                instructions=(form.instructions.data or "").strip() or None,
                sequence_no=sequence_no,
            ))
            db.session.commit()
            flash("Step added.", "success")
    else:
        _flash_errors(form)

    return _detail(path_id)


@learning_bp.post("/steps/<int:step_id>/update")
@permission_required("problem.manage")
def update_step(step_id):
    step = db.get_or_404(LearningPathStep, step_id)
    form = StepForm()

    if form.validate_on_submit():
        sequence_no = form.sequence_no.data or step.sequence_no
        clash = any(s.sequence_no == sequence_no and s.step_id != step.step_id
                    for s in step.learning_path.steps)
        if clash:
            flash("Another step already uses that position.", "danger")
        else:
            step.step_title = form.step_title.data.strip()
            step.instructions = (form.instructions.data or "").strip() or None
            step.problem_id = form.problem_id.data or None
            step.sequence_no = sequence_no
            db.session.commit()
            flash("Step updated.", "success")
    else:
        _flash_errors(form)

    return _detail(step.learning_path_id)


@learning_bp.post("/steps/<int:step_id>/delete")
@permission_required("problem.manage")
def delete_step(step_id):
    step = db.get_or_404(LearningPathStep, step_id)
    path_id = step.learning_path_id
    db.session.delete(step)          # progress rows cascade
    db.session.commit()

    flash("Step deleted.", "info")
    return _detail(path_id)


# =====================================================
# PROGRESS (any logged-in user)
# =====================================================

@learning_bp.post("/steps/<int:step_id>/progress")
@login_required
def set_progress(step_id):
    step = db.get_or_404(LearningPathStep, step_id)
    _get_path(step.learning_path_id)         # hides unpublished paths
    form = ProgressForm()

    if form.validate_on_submit():
        user_id = g.current_user.user_id
        row = db.session.get(UserLearningProgress, (user_id, step_id))
        if row is None:
            row = UserLearningProgress(user_id=user_id, step_id=step_id)
            db.session.add(row)

        now = utc_now()
        row.status = form.status.data
        if row.status == "not_started":
            row.started_at = row.completed_at = None
        elif row.status == "in_progress":
            row.started_at = row.started_at or now
            row.completed_at = None
        else:
            row.started_at = row.started_at or now
            row.completed_at = now
        db.session.commit()
    else:
        _flash_errors(form)

    return _detail(step.learning_path_id)