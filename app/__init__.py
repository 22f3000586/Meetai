import os
from flask import Flask
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    load_dotenv()

    base_dir = os.path.abspath(os.path.dirname(__file__))      # .../meetminder-ai/app
    project_root = os.path.abspath(os.path.join(base_dir, ".."))  # .../meetminder-ai

    app = Flask(
        __name__,
        template_folder=os.path.join(project_root, "templates"),
        static_folder=os.path.join(project_root, "static"),
    )

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(project_root, "instance", "database.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from app.models import Meeting
    with app.app_context():
        db.create_all()

    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app
