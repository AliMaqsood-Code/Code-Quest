import os
import sys
from datetime import datetime, timedelta, timezone

DB = "/tmp/smoke_test.db"
if os.path.exists(DB):
    os.remove(DB)
os.environ["DATABASE_URL"] = f"sqlite:///{DB}"
os.environ.setdefault("SECRET_KEY", "smoke-test")

from jinja2 import BaseLoader

from seed import (
    app, seed_access_control, seed_achievements, seed_admin, seed_languages, seed_problems,
)
from app import db
from app.models import (
    ContestLeaderboardEntry, Discussion, DiscussionComment,
    DiscussionReaction, LanguageVersion, Problem, ProblemCategory,
    ProblemTag, ProfileLink, Submission, User,
)


class StubLoader(BaseLoader):
    """Every template renders as a one-line stub; we only test the logic."""
    def get_source(self, environment, template):
        return f"stub:{template}", None, lambda: True


app.jinja_env.loader = StubLoader()
app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

results = []


def call(client, method, url, label, ok, **kw):
    try:
        status = client.open(url, method=method, **kw).status_code
    except Exception as exc:
        results.append(False)
        print(f"FAIL {label} -> {type(exc).__name__}: {exc}")
        return
    good = status in (ok if isinstance(ok, tuple) else (ok,))
    results.append(good)
    print(f"{'PASS' if good else 'FAIL'} {label} -> {status}")


def expect(label, condition):
    results.append(bool(condition))
    print(f"{'PASS' if condition else 'FAIL'} {label}")


with app.app_context():
    db.create_all()
    roles = seed_access_control()
    admin_user = seed_admin(roles)
    seed_languages()
    seed_problems(admin_user)
    seed_achievements()
    db.session.commit()
    lang_id = LanguageVersion.query.first().language_version_id

anon, user, admin = app.test_client(), app.test_client(), app.test_client()
P = lambda **d: {"data": d}

# ---------------- auth ----------------
call(user, "POST", "/auth/register", "register", 302, **P(
    username="tester", email="tester@test.com",
    password="Test12345", confirm_password="Test12345"))
call(user, "POST", "/auth/register", "register duplicate -> form error", 200, **P(
    username="tester", email="tester@test.com",
    password="Test12345", confirm_password="Test12345"))
call(user, "POST", "/auth/login", "login wrong password", 200,
     **P(identifier="tester", password="nope"))
call(user, "POST", "/auth/login", "login", 302,
     **P(identifier="tester", password="Test12345"))
call(user, "GET", "/auth/login", "login page when logged in -> redirect", 302)
call(admin, "POST", "/auth/login", "admin login", 302,
     **P(identifier="admin", password="Admin@12345"))
call(anon, "GET", "/problems/bookmarks", "anon bookmarks -> login redirect", 302)

# ---------------- problems ----------------
call(anon, "GET", "/problems/", "problem list (anon)", 200)
call(user, "GET", "/problems/?difficulty=easy", "problem list filter", 200)
call(user, "GET", "/problems/two-sum", "problem detail", 200)
call(user, "GET", "/problems/nope", "problem detail missing", 404)
call(user, "POST", "/problems/two-sum/bookmark", "bookmark on", 302)
call(user, "GET", "/problems/bookmarks", "bookmark list", 200)
call(user, "POST", "/problems/two-sum/bookmark", "bookmark off", 302)
call(user, "GET", "/problems/manage", "manage as user -> 403", 403)
call(user, "GET", "/problems/new", "create as user -> 403", 403)

call(admin, "GET", "/problems/manage", "manage as admin", 200)
call(admin, "POST", "/problems/new", "create problem", 302, **P(
    title="Smoke Problem", slug="", statement="v1", difficulty="easy",
    time_limit_ms=1000, memory_limit_mb=256, visibility="public",
    status="published", tags="smoke, test"))
call(user, "GET", "/problems/smoke-problem", "new problem visible", 200)
call(admin, "POST", "/problems/smoke-problem/edit", "edit problem", 302, **P(
    title="Smoke Problem", slug="smoke-problem", statement="v2",
    difficulty="medium", time_limit_ms=1000, memory_limit_mb=256,
    visibility="public", status="published", tags="smoke"))
with app.app_context():
    p = Problem.query.filter_by(slug="smoke-problem").one()
    expect("edit created version 2", len(p.versions) == 2)

