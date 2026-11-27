"""
Demo data for Code Quest: running / upcoming / past contests with real
leaderboards, learning paths, and a set of demo users.

Run it AFTER seed.py:

    python seed.py
    python seed_demo.py

Everything created here is public / published, so it shows up for every
user. Safe to re-run: anything that already exists is skipped.
Demo accounts: demo_ayesha, demo_bilal, ... password: Demo@12345
"""
import random
from datetime import timedelta

from app import create_app, db
from app.models import (
    Contest, ContestAnnouncement, ContestProblem, ContestRegistration,
    LanguageVersion, LearningPath, LearningPathStep, NotificationPreference,
    Problem, ProblemCategory, ProblemExample, ProblemTag, ProblemVersion,
    ProgrammingLanguage, Role, Submission, User, UserProfile,
)
from app.models.user_models import utc_now
from app.utils.contest import as_utc, recalc_leaderboard

app = create_app()

DEMO_PASSWORD = "Demo@12345"

# username, display name, country, skill (0..1, drives how many they solve)
DEMO_USERS = [
    ("demo_ayesha", "Ayesha Khan", "Pakistan", 0.95),
    ("demo_bilal", "Bilal Ahmed", "Pakistan", 0.85),
    ("demo_sara", "Sara Malik", "Pakistan", 0.75),
    ("demo_hamza", "Hamza Raza", "Pakistan", 0.65),
    ("demo_zainab", "Zainab Ali", "Pakistan", 0.55),
    ("demo_usman", "Usman Sheikh", "Pakistan", 0.45),
    ("demo_hira", "Hira Noor", "Pakistan", 0.30),
    ("demo_ali", "Ali Hassan", "Pakistan", 0.15),
]

CATEGORIES = ["Arrays", "Strings", "Math", "Graphs", "Dynamic Programming"]
TAGS = ["beginner", "hashing", "two-pointers"]

# slug, title, difficulty, categories, tags, statement, (input, output, note)
EXTRA_PROBLEMS = [
    ("fizzbuzz", "FizzBuzz", "easy", ["Math"], ["beginner"],
     "Read n. For each i from 1 to n print Fizz if i is divisible by 3, "
     "Buzz if divisible by 5, FizzBuzz if divisible by both, otherwise i. "
     "Print one value per line.\n\nInput: a single integer n.\n"
     "Output: n lines.",
     ("5", "1\n2\nFizz\n4\nBuzz", None)),
    ("palindrome-check", "Palindrome Check", "easy",
     ["Strings"], ["beginner", "two-pointers"],
     "Read a string. Print YES if it reads the same forwards and backwards "
     "(ignore upper/lower case), otherwise print NO.\n\n"
     "Input: one string.\nOutput: YES or NO.",
     ("Racecar", "YES", None)),
    ("count-vowels", "Count Vowels", "easy", ["Strings"], ["beginner"],
     "Read a line of text and print how many vowels (a, e, i, o, u in "
     "either case) it contains.\n\nInput: one line of text.\n"
     "Output: a single integer.",
     ("Hello World", "3", "The vowels are e, o and o.")),
    ("fibonacci-number", "Fibonacci Number", "easy",
     ["Math", "Dynamic Programming"], ["beginner"],
     "Read n (0 <= n <= 45) and print the nth Fibonacci number, where "
     "F(0) = 0 and F(1) = 1.\n\nInput: one integer n.\n"
     "Output: F(n).",
     ("10", "55", None)),
    ("max-subarray-sum", "Maximum Subarray Sum", "medium",
     ["Arrays", "Dynamic Programming"], [],
     "Given n integers, print the largest sum of any contiguous, "
     "non-empty subarray.\n\nInput: first line n, second line n integers.\n"
     "Output: the maximum sum.",
     ("9\n-2 1 -3 4 -1 2 1 -5 4", "6", "The subarray [4, -1, 2, 1] sums to 6.")),
    ("merge-intervals", "Merge Intervals", "medium", ["Arrays"], [],
     "Given n intervals, merge all overlapping ones and print the result "
     "sorted by start, one interval per line.\n\n"
     "Input: first line n, then n lines of 'start end'.\n"
     "Output: the merged intervals as 'start end'.",
     ("4\n1 3\n2 6\n8 10\n15 18", "1 6\n8 10\n15 18",
      "[1,3] and [2,6] overlap, so they merge into [1,6].")),
    ("valid-parentheses", "Valid Parentheses", "medium", ["Strings"], [],
     "Read a string made only of the characters ()[]{}. Print YES if every "
     "bracket is closed by the correct type in the correct order, otherwise "
     "print NO.\n\nInput: one string.\nOutput: YES or NO.",
     ("([]{})", "YES", None)),
    ("climbing-stairs", "Climbing Stairs", "medium",
     ["Dynamic Programming"], [],
     "You are climbing a staircase with n steps and can take 1 or 2 steps "
     "at a time. Print the number of distinct ways to reach the top "
     "(1 <= n <= 45).\n\nInput: one integer n.\nOutput: the number of ways.",
     ("4", "5", "1+1+1+1, 1+1+2, 1+2+1, 2+1+1, 2+2.")),
    ("number-of-islands", "Number of Islands", "medium", ["Graphs"], [],
     "A grid contains '1' (land) and '0' (water). An island is a group of "
     "land cells connected up, down, left or right. Print the number of "
     "islands.\n\nInput: first line r c, then r lines of c characters.\n"
     "Output: the number of islands.",
     ("3 4\n1100\n1001\n0011", "2", None)),
    ("longest-increasing-subsequence", "Longest Increasing Subsequence",
     "hard", ["Dynamic Programming", "Arrays"], [],
     "Given n integers, print the length of the longest strictly "
     "increasing subsequence.\n\nInput: first line n, second line n "
     "integers.\nOutput: the length.",
     ("8\n10 9 2 5 3 7 101 18", "4", "One answer is 2, 3, 7, 101.")),
]

