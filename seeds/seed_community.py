"""
Community demo data for Code Quest: discussions (with replies and
reactions), teams, groups, invitations and notifications.

Run it AFTER seed.py and seed_demo.py:

    python seed_community.py

What every regular user gets
  * Discussions: six public threads, comments, replies and reactions.
  * Group "Code Quest Community" and team "Code Quest Crew": every existing
    user is added as a member (teams and groups are private by design, so
    this is how they become visible to everyone).
  * Pending invitations to the team "Algorithm Warriors" and the group
    "Study Circle", so the Invitations pages have something to accept.
  * A few notifications (some unread, one read).

Safe to re-run: existing rows are skipped. Run it again after new people
register to add them too (or use the optional auto-join snippet).
Group join code for the Community group: WELCOME2026
"""
import random
from datetime import timedelta

from flask import url_for

from app import create_app, db
from app.models import (
    Contest, Discussion, DiscussionComment, DiscussionReaction, GroupInvitation,
    GroupMember, Notification, PrivateGroup, Problem, Team, TeamInvitation,
    TeamMember, User,
)
from app.models.user_models import utc_now
from app.utils.engagement import notify
from app.utils.tokenManagement import hash_token

app = create_app()

JOIN_CODE = "WELCOME2026"
REACTIONS = ["like", "helpful", "insightful"]

# title, author username, problem slug|None, locked, age (hours), body,
# comments: [(username, text, [(username, reply text), ...]), ...]
DISCUSSIONS = [
    ("Welcome to Code Quest! Introduce yourself", "admin", None, False, 300,
     "Hi everyone, and welcome!\n\nTell us a little about yourself: what you "
     "are learning, your favourite language, and what you want to get out of "
     "the platform. New and experienced coders are all welcome here.",
     [("demo_ayesha", "Hi! I mostly write Python and I'm preparing for "
                      "contests. Happy to help with questions.",
       [("demo_hira", "Great to meet you. I'm just starting out with "
                      "arrays, so I'll probably ask a lot!")]),
      ("demo_bilal", "Hello from a C++ fan. The weekly contests here are a "
                     "lot of fun.", []),
      ("demo_ali", "New here. Which problems would you start with?",
       [("demo_sara", "Try the Python Basics learning path first. It goes "
                      "step by step.")])]),

    ("What is the best way to learn dynamic programming?", "demo_hira",
     None, False, 150,
     "I understand recursion, but dynamic programming still confuses me. "
     "How did you learn it? Is there an order of problems that worked?",
     [("demo_ayesha", "Start by writing the plain recursive solution, then "
                      "add memoization. Only after that convert it to a "
                      "table. The DP Foundations learning path follows this "
                      "order.",
       [("demo_hira", "That makes sense, I'll try it with Fibonacci first."),
        ("demo_zainab", "Seconded. Drawing the recursion tree helped me a "
                        "lot.")]),
      ("demo_usman", "Practice little and often. Two problems a day beats "
                     "ten on a weekend.", [])]),

    ("Hash map or brute force: does it matter for small inputs?",
     "demo_sara", "two-sum", False, 96,
     "For Two Sum, the O(n^2) pair check passes the small examples. At what "
     "input size does the hash map approach start to matter in practice?",
     [("demo_bilal", "Around a few thousand elements you will already feel "
                     "it. Contest tests are usually much bigger, so go with "
                     "the hash map.",
       [("demo_sara", "Thanks, that settles it.")]),
      ("demo_hamza", "Also remember the second hint: check whether "
                     "target - x was already seen.", [])]),

    ("Why does Climbing Stairs follow the Fibonacci pattern?",
     "demo_zainab", "climbing-stairs", False, 60,
     "I solved it with a loop but I don't really see why the answer is a "
     "Fibonacci number. Can someone explain the intuition?",
     [("demo_ayesha", "To reach step n you came from step n-1 (one step) or "
                      "step n-2 (two steps). So ways(n) = ways(n-1) + "
                      "ways(n-2), which is exactly the Fibonacci rule.",
       [("demo_zainab", "That clicked, thank you!")])]),

    ("Tips for staying calm in timed contests", "demo_bilal", None, False, 30,
     "Every time a contest clock is running I rush and make silly mistakes. "
     "What routines help you stay calm and avoid wrong attempts, which add "
     "penalty time?",
     [("demo_ayesha", "Read all problems first, solve the easiest one, and "
                      "test on the examples before you submit.", []),
      ("demo_sara", "Take a short break if you get stuck. Coming back with "
                    "fresh eyes saves more time than it costs.", [])]),

    ("Contest rules and the penalty system (please read)", "admin", None,
     True, 400,
     "Scoring: each problem has a points value. Rankings are by total score, "
     "then by lowest penalty.\n\nPenalty: the time from the start of the "
     "contest to each accepted solution, plus 20 minutes for every wrong "
     "attempt made on that problem before it was accepted.\n\nThis thread is "
     "locked. Ask questions in a new discussion.",
     [("demo_usman", "Does a wrong attempt on a problem I never solve add "
                     "penalty?",
       [("admin", "No. Penalty only counts for problems you eventually "
                  "solve.")])]),
]