call(admin, "POST", "/problems/categories", "create category", 302, **P(
    category_name="Smoke Cat", description="", parent_category_id=0))
with app.app_context():
    cat_id = ProblemCategory.query.filter_by(category_name="Smoke Cat").one().category_id
call(admin, "POST", f"/problems/categories/{cat_id}/edit", "edit category", 302,
     **P(category_name="Smoke Cat 2", description="x", parent_category_id=0))
call(admin, "POST", f"/problems/categories/{cat_id}/delete", "delete category", 302)
call(admin, "POST", "/problems/tags", "create tag", 302, **P(tag_name="smoke-tag"))
with app.app_context():
    tag_id = ProblemTag.query.filter_by(tag_name="smoke-tag").one().tag_id
call(admin, "POST", f"/problems/tags/{tag_id}/edit", "edit tag", 302,
     **P(tag_name="smoke-tag-2"))
call(admin, "POST", f"/problems/tags/{tag_id}/delete", "delete tag", 302)
call(admin, "POST", "/problems/smoke-problem/archive", "archive problem", 302)
call(user, "GET", "/problems/smoke-problem", "archived hidden from users", 404)

# ---------------- submissions ----------------
call(user, "GET", "/submissions/submit/two-sum", "submit page", 200)
call(user, "POST", "/submissions/submit/two-sum", "submit code", 302,
     **P(language_version_id=lang_id, source_code="print(1)"))
with app.app_context():
    sub = Submission.query.order_by(Submission.submission_id.desc()).first()
    sub_id = sub.submission_id
    expect("submission saved as queued", sub.status == "queued")
call(user, "GET", "/submissions/", "my submissions", 200)
call(user, "GET", f"/submissions/{sub_id}", "submission detail", 200)
call(anon, "GET", f"/submissions/{sub_id}", "submission detail anon -> redirect", 302)
call(admin, "GET", "/submissions/review", "review queue", 200)
call(user, "POST", f"/submissions/{sub_id}/status", "status as user -> 403", 403,
     **P(status="accepted"))
call(admin, "POST", f"/submissions/{sub_id}/status", "status as admin", 302,
     **P(status="accepted"))

# ---------------- profile ----------------
call(anon, "GET", "/users/tester", "profile view", 200)
call(anon, "GET", "/users/ghost", "profile missing", 404)
call(user, "POST", "/account/profile", "edit profile", 302, **P(
    display_name="Tester", bio="hi", country="PK", avatar_url="",
    github_url="https://github.com/x"))
call(user, "POST", "/account/profile/links", "add link", 302,
     **P(label="Site", url="https://example.com"))
call(user, "POST", "/account/profile/links", "add bad link (rejected)", 302,
     **P(label="Bad", url="javascript:alert(1)"))
with app.app_context():
    links = ProfileLink.query.all()
    expect("only the valid link was saved", len(links) == 1)
    link_id = links[0].link_id
call(user, "POST", f"/account/profile/links/{link_id}/delete", "delete link", 302)
call(user, "POST", "/users/admin/follow", "follow", 302)
call(user, "POST", "/users/tester/follow", "follow self (rejected)", 302)
with app.app_context():
    tester = User.query.filter_by(username="tester").one()
    expect("following exactly 1 user", len(tester.following) == 1)
call(user, "POST", "/users/admin/unfollow", "unfollow", 302)

# ---------------- discussions ----------------
call(user, "POST", "/discussions/new", "create discussion", 302,
     **P(title="Hello", body="First post"))
call(anon, "GET", "/discussions/", "discussion list", 200)
call(anon, "GET", "/discussions/1", "discussion detail", 200)
call(user, "POST", "/discussions/1/comments", "comment", 302, **P(body="c1"))
call(user, "POST", "/discussions/1/comments", "nested reply", 302,
     **P(body="reply", parent_comment_id=1))
call(user, "POST", "/discussions/comments/1/react", "react on", 302,
     **P(reaction_type="like"))
with app.app_context():
    expect("reaction saved", DiscussionReaction.query.count() == 1)
call(user, "POST", "/discussions/comments/1/react", "react off", 302,
     **P(reaction_type="like"))
call(user, "POST", "/discussions/comments/1/edit", "edit comment", 302, **P(body="c1 edited"))
call(user, "POST", "/discussions/1/lock", "lock as user -> 403", 403)
call(admin, "POST", "/discussions/1/lock", "lock as admin", 302)
call(user, "POST", "/discussions/1/comments", "comment on locked (rejected)", 302, **P(body="x"))
with app.app_context():
    expect("locked thread still has 2 comments",
           DiscussionComment.query.count() == 2)
