from functools import wraps
from flask import Blueprint, request, jsonify,current_app
from lms.models import db, Section, EBook, User, BookRequest, Role
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token
import os
from werkzeug.utils import secure_filename
from flask import send_from_directory
from .tasks import export_as_csv
from flask_caching import Cache
from . import cache
from lms.tasks import export_as_csv
from flask_jwt_extended import jwt_required, get_jwt_identity


librarian_bp = Blueprint("librarian", __name__)


@librarian_bp.route("/librarian/login", methods=["POST"])
def login():
    username = request.json.get("username")
    password = request.json.get("password")

    user = User.query.filter_by(username=username).first()

    if user and user.password == password:
        librarian_role = Role.query.filter_by(role_name="librarian").first()
        if librarian_role and librarian_role in user.roles:
            access_token = create_access_token(identity=user.id)
            return jsonify(
                {
                    "access_token": access_token,
                    "role": "librarian",
                    "message": "Librarian logged in successfully",
                }
            )
        else:
            return jsonify({"error": "Invalid librarian credentials"}), 401
    else:
        return jsonify({"error": "Invalid username or password"}), 400


@librarian_bp.route("/librarian/dashboard", methods=["GET"])
@jwt_required()
@cache.cached(timeout=60, key_prefix="dashboard_stats")
def dashboard():


    total_users = User.query.count()
    total_requests = BookRequest.query.count()
    total_ebooks = EBook.query.count()
    total_sections = Section.query.count()


    sections = Section.query.all()
    sections_data = [
        {"id": section.id, "name": section.name, "description": section.description}
        for section in sections
    ]

    return jsonify(
        {
            "total_users": total_users,
            "total_requests": total_requests,
            "total_ebooks": total_ebooks,
            "total_sections": total_sections,
            "sections": sections_data,
        }
    )


############################Section#########################################


@librarian_bp.route("/sections", methods=["GET"])
@jwt_required()
@cache.cached(timeout=60, key_prefix="all_sections")
def get_sections():
    sections = Section.query.all()
    sections_data = [
        {
            "id": section.id,
            "name": section.name,
            "description": section.description,
            "date_created": section.date_created,
        }
        for section in sections
    ]
    return jsonify(sections_data), 200


@librarian_bp.route("/sections", methods=["POST"])
@jwt_required()
def create_section():
    data = request.json
    name = data.get("name")
    description = data.get("description")

    if not name:
        return jsonify({"error": "Section name is required"}), 400

    new_section = Section(name=name, description=description)
    db.session.add(new_section)
    db.session.commit()

    cache.delete("all_sections")
    cache.delete("dashboard_stats")

    return jsonify({"message": "Section created successfully"}), 201


@librarian_bp.route("/sections/<int:section_id>", methods=["PUT"])
@jwt_required()
def update_section(section_id):
    section = Section.query.get_or_404(section_id)
    data = request.json
    section.name = data.get("name", section.name)
    section.description = data.get("description", section.description)
    section.date_created = data.get("date_created", section.date_created)

    db.session.commit()

    cache.delete("all_sections")
    cache.delete("dashboard_stats")

    return jsonify({"message": "Section updated successfully"}), 200


@librarian_bp.route("/sections/<int:section_id>", methods=["DELETE"])
@jwt_required()
def delete_section(section_id):
    section = Section.query.get_or_404(section_id)
    db.session.delete(section)
    db.session.commit()

    cache.delete("all_sections")
    cache.delete("dashboard_stats")

    return jsonify({"message": "Section deleted successfully"}), 200

@librarian_bp.route("/sections/<int:section_id>/ebooks", methods=["GET"])
@jwt_required()
def get_ebooks(section_id):
    ebooks = EBook.query.filter_by(section_id=section_id).all()
    ebooks_data = [
        {
            "id": ebook.id,
            "title": ebook.title,
            "content": ebook.content,
            "authors": ebook.authors,
            "isbn": ebook.isbn,
        }
        for ebook in ebooks
    ]
    return jsonify(ebooks_data), 200


