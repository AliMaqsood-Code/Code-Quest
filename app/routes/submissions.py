from flask import (
    Blueprint, abort, flash, g, redirect, render_template, request, url_for,
)

from app import db
from app.forms.submission import STATUSES, ReviewForm, SubmissionForm
from app.models import Contest, Problem, Submission
from app.utils.auth import log_action, login_required, permission_required
from app.utils.contest import can_submit_to_contest, recalc_leaderboard
from app.utils.engagement import award_for_accepted, notify

submissions_bp = Blueprint("submissions", __name__, url_prefix="/submissions")


# =====================================================
# CREATE: save the code as received (status = queued)
# =====================================================

@submissions_bp.route("/submit/<slug>", methods=["GET", "POST"])
@login_required
def submit(slug):
    problem = Problem.query.filter_by(
        slug=slug, status="published"
    ).first_or_404()

    # Contest submissions arrive as /submissions/submit/<slug>?contest=<id>.
    contest = None
    contest_id = request.args.get("contest", type=int)
    if contest_id:
        contest = db.get_or_404(Contest, contest_id)
        if not can_submit_to_contest(contest, problem, g.current_user):
            abort(403)
    elif problem.visibility != "public":
        abort(404)

    form = SubmissionForm()
    if form.validate_on_submit():
        submission = Submission(
            user_id=g.current_user.user_id,
            problem_id=problem.problem_id,
            language_version_id=form.language_version_id.data,
            source_code=form.source_code.data,
            status="queued",
            contest_id=contest.contest_id if contest else None,
        )
        db.session.add(submission)
        db.session.commit()

        flash("Code submitted. It will be reviewed and the result "
              "updated within 24 hours.", "success")
        return redirect(url_for("submissions.detail",
                                submission_id=submission.submission_id))

    return render_template("submissions/submit.html",
                           form=form, problem=problem, contest=contest)


# =====================================================
# READ: my submissions, one submission
# =====================================================

@submissions_bp.get("/")
@login_required
def index():
    query = Submission.query.filter_by(user_id=g.current_user.user_id)

    slug = request.args.get("problem")
    if slug:
        query = query.join(Problem).filter(Problem.slug == slug)

    submissions = (query.order_by(Submission.submitted_at.desc())
                   .limit(200).all())
    return render_template("submissions/list.html",
                           submissions=submissions, problem_slug=slug)


@submissions_bp.get("/<int:submission_id>")
@login_required
def detail(submission_id):
    submission = db.get_or_404(Submission, submission_id)
    user = g.current_user
    can_review = user.has_permission("problem.manage")

    # Owners and reviewers only; anyone else gets a 404, not a hint it exists.
    if submission.user_id != user.user_id and not can_review:
        abort(404)

    return render_template(
        "submissions/detail.html",
        submission=submission,
        review_form=ReviewForm(status=submission.status) if can_review else None,
    )


# =====================================================
# UPDATE (problem.manage): set the result after review
# =====================================================

@submissions_bp.get("/review")
@permission_required("problem.manage")
def review_queue():
    status = request.args.get("status", "queued")

    query = Submission.query
    if status in STATUSES:
        query = query.filter_by(status=status)

    submissions = (query.order_by(Submission.submitted_at.asc())
                   .limit(200).all())
    return render_template("submissions/review.html",
                           submissions=submissions, status=status,
                           statuses=STATUSES)


@submissions_bp.post("/<int:submission_id>/status")
@permission_required("problem.manage")
def update_status(submission_id):
    submission = db.get_or_404(Submission, submission_id)
    form = ReviewForm()

    if form.validate_on_submit():
        previous = submission.status
        submission.status = form.status.data
        if submission.contest_id:
            recalc_leaderboard(submission.contest)

        if submission.status != previous:
            notify(
                submission.user_id, "submission", "Submission reviewed",
                f"Your submission to {submission.problem.title} is now: "
                f"{submission.status.replace('_', ' ')}.",
                url_for("submissions.detail",
                        submission_id=submission.submission_id),
            )
            if submission.status == "accepted":
                award_for_accepted(submission)

        log_action("submission.review", "submission",
                   submission.submission_id, g.current_user.user_id)
        db.session.commit()
        flash("Submission status updated.", "success")

    return redirect(url_for("submissions.detail",
                            submission_id=submission.submission_id))