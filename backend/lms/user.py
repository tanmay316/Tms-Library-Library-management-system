from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token
from lms.models import db, Section, EBook, User, BookRequest, Role, Feedback
from .models import User, Role
from flask_security import current_user
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import cache


user_bp = Blueprint("user", __name__)


@user_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"message": "Username, email, and password are required"}), 400

    if (
        User.query.filter_by(username=username).first()
        or User.query.filter_by(email=email).first()
    ):
        return jsonify({"message": "Username or email already exists"}), 400

    user = User(
        username=username,
        email=email,
        password=password, 
        active=True,
    )

    user_role = Role.query.filter_by(role_name="user").first()
    if not user_role:
        user_role = Role(role_name="user", description="Regular User")
        db.session.add(user_role)

    user.roles.append(user_role)

    db.session.add(user)
    db.session.commit()

    current_app.logger.info(f"User registered successfully: {username}")
    return jsonify({"message": "User registered successfully"}), 201


@user_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    current_app.logger.info(f"Login attempt for user: {username}")

    user = User.query.filter_by(username=username).first()

    if not user or user.password != password:
        current_app.logger.warning(f"Login failed for user: {username}")
        return jsonify({"message": "Invalid username or password"}), 401

    # Create access token
    access_token = create_access_token(identity=user.id)
    role = "user"
    current_app.logger.info(f"User logged in successfully: {username}")
    return jsonify(access_token=access_token, role=role), 200


@user_bp.route("/sections_with_books", methods=["GET"])
@cache.cached(timeout=300, key_prefix="sections_with_books")
def get_sections_with_books():
    sections = Section.query.all()
    sections_data = []
    for section in sections:
        ebooks = EBook.query.filter_by(section_id=section.id).all()
        ebooks_data = [
            {
                "id": ebook.id,
                "title": ebook.title,
                "authors": ebook.authors,
                "isbn": ebook.isbn,
            }
            for ebook in ebooks
        ]
        sections_data.append(
            {
                "id": section.id,
                "name": section.name,
                "ebooks": ebooks_data,
            }
        )
    return jsonify(sections_data)


@user_bp.route("/book/<int:book_id>", methods=["GET"])
def get_book_details(book_id):
    ebook = EBook.query.get_or_404(book_id)
    book_details = {
        "id": ebook.id,
        "title": ebook.title,
        "description": ebook.description,
        "rating": ebook.rating,
    }
    return jsonify(book_details)


@user_bp.route("/issued_books", methods=["GET"])
@jwt_required()
@cache.cached(timeout=10, key_prefix="issued_books_{user_id}")
def get_issued_books():
    user_id = get_jwt_identity()
    issued_books = BookRequest.query.filter_by(user_id=user_id, is_granted=True).all()
    issued_books_data = [
        {
            "id": request.ebook.id,
            "title": request.ebook.title,
            "authors": request.ebook.authors,
            "date_granted": request.date_granted,
        }
        for request in issued_books
    ]
    return jsonify(issued_books_data), 200


@user_bp.route("/book/rate", methods=["POST"])
@jwt_required()
def rate_book():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Invalid request, JSON body required"}), 400

    ebook_id = data.get("ebook_id")
    rating = data.get("rating")

    if ebook_id is None or rating is None:
        return jsonify({"message": "EBook ID and rating are required"}), 400

    try:
        ebook_id = int(ebook_id)
        rating = int(rating)
    except ValueError:
        return jsonify({"message": "Invalid data types for ebook_id or rating"}), 400

    if rating < 0 or rating > 5:
        return jsonify({"message": "Rating must be between 0 and 5"}), 400

    ebook = EBook.query.get_or_404(ebook_id)

    user_id = get_jwt_identity()

    feedback = Feedback(user_id=user_id, ebook_id=ebook.id, rating=rating, comment="")
    db.session.add(feedback)
    db.session.commit()


    feedbacks = Feedback.query.filter_by(ebook_id=ebook.id).all()
    if feedbacks:
        avg_rating = sum([f.rating for f in feedbacks]) / len(feedbacks)
        ebook.rating = avg_rating
        db.session.commit()

    

    return jsonify({"message": "Rating submitted successfully"})


@user_bp.route("/book/request", methods=["POST"])
@jwt_required()
def request_book():
    user_id = get_jwt_identity()
    data = request.get_json()
    ebook_id = data.get("ebook_id")

    if not ebook_id:
        return jsonify({"message": "EBook ID is required"}), 400


    current_requests = BookRequest.query.filter_by(
        user_id=user_id, is_granted=False
    ).count()
    if current_requests >= 5:
        return (
            jsonify(
                {
                    "message": "You have already requested 5 books. Please wait until some are granted."
                }
            ),
            400,
        )

    new_request = BookRequest(user_id=user_id, ebook_id=ebook_id)
    db.session.add(new_request)
    db.session.commit()

    cache.delete(f"issued_books")

    return jsonify({"message": "Book requested successfully"}), 201


@user_bp.route("/book/return/<int:book_id>", methods=["POST"])
@jwt_required()
def return_book(book_id):
    user_id = get_jwt_identity()
    book_request = BookRequest.query.filter_by(
        user_id=user_id, ebook_id=book_id, is_granted=True
    ).first()

    if not book_request:
        return jsonify({"message": "No granted request found for this book"}), 404

    book_request.is_granted = False
    book_request.date_returned = datetime.utcnow()
    db.session.commit()

    cache.delete(f"issued_books")

    return jsonify({"message": "Book returned successfully"}), 200


@user_bp.route("/book/request/limit", methods=["GET"])
@jwt_required()
def check_request_limit():
    user_id = get_jwt_identity()
    current_requests = BookRequest.query.filter_by(
        user_id=user_id, is_granted=False
    ).count()
    can_request_more = current_requests < 5
    return jsonify({"can_request_more": can_request_more}), 200


@user_bp.route("/book/request/status/<int:book_id>", methods=["GET"])
@jwt_required()
def check_request_status(book_id):
    user_id = get_jwt_identity()
    book_request = BookRequest.query.filter_by(
        user_id=user_id, ebook_id=book_id
    ).first()

    if book_request:
        return (
            jsonify({"is_requested": True, "is_granted": book_request.is_granted}),
            200,
        )
    
    cache.delete(f"issued_books")

    return jsonify({"is_requested": False, "is_granted": False}), 200


@user_bp.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "")
    sections = Section.query.filter(Section.name.ilike(f"%{query}%")).all()
    ebooks = EBook.query.filter(
        (EBook.title.ilike(f"%{query}%"))
        | (EBook.authors.ilike(f"%{query}%"))
        | (EBook.isbn.ilike(f"%{query}%"))
    ).all()

    sections_data = [{"id": section.id, "name": section.name} for section in sections]
    ebooks_data = [
        {
            "id": ebook.id,
            "title": ebook.title,
            "authors": ebook.authors,
            "isbn": ebook.isbn,
            
        }
        for ebook in ebooks
    ]

    return jsonify({"sections": sections_data, "ebooks": ebooks_data}), 200
