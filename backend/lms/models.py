from datetime import datetime
import uuid
from flask_security import UserMixin, RoleMixin
from . import db


roles_users = db.Table(
    "roles_users",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("role_id", db.Integer, db.ForeignKey("role.id")),
)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True)
    confirmed_at = db.Column(db.DateTime, default=datetime.utcnow)
    fs_uniquifier = db.Column(
        db.String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    roles = db.relationship(
        "Role", secondary=roles_users, backref=db.backref("users", lazy="dynamic")
    )
    max_books = db.Column(db.Integer, default=5)
    requests = db.relationship("BookRequest", backref="user", cascade="all, delete")


class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    description = db.Column(db.Text)
    ebooks = db.relationship(
        "EBook", backref="section", cascade="all, delete", lazy=True
    )


class EBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.String(255), nullable=False) 
    authors = db.Column(db.String(255), nullable=False)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    rating = db.Column(db.Float, default=0.0)
    description = db.Column(db.Text)
    date_issued = db.Column(db.DateTime)
    return_date = db.Column(db.DateTime)
    section_id = db.Column(db.Integer, db.ForeignKey("section.id"), nullable=False)
    is_granted = db.Column(db.Boolean, default=False)
    requests = db.relationship(
        "BookRequest", backref="ebook", cascade="all, delete", lazy=True
    )


class BookRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    ebook_id = db.Column(db.Integer, db.ForeignKey("e_book.id"), nullable=False)
    date_requested = db.Column(db.DateTime, default=datetime.utcnow)
    is_granted = db.Column(db.Boolean, default=False)
    date_granted = db.Column(db.DateTime)
    date_returned = db.Column(db.DateTime)


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    ebook_id = db.Column(db.Integer, db.ForeignKey("e_book.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship(
        "User", backref=db.backref("feedbacks", cascade="all, delete")
    )
    ebook = db.relationship(
        "EBook", backref=db.backref("feedbacks", cascade="all, delete")
    )


def initialize_database():
    from flask_security.utils import hash_password

    if not Role.query.filter_by(role_name="librarian").first():
        librarian_role = Role(role_name="librarian", description="Librarian Role")
        db.session.add(librarian_role)
        db.session.commit()

    if not User.query.filter_by(username="librarian").first():
        librarian_user = User(
            username="librarian",
            password="123",
            email="tanmaysharma917@gmail.com",
            active=True,
            confirmed_at=datetime.utcnow(),
        )
        librarian_role = Role.query.filter_by(role_name="librarian").first()
        librarian_user.roles.append(librarian_role)
        db.session.add(librarian_user)
        db.session.commit()
