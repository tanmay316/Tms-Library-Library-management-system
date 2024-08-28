from celery import shared_task
from flask_mail import Message
from datetime import datetime, timedelta
from .models import User, BookRequest, EBook, Section, Feedback
from flask import render_template
import csv
import os
import logging
from lms.models import db


def get_flask_app():
    from lms import create_app

    app = create_app()
    mail = app.extensions.get("mail")
    return app, mail


@shared_task(ignore_result=False)
def daily_reminder():
    logging.info("Starting daily_reminder task")
    try:
        app, mail = get_flask_app()
        with app.app_context():
            now = datetime.utcnow()
            users = User.query.all()
            logging.info(f"Found {len(users)} users.")
            for user in users:
                book_requests = BookRequest.query.filter(
                    BookRequest.user_id == user.id, BookRequest.is_granted == True
                ).all()
                books_due = [
                    req
                    for req in book_requests
                    if req.date_returned
                    and now <= req.date_returned <= now + timedelta(days=2)
                ]
                logging.info(f"User {user.email} has {len(books_due)} books due soon.")
                if books_due:
                    send_reminder_email(user, books_due, mail)
            logging.info("Daily reminder task completed successfully")
    except Exception as e:
        logging.error(f"Error in daily_reminder task: {e}")


def send_reminder_email(user, books_due, mail):
    msg = Message("Library Reminder", recipients=[user.email])
    msg.body = f"Dear {user.username},\n\nYou have books due for return soon:\n"
    for book in books_due:
        ebook = EBook.query.get(book.ebook_id)
        msg.body += (
            f"- {ebook.title}, due by {book.date_returned.strftime('%Y-%m-%d')}\n"
        )
    logging.info(f"Sending email to {user.email} for {len(books_due)} books due.")
    mail.send(msg)


from sqlalchemy import func


@shared_task(ignore_result=False)
def monthly_report():
    logging.info("Starting monthly_report task")
    try:
        app, mail = get_flask_app()
        with app.app_context():
            now = datetime.utcnow()
            start_time = now - timedelta(
                days=30
            ) 

            sections = Section.query.all()
            ebooks = EBook.query.all()

            feedbacks = (
                db.session.query(
                    Feedback.user_id,
                    Feedback.ebook_id,
                    func.avg(Feedback.rating).label("avg_rating"),
                    User.username,
                    EBook.title,
                )
                .join(User, Feedback.user_id == User.id)
                .join(EBook, Feedback.ebook_id == EBook.id)
                .filter(
                    Feedback.date_created >= start_time,
                    Feedback.date_created <= now,
                )
                .group_by(
                    Feedback.user_id, Feedback.ebook_id, User.username, EBook.title
                )
                .all()
            )

            requests = BookRequest.query.filter(
                BookRequest.date_granted
                >= start_time,  
                BookRequest.date_granted <= now,
                BookRequest.is_granted
                == True,
            ).all()

            html_report = render_template(
                "monthly_report.html",
                sections=sections,
                ebooks=ebooks,
                feedbacks=feedbacks,
                requests=requests,
            )
            msg = Message(
                "Monthly Library Report", recipients=["tanmaysharma917@gmail.com"]
            )
            msg.html = html_report
            mail.send(msg)
            logging.info("Monthly report task completed successfully")
    except Exception as e:
        logging.error(f"Error in monthly_report task: {e}", exc_info=True)


@shared_task(ignore_result=False)
def export_as_csv(librarian_email):
    logging.info("Starting export_as_csv task")
    try:
        app, mail = get_flask_app()
        with app.app_context():
            requests = BookRequest.query.all()
            file_path = os.path.join("uploads", "book_requests.csv")
            if not os.path.exists("uploads"):
                os.makedirs("uploads")

            logging.info(f"File path for export: {file_path}")
            with open(file_path, "w", newline="") as csvfile:
                fieldnames = [
                    "ID",
                    "User",
                    "Book",
                    "Author(s)",
                    "Date Issued",
                    "Return Date",
                    "Content",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for request in requests:
                    ebook = EBook.query.get(request.ebook_id)
                    user = User.query.get(request.user_id)
                    writer.writerow(
                        {
                            "ID": request.id,
                            "User": user.username,
                            "Book": ebook.title,
                            "Author(s)": ebook.authors,
                            "Date Issued": request.date_granted,
                            "Return Date": request.date_returned,
                            "Content": ebook.content,
                        }
                    )
            logging.info("CSV writing completed successfully")

            msg = Message("CSV Export Complete", recipients=[librarian_email])
            msg.body = "The CSV export of book requests has been completed."
            with open(file_path, "r") as fp:
                msg.attach("book_requests.csv", "text/csv", fp.read())
            mail.send(msg)
            logging.info("Export CSV task completed successfully")
    except Exception as e:
        logging.error(f"Error in export_as_csv task: {e}", exc_info=True)
        raise e