def user_map():
    return {u.username: u for u in User.query.all()}


# -----------------------------------------------------
# Discussions
# -----------------------------------------------------

def seed_discussions(users, rng):
    now = utc_now()
    problems = {p.slug: p for p in Problem.query.all()}
    created = 0

    for (title, author, slug, locked, age, body, comments) in DISCUSSIONS:
        if Discussion.query.filter_by(title=title).first():
            continue

        problem = problems.get(slug)
        discussion = Discussion(
            user_id=users[author].user_id,
            problem_id=problem.problem_id if problem else None,
            title=title, body=body, is_locked=locked,
            created_at=now - timedelta(hours=age),
        )
        db.session.add(discussion)
        db.session.flush()

        minutes = age * 60
        all_comments = []

        def add_comment(username, text, parent=None):
            nonlocal minutes
            minutes = max(5, minutes - rng.randint(20, 90))
            comment = DiscussionComment(
                discussion_id=discussion.discussion_id,
                user_id=users[username].user_id,
                parent_comment_id=parent.comment_id if parent else None,
                body=text,
                created_at=now - timedelta(minutes=minutes),
            )
            db.session.add(comment)
            db.session.flush()
            all_comments.append(comment)
            return comment

        for username, text, replies in comments:
            top = add_comment(username, text)
            for reply_user, reply_text in replies:
                add_comment(reply_user, reply_text, parent=top)

        # A few reactions from demo users (one per user / comment / type)
        demo_ids = [u.user_id for name, u in users.items()
                    if name.startswith("demo_")]
        for comment in all_comments:
            for uid in rng.sample(demo_ids, k=rng.randint(0, 3)):
                if uid == comment.user_id:
                    continue
                db.session.add(DiscussionReaction(
                    comment_id=comment.comment_id, user_id=uid,
                    reaction_type=rng.choice(REACTIONS),
                ))

        created += 1

    return created


# -----------------------------------------------------
# Teams and groups
# -----------------------------------------------------

def ensure_team(name, owner, description, members):
    team = Team.query.filter_by(team_name=name, owner_id=owner.user_id).first()
    if team is None:
        team = Team(team_name=name, owner_id=owner.user_id,
                    description=description)
        db.session.add(team)
        db.session.flush()
        db.session.add(TeamMember(team_id=team.team_id,
                                  user_id=owner.user_id, team_role="owner"))
    have = {m.user_id for m in TeamMember.query.filter_by(team_id=team.team_id)}
    for user in members:
        if user.user_id not in have:
            db.session.add(TeamMember(team_id=team.team_id,
                                      user_id=user.user_id,
                                      team_role="member"))
            have.add(user.user_id)
    return team


def ensure_group(name, owner, description, members, code=None):
    group = PrivateGroup.query.filter_by(
        group_name=name, owner_id=owner.user_id).first()
    if group is None:
        group = PrivateGroup(
            group_name=name, owner_id=owner.user_id, description=description,
            invite_code_hash=hash_token(code) if code else None,
        )
        db.session.add(group)
        db.session.flush()
        db.session.add(GroupMember(group_id=group.group_id,
                                   user_id=owner.user_id,
                                   member_role="owner"))
    have = {m.user_id for m in GroupMember.query.filter_by(group_id=group.group_id)}
    for user in members:
        if user.user_id not in have:
            db.session.add(GroupMember(group_id=group.group_id,
                                       user_id=user.user_id,
                                       member_role="member"))
            have.add(user.user_id)
    return group


