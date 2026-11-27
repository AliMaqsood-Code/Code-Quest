from collections import defaultdict

from flask import (
    Blueprint, abort, flash, g, redirect, render_template, request, url_for,
)
from sqlalchemy import func, or_

from app import db
from app.forms.discussion import (
    REACTIONS, CommentForm, DiscussionForm, ReactionForm,
)
from app.models import (
    Discussion, DiscussionComment, DiscussionReaction, Problem,
)
from app.utils.auth import log_action, login_required, permission_required
from app.utils.engagement import notify

discussions_bp = Blueprint("discussions", __name__, url_prefix="/discussions")


def _is_mod():
    user = g.current_user
    return user is not None and user.has_permission("discussion.moderate")


def _problem_open(problem):
    return problem.status == "published" and problem.visibility == "public"


def _get_discussion(discussion_id):
    """Threads on unpublished or private problems are hidden from everyone
    except moderators."""
    discussion = db.get_or_404(Discussion, discussion_id)
    if (discussion.problem is not None
            and not _problem_open(discussion.problem)
            and not _is_mod()):
        abort(404)
    return discussion


def _flash_errors(form):
    for errors in form.errors.values():
        flash(errors[0], "danger")


# =====================================================
# DISCUSSIONS: read
# =====================================================

@discussions_bp.get("/")
def index():
    query = Discussion.query.outerjoin(Problem)

    problem = None
    slug = request.args.get("problem")
    if slug:
        problem = Problem.query.filter_by(slug=slug).first_or_404()
        if not _problem_open(problem):
            abort(404)
        query = query.filter(Discussion.problem_id == problem.problem_id)
    else:
        query = query.filter(or_(
            Discussion.problem_id.is_(None),
            (Problem.status == "published") & (Problem.visibility == "public"),
        ))

    discussions = (query.order_by(Discussion.created_at.desc())
                   .limit(100).all())
    comment_counts = dict(
        db.session.query(
            DiscussionComment.discussion_id,
            func.count(DiscussionComment.comment_id),
        ).group_by(DiscussionComment.discussion_id).all()
    )

    return render_template(
        "discussions/list.html",
        discussions=discussions,
        problem=problem,
        comment_counts=comment_counts,
    )


@discussions_bp.get("/<int:discussion_id>")
def detail(discussion_id):
    discussion = _get_discussion(discussion_id)
    user = g.current_user

    top_level = sorted(
        (c for c in discussion.comments if c.parent_comment_id is None),
        key=lambda c: c.created_at,
    )

    # reaction_counts[comment_id][reaction_type] -> number of reactions
    reaction_counts = defaultdict(dict)
    rows = (
        db.session.query(
            DiscussionReaction.comment_id,
            DiscussionReaction.reaction_type,
            func.count(),
        )
        .join(DiscussionComment)
        .filter(DiscussionComment.discussion_id == discussion.discussion_id)
        .group_by(DiscussionReaction.comment_id,
                  DiscussionReaction.reaction_type)
        .all()
    )
    for comment_id, reaction_type, count in rows:
        reaction_counts[comment_id][reaction_type] = count

    # my_reactions: set of (comment_id, reaction_type) the viewer has given
    my_reactions = set()
    if user is not None:
        my_reactions = {
            (r.comment_id, r.reaction_type)
            for r in DiscussionReaction.query.join(DiscussionComment).filter(
                DiscussionComment.discussion_id == discussion.discussion_id,
                DiscussionReaction.user_id == user.user_id,
            )
        }

    return render_template(
        "discussions/detail.html",
        discussion=discussion,
        comments=top_level,
        comment_form=CommentForm(),
        reaction_counts=reaction_counts,
        my_reactions=my_reactions,
        reactions=REACTIONS,
        can_moderate=_is_mod(),
        can_comment=user is not None and not discussion.is_locked,
    )


# =====================================================
# DISCUSSIONS: create / update / delete
# =====================================================

@discussions_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    problem = None
    slug = request.args.get("problem")
    if slug:
        problem = Problem.query.filter_by(
            slug=slug, status="published", visibility="public"
        ).first_or_404()

    form = DiscussionForm()
    if form.validate_on_submit():
        discussion = Discussion(
            user_id=g.current_user.user_id,
            problem_id=problem.problem_id if problem else None,
            title=form.title.data.strip(),
            body=form.body.data,
        )
        db.session.add(discussion)
        db.session.commit()

        flash("Discussion created.", "success")
        return redirect(url_for("discussions.detail",
                                discussion_id=discussion.discussion_id))

    return render_template("discussions/form.html",
                           form=form, discussion=None, problem=problem)


@discussions_bp.route("/<int:discussion_id>/edit", methods=["GET", "POST"])
@login_required
def edit(discussion_id):
    discussion = _get_discussion(discussion_id)
    if discussion.user_id != g.current_user.user_id:
        abort(403)

    form = DiscussionForm(obj=discussion)
    if form.validate_on_submit():
        discussion.title = form.title.data.strip()
        discussion.body = form.body.data
        db.session.commit()

        flash("Discussion updated.", "success")
        return redirect(url_for("discussions.detail",
                                discussion_id=discussion.discussion_id))

    return render_template("discussions/form.html", form=form,
                           discussion=discussion, problem=discussion.problem)