##################### EBOOK ###########################################

ALLOWED_EXTENSIONS = {"pdf"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@librarian_bp.route("/librarian/upload", methods=["POST"])
@jwt_required()
def upload_ebook():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        data = request.form
        title = data.get("title")
        authors = data.get("authors")
        isbn = data.get("isbn")
        section_id = data.get("section_id")
        description = data.get("description")

        new_ebook = EBook(
            title=title,
            content=filename,  
            authors=authors,
            isbn=isbn,
            section_id=section_id,
            description=description, 
            date_issued=datetime.utcnow(),
        )
        db.session.add(new_ebook)
        db.session.commit()

        return jsonify({"message": "EBook uploaded successfully"}), 201
    else:
        return jsonify({"error": "File type not allowed"}), 400


@librarian_bp.route("/librarian/ebooks/<int:ebook_id>", methods=["PUT"])
@jwt_required()
def update_ebook(ebook_id):
    ebook = EBook.query.get_or_404(ebook_id)
    data = request.json 

    ebook.title = data.get("title", ebook.title)
    ebook.authors = data.get("authors", ebook.authors)
    ebook.description = data.get("description", ebook.description)

    db.session.commit()

    return jsonify({"message": "EBook updated successfully"}), 200


@librarian_bp.route("/librarian/ebooks/<int:ebook_id>", methods=["DELETE"])
@jwt_required()
def delete_ebook(ebook_id):
    ebook = EBook.query.get_or_404(ebook_id)
    db.session.delete(ebook)
    db.session.commit()

    return jsonify({"message": "EBook deleted successfully"}), 200


@librarian_bp.route("/static/uploads/<filename>", methods=["GET"])
@jwt_required()
def get_uploaded_file(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


#####################################Requests#########################################################################33


@librarian_bp.route("/requests", methods=["GET"])
@jwt_required()

def view_requests():
    requests = BookRequest.query.all()
    requests_data = [
        {
            "id": request.id,
            "user_id": request.user_id,
            "ebook_id": request.ebook_id,
            "date_requested": request.date_requested,
            "is_granted": request.is_granted,
            "date_granted": request.date_granted,
            "date_returned": request.date_returned,
        }
        for request in requests
    ]
    return jsonify(requests_data), 200


@librarian_bp.route("/requests/<int:request_id>/grant", methods=["POST"])
@jwt_required()
def grant_request(request_id):
    book_request = BookRequest.query.get_or_404(request_id)
    book_request.is_granted = True
    book_request.date_granted = datetime.utcnow()
    book_request.date_returned = book_request.date_granted + timedelta(
        days=7
    )
    db.session.commit()
    return jsonify({"message": "Request granted"}), 200


@librarian_bp.route("/requests/<int:request_id>/revoke", methods=["POST"])
@jwt_required()
def revoke_request(request_id):
    book_request = BookRequest.query.get_or_404(request_id)
    book_request.is_granted = False
    book_request.date_returned = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": "Request revoked"}), 200


@librarian_bp.route("/requests/<int:request_id>", methods=["DELETE"])
@jwt_required()
def delete_request(request_id):
    book_request = BookRequest.query.get_or_404(request_id)
    db.session.delete(book_request)
    db.session.commit()
    return jsonify({"message": "Request revoked and deleted"}), 200


###################Tasks###############################


def roles_required_debug(role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            roles = [role.role_name for role in user.roles]
            current_app.logger.info(f"User roles: {roles}")
            if role not in roles:
                current_app.logger.warning(
                    f"User does not have the required role: {role}"
                )
                return jsonify({"message": "Forbidden"}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


@librarian_bp.route("/export/csv", methods=["POST"])
@jwt_required()
@roles_required_debug("librarian")
def export_csv():
    try:
        librarian_email = "tanmaysharma917@gmail.com"
        export_as_csv(librarian_email) 
        return jsonify({"message": "CSV export completed"}), 200
    except Exception as e:
        current_app.logger.error(f"Error in exporting CSV: {e}")
        return jsonify({"message": "Error in exporting CSV"}), 500
