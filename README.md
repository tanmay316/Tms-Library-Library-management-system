# Tms Library: A Library management system
 
## Overview:
The Library Management System (LMS) is a multi-user web application that allows librarians to 
manage sections and e-books and general users to request, and access e-books. The system 
includes features such as role-based access control, e-book management, section management, 
and asynchronous tasks for daily reminders and monthly reports.

## Technologies Used:
**Flask:** Used for developing the backend REST API, providing endpoints for user authentication, 
section, and e-book management. 
**SQLite:** Employed as the relational database to store user, section, and e-book information. 
**Flask-SQLAlchemy:** Used as the ORM for database operations. 
**Flask-Security:** Integrated for role-based access control, ensuring that only users with specific 
roles (e.g., librarian) can perform certain actions. 
**Flask-JWT:** Implemented for managing authentication and protecting API endpoints. 
**Flask-Caching:** Used for caching API responses to improve performance. 
**Celery with Redis:** Employed for handling asynchronous tasks such as sending daily reminders 
and generating monthly activity reports. 
**Flask-Mail:** Utilized for sending email notifications to users. 
**Flask-Migrate:** Used for managing database migrations.

## Installation

### Backend Setup
1. **Clone the repository:**
2. ```markdown
   git clone https://github.com/tanmay316/Tms-Library-Library-management-system.git
3. **Navigate to the backend directory:**
   ```markdown
   cd backend
4. **Activate the virtual environment:**
   ```markdown
   venv\Scripts\activate
5. **Run the Flask app:**
   ```markdown
   flask run or python app.py

### Frontend Setup
1. Navigate to the frontend directory:
   ```markdown
   cd frontend
2. Install the required packages:
   ```markdown
   npm install
3. Run the Vue.js app:
   ```markdown
   npm run serve

### Accessing the Application
The Flask backend will run by default on http://127.0.0.1:5000/.
The Vue.js frontend will run by default on http://localhost:8080/.

##Contributing:
Contributions are welcome! Please fork this repository and submit a pull request for any improvements.