WRONG_STATUSES = ["wrong_answer", "wrong_answer", "runtime_error",
                  "time_limit_exceeded"]
DIFFICULTY_PENALTY = {"easy": 0.0, "medium": 0.2, "hard": 0.4}


def get_or_create(model, defaults=None, **lookup):
    obj = model.query.filter_by(**lookup).first()
    if obj is None:
        obj = model(**lookup, **(defaults or {}))
        db.session.add(obj)
        db.session.flush()
    return obj


# -----------------------------------------------------
# Users
# -----------------------------------------------------

def seed_users(user_role):
    participants = []
    for username, display, country, skill in DEMO_USERS:
        user = User.query.filter_by(username=username).first()
        if user is None:
            user = User(username=username, email=f"{username}@codequest.local")
            user.set_password(DEMO_PASSWORD)
            user.roles = [user_role]
            user.profile = UserProfile(
                display_name=display,
                country=country,
                bio="Demo account for Code Quest.",
            )
            user.notification_preferences = NotificationPreference()
            db.session.add(user)
            db.session.flush()
        participants.append((user, skill))
    return participants


# -----------------------------------------------------
# Problems
# -----------------------------------------------------

def seed_extra_problems(admin):
    cats = {n: get_or_create(ProblemCategory, category_name=n)
            for n in CATEGORIES}
    tags = {n: get_or_create(ProblemTag, tag_name=n) for n in TAGS}

    for (slug, title, difficulty, cat_names, tag_names,
         statement, (inp, out, note)) in EXTRA_PROBLEMS:

        if Problem.query.filter_by(slug=slug).first():
            continue

        problem = Problem(
            author_id=admin.user_id, title=title, slug=slug,
            statement=statement, difficulty=difficulty,
            time_limit_ms=1000, memory_limit_mb=256,
            visibility="public", status="published",
        )
        problem.categories = [cats[n] for n in cat_names]
        problem.tags = [tags[n] for n in tag_names]
        problem.versions = [ProblemVersion(
            version_no=1, statement_snapshot=statement,
            edited_by=admin.user_id,
        )]
        problem.examples = [ProblemExample(
            example_order=1, input_text=inp, output_text=out,
            explanation=note,
        )]
        db.session.add(problem)

    db.session.flush()
    return {p.slug: p for p in Problem.query.all()}


# -----------------------------------------------------
# Contests
# -----------------------------------------------------

