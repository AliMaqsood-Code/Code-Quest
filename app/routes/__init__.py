def register_blueprints(app):
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.problems import problems_bp
    from app.routes.submissions import submissions_bp
    from app.routes.profile import profile_bp
    from app.routes.discussions import discussions_bp
    from app.routes.contests import contests_bp
    from app.routes.teams import teams_bp
    from app.routes.groups import groups_bp
    from app.routes.learning import learning_bp
    from app.routes.notifications import notifications_bp
    from app.routes.achievements import achievements_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(problems_bp)
    app.register_blueprint(submissions_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(discussions_bp)
    app.register_blueprint(contests_bp)
    app.register_blueprint(teams_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(learning_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(achievements_bp)