@discussions_bp.post("/<int:discussion_id>/delete")
@login_required
def delete(discussion_id):
    discussion = _get_discussion(discussion_id)
    user = g.current_user
    is_owner = discussion.user_id == user.user_id

    if not is_owner and not _is_mod():
        abort(403)
    if not is_owner:
        log_action("discussion.delete", "discussion",
                   discussion.discussion_id, user.user_id)

    problem = discussion.problem
    db.session.delete(discussion)
    db.session.commit()

    flash("Discussion deleted.", "info")
    if problem is not None:
        return redirect(url_for("discussions.index", problem=problem.slug))
    return redirect(url_for("discussions.index"))


@discussions_bp.post("/<int:discussion_id>/lock")
@permission_required("discussion.moderate")
def toggle_lock(discussion_id):
    discussion = _get_discussion(discussion_id)
    discussion.is_locked = not discussion.is_locked

    action = "discussion.lock" if discussion.is_locked else "discussion.unlock"
    log_action(action, "discussion", discussion.discussion_id,
               g.current_user.user_id)
    db.session.commit()

    flash("Discussion locked." if discussion.is_locked
          else "Discussion unlocked.", "info")
    return redirect(url_for("discussions.detail",
                            discussion_id=discussion.discussion_id))


# =====================================================
# COMMENTS: create / update / delete
# =====================================================

@discussions_bp.post("/<int:discussion_id>/comments")
@login_required
def add_comment(discussion_id):
    discussion = _get_discussion(discussion_id)
    detail_url = url_for("discussions.detail", discussion_id=discussion_id)

    if discussion.is_locked:
        flash("This discussion is locked.", "danger")
        return redirect(detail_url)

    form = CommentForm()
    if form.validate_on_submit():
        parent_id = form.parent_comment_id.data or None
        recipients = {discussion.user_id}
        if parent_id is not None:
            parent = db.session.get(DiscussionComment, parent_id)
            if parent is None or parent.discussion_id != discussion_id:
                abort(400)
            recipients.add(parent.user_id)

        db.session.add(DiscussionComment(
            discussion_id=discussion_id,
            user_id=g.current_user.user_id,
            parent_comment_id=parent_id,
            body=form.body.data,
        ))

        recipients.discard(g.current_user.user_id)
        for uid in recipients:
            notify(uid, "discussion", f"New reply in: {discussion.title}",
                   f"{g.current_user.username} commented in a discussion "
                   "you're part of.", detail_url)
        db.session.commit()
        flash("Comment posted.", "success")
    else:
        _flash_errors(form)

    return redirect(detail_url)


@discussions_bp.route("/comments/<int:comment_id>/edit",
                      methods=["GET", "POST"])
@login_required
def edit_comment(comment_id):
    comment = db.get_or_404(DiscussionComment, comment_id)
    discussion = _get_discussion(comment.discussion_id)
    detail_url = url_for("discussions.detail",
                         discussion_id=discussion.discussion_id)

    if comment.user_id != g.current_user.user_id:
        abort(403)
    if discussion.is_locked:
        flash("This discussion is locked.", "danger")
        return redirect(detail_url)

    form = CommentForm(obj=comment)
    if form.validate_on_submit():
        comment.body = form.body.data
        comment.is_edited = True
        db.session.commit()

        flash("Comment updated.", "success")
        return redirect(detail_url)

    return render_template("discussions/comment_form.html", form=form,
                           comment=comment, discussion=discussion)


@discussions_bp.post("/comments/<int:comment_id>/delete")
@login_required
def delete_comment(comment_id):
    comment = db.get_or_404(DiscussionComment, comment_id)
    discussion = _get_discussion(comment.discussion_id)
    user = g.current_user
    is_owner = comment.user_id == user.user_id

    if not is_owner and not _is_mod():
        abort(403)
    if not is_owner:
        log_action("comment.delete", "discussion_comment",
                   comment.comment_id, user.user_id)

    # Replies and reactions go with it (cascade).
    db.session.delete(comment)
    db.session.commit()

    flash("Comment deleted.", "info")
    return redirect(url_for("discussions.detail",
                            discussion_id=discussion.discussion_id))


# =====================================================
# REACTIONS: toggle one reaction type on a comment
# =====================================================

@discussions_bp.post("/comments/<int:comment_id>/react")
@login_required
def react(comment_id):
    comment = db.get_or_404(DiscussionComment, comment_id)
    discussion = _get_discussion(comment.discussion_id)
    detail_url = url_for("discussions.detail",
                         discussion_id=discussion.discussion_id)

    form = ReactionForm()
    if not form.validate_on_submit():
        flash("Invalid reaction.", "danger")
        return redirect(detail_url)

    existing = DiscussionReaction.query.filter_by(
        comment_id=comment.comment_id,
        user_id=g.current_user.user_id,
        reaction_type=form.reaction_type.data,
    ).first()

    if existing:
        db.session.delete(existing)
    else:
        db.session.add(DiscussionReaction(
            comment_id=comment.comment_id,
            user_id=g.current_user.user_id,
            reaction_type=form.reaction_type.data,
        ))
    db.session.commit()

    return redirect(detail_url)