def simulate_submissions(contest, user, skill, problems, lang, rng):
    """Create realistic accepted / wrong attempts inside the contest window."""
    start = as_utc(contest.starts_at)
    end = as_utc(contest.ends_at)
    window = (min(utc_now(), end) - start).total_seconds()
    if window <= 0:
        return

    for problem, _points in problems:
        chance = max(0.05, skill - DIFFICULTY_PENALTY[problem.difficulty])
        solved = rng.random() < chance
        wrong = rng.choice([0, 0, 1, 2]) if solved else rng.choice([0, 1, 2])
        attempts = wrong + (1 if solved else 0)
        if attempts == 0:
            continue

        offsets = sorted(rng.uniform(0.02, 1.0) * window
                         for _ in range(attempts))
        for i, offset in enumerate(offsets):
            accepted = solved and i == attempts - 1
            db.session.add(Submission(
                user_id=user.user_id,
                problem_id=problem.problem_id,
                language_version_id=lang.language_version_id,
                source_code=f"# demo submission for {problem.slug}\nprint('demo')",
                status="accepted" if accepted else rng.choice(WRONG_STATUSES),
                submitted_at=start + timedelta(seconds=offset),
                contest_id=contest.contest_id,
            ))


def seed_contests(admin, participants, problems, lang, rng):
    now = utc_now()
    hours = lambda n: timedelta(hours=n)
    days = lambda n: timedelta(days=n)

    # title, description, start, end, [(slug, points)], announcement,
    # how many demo users take part, simulate submissions?
    specs = [
        ("Weekly Warm-up #12",
         "A relaxed four-problem round to start the week. "
         "Easy and medium problems on strings and arrays.",
         now - days(1), now + days(3),
         [("count-vowels", 100), ("palindrome-check", 100),
          ("max-subarray-sum", 200), ("climbing-stairs", 200)],
         "Welcome to the Weekly Warm-up! Good luck and have fun.",
         8, True),

        ("Algorithm Sprint",
         "A short, fast contest. Three problems, eight hours.",
         now - hours(3), now + hours(5),
         [("merge-intervals", 150), ("valid-parentheses", 150),
          ("number-of-islands", 250)],
         "The sprint is live. Remember: wrong attempts add a time penalty.",
         6, True),

        ("Dynamic Programming Cup",
         "Three dynamic programming problems, from warm-up to hard.",
         now + days(2), now + days(2) + hours(3),
         [("fibonacci-number", 100), ("climbing-stairs", 200),
          ("longest-increasing-subsequence", 400)],
         "Registration is open. Problems unlock when the contest starts.",
         5, False),

        ("Beginner Bash",
         "New to competitive coding? Start here with three gentle problems.",
         now + days(6), now + days(6) + hours(2),
         [("fizzbuzz", 100), ("reverse-string", 100), ("two-sum", 150)],
         "Everyone is welcome. Register to take part.",
         3, False),

        ("Autumn Classic",
         "Our autumn round has finished. Check the final standings.",
         now - days(14), now - days(14) + hours(2),
         [("two-sum", 100), ("reverse-string", 100),
          ("fizzbuzz", 100), ("max-subarray-sum", 200)],
         "Thanks for competing! The final leaderboard is published.",
         8, True),

        ("Weekend Challenge #9",
         "A weekend round with trickier medium problems.",
         now - days(7), now - days(7) + hours(3),
         [("valid-parentheses", 150), ("merge-intervals", 150),
          ("number-of-islands", 200)],
         "The contest is over. Well played everyone.",
         7, True),
    ]

    created = 0
    for (title, description, start, end, plist, note,
         count, simulate) in specs:

        if Contest.query.filter_by(title=title).first():
            continue

        contest_problems = [(problems[slug], pts) for slug, pts in plist]

        contest = Contest(
            created_by=admin.user_id, title=title, description=description,
            starts_at=start, ends_at=end,
            visibility="public", status="scheduled",
        )
        contest.contest_problems = [
            ContestProblem(problem_id=p.problem_id, points=pts, sequence_no=i)
            for i, (p, pts) in enumerate(contest_problems, start=1)
        ]
        contest.announcements = [ContestAnnouncement(
            author_id=admin.user_id, message=note,
            published_at=min(utc_now(), start) if start < utc_now()
            else utc_now(),
        )]
        db.session.add(contest)
        db.session.flush()

        for user, skill in participants[:count]:
            db.session.add(ContestRegistration(
                contest_id=contest.contest_id, user_id=user.user_id,
                registered_at=min(utc_now(), start) - hours(rng.randint(1, 48)),
            ))
            if simulate:
                simulate_submissions(contest, user, skill,
                                     contest_problems, lang, rng)

        db.session.flush()
        recalc_leaderboard(contest)
        created += 1

    return created


