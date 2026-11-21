from app import create_app, db
from app.models import (
    User, Role, Permission, UserProfile, NotificationPreference,
    ProgrammingLanguage, LanguageVersion,
    Problem, ProblemVersion, ProblemCategory, ProblemTag,
    ProblemExample, TestCase,
)

app = create_app()

PERMISSIONS = {
    "problem.manage": "Create, edit and archive problems",
    "contest.manage": "Create and manage contests",
    "user.manage": "Activate, deactivate and assign roles to users",
    "discussion.moderate": "Lock threads and remove comments",
}

ROLES = {
    "user": ("Regular platform user", []),
    "moderator": ("Moderates discussions", ["discussion.moderate"]),
    "admin": ("Full access", list(PERMISSIONS)),
}

LANGUAGES = {
    # name: (slug, version, runtime image)
    "Python": ("python", "3.12", "python:3.12-slim"),
    "C++": ("cpp", "17", "gcc:13"),
    "Java": ("java", "17", "eclipse-temurin:17"),
    "JavaScript": ("javascript", "20", "node:20-slim"),
}

CATEGORIES = ["Arrays", "Strings", "Math", "Graphs", "Dynamic Programming"]
TAGS = ["beginner", "hashing", "two-pointers"]

ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "admin@codequest.local"
ADMIN_PASSWORD = "Admin@12345"  # dev only, change before any real use


def get_or_create(model, defaults=None, **lookup):
    obj = model.query.filter_by(**lookup).first()
    if obj is None:
        obj = model(**lookup, **(defaults or {}))
        db.session.add(obj)
        db.session.flush()
    return obj


def seed_access_control():
    perms = {
        key: get_or_create(Permission, {"description": desc}, permission_key=key)
        for key, desc in PERMISSIONS.items()
    }
    roles = {}
    for name, (desc, perm_keys) in ROLES.items():
        role = get_or_create(Role, {"description": desc}, role_name=name)
        role.permissions = [perms[k] for k in perm_keys]
        roles[name] = role
    return roles


def seed_admin(roles):
    admin = User.query.filter_by(username=ADMIN_USERNAME).first()
    if admin:
        return admin
    admin = User(username=ADMIN_USERNAME, email=ADMIN_EMAIL)
    admin.set_password(ADMIN_PASSWORD)
    admin.roles = [roles["admin"], roles["user"]]
    admin.profile = UserProfile(display_name="Admin")
    admin.notification_preferences = NotificationPreference()
    db.session.add(admin)
    db.session.flush()
    return admin


def seed_languages():
    for name, (slug, version, image) in LANGUAGES.items():
        lang = get_or_create(
            ProgrammingLanguage, {"slug": slug}, language_name=name
        )
        get_or_create(
            LanguageVersion,
            {"runtime_image": image, "is_default": True},
            language_id=lang.language_id,
            version_label=version,
        )


def seed_problem(admin, cats, tags, slug, title, statement, difficulty,
                 category_names, tag_names, examples, tests):
    if Problem.query.filter_by(slug=slug).first():
        return
    problem = Problem(
        author_id=admin.user_id,
        title=title,
        slug=slug,
        statement=statement,
        difficulty=difficulty,
        time_limit_ms=1000,
        memory_limit_mb=256,
        visibility="public",
        status="published",
    )
    problem.categories = [cats[n] for n in category_names]
    problem.tags = [tags[n] for n in tag_names]
    problem.versions = [
        ProblemVersion(
            version_no=1,
            statement_snapshot=statement,
            edited_by=admin.user_id,
        )
    ]
    problem.examples = [
        ProblemExample(
            example_order=i,
            input_text=inp,
            output_text=out,
            explanation=expl,
        )
        for i, (inp, out, expl) in enumerate(examples, start=1)
    ]
    problem.test_cases = [
        TestCase(
            case_name=f"case {i}",
            input_data=inp,
            expected_output=out,
            is_sample=is_sample,
            is_hidden=not is_sample,
        )
        for i, (inp, out, is_sample) in enumerate(tests, start=1)
    ]
    db.session.add(problem)


def seed_problems(admin):
    cats = {
        n: get_or_create(ProblemCategory, category_name=n) for n in CATEGORIES
    }
    tags = {n: get_or_create(ProblemTag, tag_name=n) for n in TAGS}

    seed_problem(
        admin, cats, tags,
        slug="two-sum",
        title="Two Sum",
        statement=(
            "Given n integers and a target, print the 0-based indices of the "
            "two numbers that add up to the target.\n\n"
            "Input: first line n and target, second line n integers.\n"
            "Output: the two indices separated by a space."
        ),
        difficulty="easy",
        category_names=["Arrays"],
        tag_names=["beginner", "hashing"],
        examples=[("4 9\n2 7 11 15", "0 1", "2 + 7 = 9")],
        tests=[
            ("4 9\n2 7 11 15", "0 1", True),
            ("3 6\n3 2 4", "1 2", False),
            ("2 6\n3 3", "0 1", False),
        ],
    )

    seed_problem(
        admin, cats, tags,
        slug="reverse-string",
        title="Reverse a String",
        statement="Read a string and print it reversed.",
        difficulty="easy",
        category_names=["Strings"],
        tag_names=["beginner", "two-pointers"],
        examples=[("hello", "olleh", None)],
        tests=[
            ("hello", "olleh", True),
            ("a", "a", False),
            ("racecar", "racecar", False),
        ],
    )


if __name__ == "__main__":
    with app.app_context():
        roles = seed_access_control()
        admin = seed_admin(roles)
        seed_languages()
        seed_problems(admin)
        db.session.commit()
        print("Seed complete.")