call(admin, "POST", "/discussions/1/lock", "unlock", 302)
call(user, "POST", "/discussions/comments/1/delete", "delete comment (+reply)", 302)
with app.app_context():
    expect("reply deleted with parent", DiscussionComment.query.count() == 0)
call(user, "POST", "/discussions/1/delete", "delete discussion", 302)

# ---------------- contests ----------------
fmt = "%Y-%m-%dT%H:%M"
now = datetime.now(timezone.utc)
call(admin, "POST", "/contests/new", "create contest", 302, **P(
    title="Smoke Contest", description="", visibility="public",
    starts_at=(now - timedelta(days=1)).strftime(fmt),
    ends_at=(now + timedelta(days=1)).strftime(fmt)))
call(admin, "POST", "/contests/new", "contest ends before start -> form error", 200, **P(
    title="Bad", description="", visibility="public",
    starts_at=(now + timedelta(days=1)).strftime(fmt),
    ends_at=(now - timedelta(days=1)).strftime(fmt)))
call(anon, "GET", "/contests/", "contest list", 200)
call(admin, "POST", "/contests/1/problems", "add contest problem", 302,
     **P(problem_id=1, points=100, sequence_no=""))
call(admin, "POST", "/contests/1/announcements", "announcement", 302, **P(message="Welcome"))
call(user, "POST", "/contests/1/register", "register for contest", 302)
call(user, "GET", "/contests/1", "contest detail", 200)
call(user, "POST", "/submissions/submit/two-sum?contest=1", "contest submission", 302,
     **P(language_version_id=lang_id, source_code="print(2)"))
with app.app_context():
    cs = Submission.query.filter_by(contest_id=1).one().submission_id
call(admin, "POST", f"/submissions/{cs}/status", "accept contest submission", 302,
     **P(status="accepted"))
with app.app_context():
    entry = ContestLeaderboardEntry.query.filter_by(contest_id=1).one()
    expect("leaderboard: score 100, rank 1",
           entry.score == 100 and entry.rank_position == 1)
call(anon, "GET", "/contests/1/leaderboard", "leaderboard page", 200)
call(user, "POST", "/contests/1/unregister", "unregister after start (rejected)", 302)
call(admin, "POST", "/contests/1/cancel", "cancel contest", 302)
call(user, "GET", "/contests/1", "cancelled contest hidden", 404)
call(admin, "POST", "/contests/1/cancel", "restore contest", 302)
call(admin, "POST", "/contests/1/leaderboard/refresh", "refresh leaderboard", 302)

# ---------------- teams ----------------
from app.models import Team, TeamMember, PrivateGroup, GroupMember
from app.utils.tokenManagement import generate_token

call(user, "POST", "/teams/new", "create team", 302,
     **P(team_name="Smoke Team", description=""))
call(user, "POST", "/teams/1/invite", "invite admin", 302, **P(username="admin"))
call(user, "POST", "/teams/1/invite", "invite unknown user (rejected)", 302,
     **P(username="ghost"))
call(admin, "GET", "/teams/1", "non-member sees 404", 404)
call(admin, "GET", "/teams/invitations", "my invitations", 200)
call(admin, "POST", "/teams/invitations/1/accept", "accept invitation", 302)
call(admin, "GET", "/teams/1", "member sees team", 200)
call(admin, "POST", "/teams/1/invite", "member invite -> 403", 403, **P(username="tester"))
call(admin, "POST", "/teams/1/leave", "leave team", 302)
call(user, "POST", "/teams/1/invite", "re-invite after leaving", 302, **P(username="admin"))
call(admin, "POST", "/teams/invitations/1/decline", "decline invitation", 302)
call(user, "POST", "/teams/1/edit", "edit team", 302,
     **P(team_name="Smoke Team 2", description="x"))
call(user, "POST", "/teams/1/leave", "owner leave (rejected)", 302)
call(user, "POST", "/teams/1/delete", "delete team", 302)
with app.app_context():
    expect("team and members deleted",
           Team.query.count() == 0 and TeamMember.query.count() == 0)

# ---------------- groups ----------------
call(user, "POST", "/groups/new", "create group", 302,
     **P(group_name="Smoke Group", description=""))