# -----------------------------------------------------
# Learning paths
# -----------------------------------------------------

def seed_learning_paths(admin, problems):
    # title, difficulty, description, [(step title, instructions, slug|None)]
    paths = [
        ("Python Basics for Beginners", "easy",
         "Your first five problems. Strings, loops and a first look at "
         "dictionaries.",
         [("Warm up with strings",
           "Read the input and print it backwards. Try Python slicing.",
           "reverse-string"),
          ("Counting things",
           "Loop over the characters and count the ones you need.",
           "count-vowels"),
          ("Spot the pattern",
           "Compare the text with its reverse. Mind upper and lower case.",
           "palindrome-check"),
          ("Your first loop challenge",
           "Use a for loop and the modulo operator.",
           "fizzbuzz"),
          ("Lookups with dictionaries",
           "A dictionary lets you find a value in constant time.",
           "two-sum")]),

        ("Dynamic Programming Foundations", "medium",
         "Learn to break a problem into smaller overlapping problems and "
         "remember the answers.",
         [("Start with Fibonacci",
           "Notice how the same values are needed again and again.",
           "fibonacci-number"),
          ("Counting ways",
           "The ways to reach step n come from step n-1 and n-2.",
           "climbing-stairs"),
          ("Best running sum",
           "Decide at each element: extend the current sum or start over.",
           "max-subarray-sum"),
          ("A harder challenge",
           "Keep the best subsequence length ending at each position.",
           "longest-increasing-subsequence")]),

        ("Data Structures Workout", "medium",
         "Practice with stacks, sorting and graph search.",
         [("Read first: when to use a stack",
           "A stack gives last-in, first-out access. It fits problems where "
           "the most recent open item must be closed first. Read about it "
           "before the next step.",
           None),
          ("Matching brackets",
           "Push opening brackets and pop when you see a closing one.",
           "valid-parentheses"),
          ("Sort, then merge",
           "Sorting by start makes overlaps easy to spot.",
           "merge-intervals"),
          ("Flood fill",
           "Visit every land cell once with depth-first or breadth-first "
           "search.",
           "number-of-islands")]),
    ]

    created = 0
    for title, difficulty, description, steps in paths:
        if LearningPath.query.filter_by(title=title).first():
            continue

        path = LearningPath(
            created_by=admin.user_id, title=title, difficulty=difficulty,
            description=description, is_published=True,
        )
        path.steps = [
            LearningPathStep(
                step_title=step_title, instructions=instructions,
                sequence_no=i,
                problem_id=problems[slug].problem_id if slug else None,
            )
            for i, (step_title, instructions, slug) in enumerate(steps, 1)
        ]
        db.session.add(path)
        created += 1

    return created


# -----------------------------------------------------
# Run
# -----------------------------------------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        admin = User.query.filter_by(username="admin").first()
        user_role = Role.query.filter_by(role_name="user").first()
        python = (LanguageVersion.query.join(ProgrammingLanguage)
                  .filter(ProgrammingLanguage.slug == "python").first())

        if not (admin and user_role and python):
            raise SystemExit("Run `python seed.py` first, then this script.")

        rng = random.Random(2026)   # same data every run

        participants = seed_users(user_role)
        problems = seed_extra_problems(admin)

        needed = {"two-sum", "reverse-string"}
        if not needed <= problems.keys():
            raise SystemExit("Missing base problems. Run `python seed.py` first.")

        contests = seed_contests(admin, participants, problems, python, rng)
        paths = seed_learning_paths(admin, problems)

        db.session.commit()

        print(f"Demo users: {len(participants)} (password: {DEMO_PASSWORD})")
        print(f"New contests: {contests}")
        print(f"New learning paths: {paths}")