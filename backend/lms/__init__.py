from flask import Flask, current_app, request
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask import Flask, send_from_directory
import os
from flask_apscheduler import APScheduler
from flask_mail import Mail
import logging
from flask_caching import Cache
from .celery import make_celery

cache = Cache()
db = SQLAlchemy()
mail = Mail()


def create_app():

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///library.db"
    app.config["SECRET_KEY"] = "super-secret"
    app.config["SECURITY_PASSWORD_SALT"] = "super-secret-salt"
    app.config["SECURITY_REGISTERABLE"] = False
    app.config["SECURITY_PASSWORD_HASH"] = "pbkdf2_sha512"
    app.config["JWT_SECRET_KEY"] = "jwt-secret-string"
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SECURITY_USER_IDENTITY_ATTRIBUTES"] = "username"

    app.config["CELERY_BROKER_URL"] = "redis://localhost:6379/1"
    app.config["CELERY_RESULT_BACKEND"] = "redis://localhost:6379/2"

    # Disable Flask-Security's built-in views
    app.config["SECURITY_LOGIN_URL"] = "/login"
    app.config["SECURITY_LOGOUT_URL"] = "/logout"
    app.config["SECURITY_REGISTER_URL"] = "/register"
    app.config["SECURITY_RESET_URL"] = "/reset"
    app.config["SECURITY_CHANGE_URL"] = "/change"
    app.config["SECURITY_CONFIRM_URL"] = "/confirm"

    # Disable Flask-Security features Im not using
    app.config["SECURITY_REGISTERABLE"] = False
    app.config["SECURITY_RECOVERABLE"] = False
    app.config["SECURITY_CHANGEABLE"] = False
    app.config["SECURITY_CONFIRMABLE"] = False

    # Update for Flask-Security 4.0
    app.config["SECURITY_USER_IDENTITY_ATTRIBUTES"] = [
        {"username": {"mapper": "username"}}
    ]

    # Redis configuration
    app.config["CACHE_TYPE"] = "RedisCache"
    app.config["CACHE_REDIS_HOST"] = "localhost"
    app.config["CACHE_REDIS_PORT"] = 6379
    app.config["CACHE_REDIS_DB"] = 0
    app.config["CACHE_REDIS_URL"] = "redis://localhost:6379/0"
    app.config["CACHE_DEFAULT_TIMEOUT"] = 300 

    # Enable logging for cache
    logging.basicConfig(level=logging.DEBUG)
    cache_logger = logging.getLogger("flask_caching")
    cache_logger.setLevel(logging.DEBUG)

    import time


    @app.before_request
    def start_timer():
        request.start_time = time.time()


    @app.after_request
    def log_request(response):
        if hasattr(request, "start_time"):
            duration = time.time() - request.start_time
            current_app.logger.info(f"Request to {request.path} took {duration:.4f}s")
        return response

    cache.init_app(app)

    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USE_SSL"] = False
    app.config["MAIL_USERNAME"] = "tanmaysharma917@gmail.com"
    app.config["MAIL_PASSWORD"] = "twmh meeh pilz tmuc"
    app.config["MAIL_DEFAULT_SENDER"] = "tanmaysharma917@gmail.com"

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("apscheduler")
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    app.config["UPLOAD_FOLDER"] = "uploads"
    if not os.path.exists(app.config["UPLOAD_FOLDER"]):
        os.makedirs(app.config["UPLOAD_FOLDER"])

    # Serve uploaded files
    @app.route("/uploads/<filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    CORS(app)
    db.init_app(app)
    migrate = Migrate(app, db)
    jwt = JWTManager(app)
    mail.init_app(app)


    celery=make_celery(app)

    from .models import User, Role, initialize_database

    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore, register_blueprint=False)

    with app.app_context():
        from . import models
        db.create_all()
        initialize_database()

        from lms.librarian import librarian_bp
        from lms.user import user_bp

        app.register_blueprint(librarian_bp)
        app.register_blueprint(user_bp)

    return app