call(user, "POST", "/groups/1/code", "generate invite code", 200)
raw_code, code_hash = generate_token()
with app.app_context():
    db.session.get(PrivateGroup, 1).invite_code_hash = code_hash
    db.session.commit()
call(admin, "POST", "/groups/join", "join with bad code (rejected)", 200, **P(code="wrong"))
call(admin, "POST", "/groups/join", "join with code", 302, **P(code=raw_code))
call(admin, "GET", "/groups/1", "member sees group", 200)
call(user, "POST", "/groups/1/code/revoke", "revoke code", 302)
call(user, "POST", "/groups/1/members/2/remove", "remove owner (rejected)", 302)
with app.app_context():
    expect("owner still in group", db.session.get(GroupMember, (1, 2)) is not None)
call(user, "POST", "/groups/1/members/1/remove", "remove member (admin)", 302)
call(user, "POST", "/groups/1/invite", "invite to group", 302, **P(username="admin"))
call(admin, "POST", "/groups/invitations/1/accept", "accept group invitation", 302)
call(admin, "POST", "/groups/1/leave", "leave group", 302)
call(user, "POST", "/groups/1/edit", "edit group", 302,
     **P(group_name="Smoke Group 2", description=""))
call(user, "POST", "/groups/1/delete", "delete group", 302)
with app.app_context():
    expect("group and members deleted",
           PrivateGroup.query.count() == 0 and GroupMember.query.count() == 0)

# ---------------- learning paths ----------------
from app.models import (
    LearningPath, LearningPathStep, Notification, NotificationPreference,
    PointsTransaction, UserAchievement, UserLearningProgress,
)

call(admin, "POST", "/learning-paths/new", "create learning path", 302, **P(
    title="Smoke Path", description="", difficulty="easy", is_published="y"))
call(user, "POST", "/learning-paths/new", "create path as user -> 403", 403,
     **P(title="x", description="", difficulty=""))
call(admin, "POST", "/learning-paths/1/steps", "add step", 302, **P(
    step_title="Step A", instructions="", problem_id=1, sequence_no=""))
call(admin, "POST", "/learning-paths/1/steps", "add step without problem", 302, **P(
    step_title="Step B", instructions="read", problem_id=0, sequence_no=""))
call(admin, "POST", "/learning-paths/1/steps", "duplicate position (rejected)", 302,
     **P(step_title="Step C", instructions="", problem_id=0, sequence_no=1))
with app.app_context():
    expect("only 2 steps saved", LearningPathStep.query.count() == 2)
call(anon, "GET", "/learning-paths/", "path list", 200)
call(anon, "GET", "/learning-paths/1", "path detail", 200)
call(user, "POST", "/learning-paths/steps/1/progress", "mark step completed", 302,
     **P(status="completed"))
with app.app_context():
    row = UserLearningProgress.query.one()
    expect("completed_at set", row.status == "completed" and row.completed_at)
call(user, "POST", "/learning-paths/steps/1/progress", "reset step", 302,
     **P(status="not_started"))
with app.app_context():
    row = UserLearningProgress.query.one()
    expect("timestamps cleared", row.started_at is None and row.completed_at is None)
call(admin, "POST", "/learning-paths/steps/1/update", "update step", 302, **P(
    step_title="Step A2", instructions="", problem_id=1, sequence_no=1))
call(admin, "POST", "/learning-paths/steps/2/delete", "delete step", 302)
call(admin, "POST", "/learning-paths/1/edit", "edit path", 302, **P(
    title="Smoke Path 2", description="", difficulty="", is_published="y"))
call(admin, "POST", "/learning-paths/1/delete", "delete path", 302)
with app.app_context():
    expect("path, steps and progress deleted",
           LearningPath.query.count() == 0 and LearningPathStep.query.count() == 0
           and UserLearningProgress.query.count() == 0)

# ---------------- notifications and achievements ----------------
with app.app_context():
    tester_id = User.query.filter_by(username="tester").one().user_id
    note_ids = [n.notification_id for n in Notification.query
                .filter_by(user_id=tester_id).order_by(Notification.notification_id)]
    expect("tester received notifications", len(note_ids) >= 3)
    earned = UserAchievement.query.filter_by(user_id=tester_id).count()
    points = sum(t.points_delta for t in
                 PointsTransaction.query.filter_by(user_id=tester_id))
    expect("First Solve earned once", earned == 1)
    expect("points = 10 (solve) + 10 (achievement), no double award", points == 20)

