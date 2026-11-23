from flask import (
    Blueprint, abort, flash, g, redirect, render_template, url_for,
)
from sqlalchemy import func

from app import db
from app.forms.solution import SolutionForm, VoteForm
from app.models import Problem, PublishedSolution, SolutionVote, Submission
from app.utils.auth import log_action, login_required, permission_required

solutions_bp = Blueprint("solutions", __name__)


def _is_manager():
    user = g.current_user
    return user is not None and user.has_permission("problem.manage")


def _problem_open(problem):
    return problem.status == "published" and problem.visibility == "public"


def _get_problem(slug):
    problem = Problem.query.filter_by(slug=slug).first_or_404()
    if not _problem_open(problem) and not _is_manager():
        abort(404)
    return problem


def _get_solution(solution_id):
    solution = db.get_or_404(PublishedSolution, solution_id)
    if not _problem_open(solution.problem) and not _is_manager():
        abort(404)
    return solution


def _has_solved(user, problem):
    return db.session.query(Submission.submission_id).filter_by(
        user_id=user.user_id, problem_id=problem.problem_id,
        status="accepted",
    ).first() is not None


def _can_post(user, problem):
    """Only people who solved the problem (or managers) may publish a
    solution, so solutions don't leak before an honest attempt."""
    return user is not None and (_is_manager() or _has_solved(user, problem))


# =====================================================
# SOLUTIONS: read
# =====================================================

@solutions_bp.get("/problems/<slug>/solutions")
def index(slug):
    problem = _get_problem(slug)

    score = func.coalesce(func.sum(SolutionVote.vote_value), 0)
    rows = (
        db.session.query(PublishedSolution, score)
        .outerjoin(SolutionVote)
        .filter(PublishedSolution.problem_id == problem.problem_id)
        .group_by(PublishedSolution.solution_id)
        .order_by(PublishedSolution.is_official.desc(), score.desc(),
                  PublishedSolution.published_at.desc())
        .all()
    )

    return render_template(
        "solutions/list.html",
        problem=problem,
        solutions=[s for s, _ in rows],
        scores={s.solution_id: int(total) for s, total in rows},
        can_post=_can_post(g.current_user, problem),
    )


@solutions_bp.get("/solutions/<int:solution_id>")
def detail(solution_id):
    solution = _get_solution(solution_id)
    user = g.current_user

    upvotes = sum(1 for v in solution.votes if v.vote_value == 1)
    my_vote = 0
    if user is not None:
        my_vote = next((v.vote_value for v in solution.votes
                        if v.user_id == user.user_id), 0)

    return render_template(
        "solutions/detail.html",
        solution=solution,
        problem=solution.problem,
        upvotes=upvotes,
        downvotes=len(solution.votes) - upvotes,
        score=upvotes - (len(solution.votes) - upvotes),
        my_vote=my_vote,                         # 1, -1 or 0
        is_author=user is not None and solution.author_id == user.user_id,
        can_moderate=_is_manager(),
    )


# =====================================================
# SOLUTIONS: create / update / delete
# =====================================================

@solutions_bp.route("/problems/<slug>/solutions/new", methods=["GET", "POST"])
@login_required
def create(slug):
    problem = _get_problem(slug)

    if not _can_post(g.current_user, problem):
        flash("Solve this problem first to publish a solution.", "danger")
        return redirect(url_for("problems.detail", slug=slug))

    form = SolutionForm()
    if form.validate_on_submit():
        solution = PublishedSolution(
            problem_id=problem.problem_id,
            author_id=g.current_user.user_id,
            language_version_id=form.language_version_id.data,
            title=form.title.data.strip(),
            explanation=form.explanation.data,
            source_code=form.source_code.data,
        )
        db.session.add(solution)
        db.session.commit()

        flash("Solution published.", "success")
        return redirect(url_for("solutions.detail",
                                solution_id=solution.solution_id))

    return render_template("solutions/form.html", form=form,
                           problem=problem, solution=None)


@solutions_bp.route("/solutions/<int:solution_id>/edit",
                    methods=["GET", "POST"])
@login_required
def edit(solution_id):
    solution = _get_solution(solution_id)
    if solution.author_id != g.current_user.user_id:
        abort(403)

    form = SolutionForm(obj=solution)
    if form.validate_on_submit():
        solution.title = form.title.data.strip()
        solution.language_version_id = form.language_version_id.data
        solution.explanation = form.explanation.data
        solution.source_code = form.source_code.data
        db.session.commit()

        flash("Solution updated.", "success")
        return redirect(url_for("solutions.detail",
                                solution_id=solution.solution_id))

    return render_template("solutions/form.html", form=form,
                           problem=solution.problem, solution=solution)


@solutions_bp.post("/solutions/<int:solution_id>/delete")
@login_required
def delete(solution_id):
    solution = _get_solution(solution_id)
    user = g.current_user
    is_author = solution.author_id == user.user_id

    if not is_author and not _is_manager():
        abort(403)
    if not is_author:
        log_action("solution.delete", "published_solution",
                   solution.solution_id, user.user_id)

    slug = solution.problem.slug
    db.session.delete(solution)          # votes cascade
    db.session.commit()

    flash("Solution deleted.", "info")
    return redirect(url_for("solutions.index", slug=slug))


@solutions_bp.post("/solutions/<int:solution_id>/official")
@permission_required("problem.manage")
def toggle_official(solution_id):
    solution = _get_solution(solution_id)
    solution.is_official = not solution.is_official

    log_action("solution.official" if solution.is_official
               else "solution.unofficial",
               "published_solution", solution.solution_id,
               g.current_user.user_id)
    db.session.commit()

    flash("Marked as official." if solution.is_official
          else "Official mark removed.", "info")
    return redirect(url_for("solutions.detail",
                            solution_id=solution.solution_id))


# =====================================================
# VOTES: up / down, same vote again removes it
# =====================================================

@solutions_bp.post("/solutions/<int:solution_id>/vote")
@login_required
def vote(solution_id):
    solution = _get_solution(solution_id)
    user = g.current_user
    back = redirect(url_for("solutions.detail",
                            solution_id=solution.solution_id))

    form = VoteForm()
    if not form.validate_on_submit():
        flash("Invalid vote.", "danger")
        return back
    if solution.author_id == user.user_id:
        flash("You can't vote on your own solution.", "danger")
        return back

    value = form.vote_value.data
    existing = db.session.get(SolutionVote, (solution.solution_id,
                                             user.user_id))
    if existing is None:
        db.session.add(SolutionVote(solution_id=solution.solution_id,
                                    user_id=user.user_id, vote_value=value))
    elif existing.vote_value == value:
        db.session.delete(existing)
    else:
        existing.vote_value = value

    db.session.commit()
    return back