def invite_all(model, fk_name, container, owner, targets):
    """Pending invitations for users who have never been invited
    (so declined invitations are not re-sent)."""
    added = 0
    for user in targets:
        exists = model.query.filter_by(
            **{fk_name: getattr(container, fk_name)},
            invited_user_id=user.user_id).first()
        if exists:
            continue
        db.session.add(model(
            **{fk_name: getattr(container, fk_name)},
            invited_user_id=user.user_id, invited_by=owner.user_id,
            status="pending",
        ))
        added += 1
    return added


def seed_teams_and_groups(users, regular):
    admin = users["admin"]
    demo = [u for n, u in users.items() if n.startswith("demo_")]
    everyone = [admin] + demo + regular

    # Visible to everyone: all users are members
    crew = ensure_team(
        "Code Quest Crew", admin,
        "The official Code Quest team. Everyone is a member: share tips, "
        "ask questions and meet other coders.", everyone)
    community = ensure_group(
        "Code Quest Community", admin,
        "The main community group. New members can join with the invite "
        f"code {JOIN_CODE}.", everyone, code=JOIN_CODE)

    # Demo-only team and group, with pending invitations for regular users
    warriors = ensure_team(
        "Algorithm Warriors", users["demo_ayesha"],
        "A competitive team that trains together for weekly contests.",
        demo[:5])
    study = ensure_group(
        "Study Circle", users["demo_bilal"],
        "A relaxed group for working through learning paths together.",
        demo[1:6])
    db.session.flush()

    invites = invite_all(TeamInvitation, "team_id", warriors,
                         users["demo_ayesha"], regular)
    invites += invite_all(GroupInvitation, "group_id", study,
                          users["demo_bilal"], regular)
    return community, invites


# -----------------------------------------------------
# Notifications
# -----------------------------------------------------

def seed_notifications(regular, community):
    contest = Contest.query.filter_by(title="Algorithm Sprint").first()

    with app.test_request_context():
        contest_url = (url_for("contests.detail", contest_id=contest.contest_id)
                       if contest else url_for("contests.index"))
        items = [
            ("Welcome to Code Quest", "system",
             "Great to have you here. Start with a problem, join a contest "
             "or follow a learning path.",
             url_for("problems.index"), 40, False),
            ("Algorithm Sprint is live", "contest",
             "A short three-problem contest is running right now. Register "
             "and give it a try.",
             contest_url, 25, False),
            ("You were added to the Code Quest Community", "system",
             "You are now a member of the Code Quest Community group.",
             url_for("groups.detail", group_id=community.group_id), 15, False),
            ("New learning path: Python Basics for Beginners", "learning",
             "A new guided path with five beginner problems is available.",
             url_for("learning.index"), 120, True),
        ]

    now = utc_now()
    created = 0
    for user in regular:
        existing = {n.title for n in
                    Notification.query.filter_by(user_id=user.user_id)}
        for title, kind, message, url, minutes_ago, is_read in items:
            if title in existing:
                continue
            n = notify(user.user_id, kind, title, message, url)
            if n is None:                  # user opted out of this type
                continue
            n.created_at = now - timedelta(minutes=minutes_ago)
            if is_read:
                n.read_at = now - timedelta(minutes=minutes_ago - 5)
            created += 1
    return created


# -----------------------------------------------------
# Run
# -----------------------------------------------------

if __name__ == "__main__":
    with app.app_context():
        users = user_map()

        needed = {"admin", "demo_ayesha", "demo_bilal", "demo_sara",
                  "demo_hira", "demo_zainab", "demo_usman", "demo_hamza",
                  "demo_ali"}
        if not needed <= users.keys():
            raise SystemExit(
                "Run `python seed.py` and `python seed_demo.py` first.")

        regular = [u for name, u in users.items()
                   if name != "admin" and not name.startswith("demo_")]

        rng = random.Random(2027)

        discussions = seed_discussions(users, rng)
        community, invites = seed_teams_and_groups(users, regular)
        notifications = seed_notifications(list(users.values()), community)

        db.session.commit()

        print(f"New discussions: {discussions}")
        print(f"Regular users covered: {len(regular)}")
        print(f"New invitations: {invites}")
        print(f"New notifications: {notifications}")
        print(f"Community group join code: {JOIN_CODE}")
        if not regular:
            print("No regular users yet. Register an account, then run this "
                  "script again to add it to the team/group and send "
                  "notifications.")