call(user, "GET", "/achievements/", "achievements page", 200)
call(user, "GET", "/notifications/", "notification list", 200)
call(user, "POST", f"/notifications/{note_ids[0]}/read", "mark read", 302)
call(admin, "POST", f"/notifications/{note_ids[0]}/read", "read someone else's -> 404", 404)
call(user, "POST", "/notifications/read-all", "mark all read", 302)
with app.app_context():
    expect("no unread left", Notification.query.filter_by(
        user_id=tester_id, read_at=None).count() == 0)
call(user, "POST", f"/notifications/{note_ids[0]}/delete", "delete notification", 302)
call(user, "GET", "/notifications/preferences", "preferences page", 200)
call(user, "POST", "/notifications/preferences", "save preferences", 302,
     **P(email_enabled="y", contest_alerts="y"))
with app.app_context():
    prefs = db.session.get(NotificationPreference, tester_id)
    expect("submission alerts switched off", prefs.submission_alerts is False)

# ---------------- solutions ----------------
from app.models import PublishedSolution, SolutionVote

SOL = lambda t: P(title=t, language_version_id=lang_id,
                  explanation="how it works", source_code="print(1)")

call(anon, "GET", "/problems/two-sum/solutions", "solution list", 200)
call(admin, "POST", "/problems/reverse-string/solutions/new",
     "manager publishes without solving", 302, **SOL("Official way"))
with app.app_context():
    expect("1 solution", PublishedSolution.query.count() == 1)
call(user, "POST", "/problems/reverse-string/solutions/new",
     "publish without solving (rejected)", 302, **SOL("Cheat"))
with app.app_context():
    expect("still 1 solution", PublishedSolution.query.count() == 1)
call(user, "POST", "/problems/two-sum/solutions/new",
     "publish after solving", 302, **SOL("My way"))
with app.app_context():
    expect("2 solutions", PublishedSolution.query.count() == 2)
call(anon, "GET", "/solutions/1", "solution detail", 200)
call(anon, "GET", "/problems/reverse-string/solutions", "solution list with data", 200)

call(user, "POST", "/solutions/1/vote", "upvote", 302, **P(vote_value=1))
with app.app_context():
    expect("1 vote", SolutionVote.query.count() == 1)
call(user, "POST", "/solutions/1/vote", "same vote again removes it", 302, **P(vote_value=1))
with app.app_context():
    expect("0 votes", SolutionVote.query.count() == 0)
call(user, "POST", "/solutions/1/vote", "downvote", 302, **P(vote_value=-1))
call(user, "POST", "/solutions/1/vote", "switch to upvote", 302, **P(vote_value=1))
with app.app_context():
    v = SolutionVote.query.one()
    expect("one vote, value +1", v.vote_value == 1)
call(user, "POST", "/solutions/2/vote", "vote on own (rejected)", 302, **P(vote_value=1))
call(user, "POST", "/solutions/1/vote", "invalid vote value", 302, **P(vote_value=5))
with app.app_context():
    expect("still just 1 vote", SolutionVote.query.count() == 1)

call(user, "POST", "/solutions/1/official", "official as user -> 403", 403)
call(admin, "POST", "/solutions/1/official", "official as admin", 302)
with app.app_context():
    expect("marked official", db.session.get(PublishedSolution, 1).is_official)

call(admin, "POST", "/solutions/2/edit", "edit someone else's -> 403", 403, **SOL("Hack"))
call(user, "POST", "/solutions/2/edit", "edit own", 302, **SOL("My way v2"))
with app.app_context():
    expect("title updated", db.session.get(PublishedSolution, 2).title == "My way v2")
call(user, "POST", "/solutions/1/delete", "delete someone else's -> 403", 403)
call(admin, "POST", "/solutions/2/delete", "moderator deletes", 302)
call(admin, "POST", "/solutions/1/delete", "author deletes", 302)
with app.app_context():
    expect("solutions and votes gone",
           PublishedSolution.query.count() == 0 and SolutionVote.query.count() == 0)


# ---------------- logout ----------------
call(user, "POST", "/auth/logout", "logout", 302)
call(user, "GET", "/problems/bookmarks", "after logout -> redirect", 302)

passed = sum(results)
print(f"\n{passed}/{len(results)} checks passed")
sys.exit(0 if passed == len(results) else 1)