# Tms Library: A Library management system
 
 ![Screenshot 2024-08-28 171908](https://github.com/user-attachments/assets/7615e160-0e8b-4891-93d3-8e13c5753bea)
![Screenshot 2024-08-28 171943](https://github.com/user-attachments/assets/8690b140-b1db-4ff5-81b7-ae1060d01880)
![Screenshot 2024-08-28 172028](https://github.com/user-attachments/assets/973076c5-2725-4513-b9a6-4b4d729eb7f8)
![Screenshot 2024-08-28 172123](https://github.com/user-attachments/assets/8cb823c5-d0d1-4c8a-a93a-4d3710031fb8)

 
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
   ```markdown
   git clone https://github.com/tanmay316/Tms-Library-Library-management-system.git
2. **Navigate to the backend directory:**
   ```markdown
   cd backend
3. **Activate the virtual environment:**
   ```markdown
   venv\Scripts\activate
4. **Run the Flask app:**
   ```markdown
   flask run or python app.py
### Running Redis
1. Start Redis (Ensure you have Redis installed and the redis-server.exe file is available):
   ```markdown
   .\redis-server.exe

### Running Celery for Scheduled Tasks
1. Start the Celery Beat Scheduler:
   ```markdown
   celery -A lms.celery beat --loglevel=info
2. Start the Celery Worker:
   ```markdown
   celery -A lms.celery worker --loglevel=debug --concurrency=1 --pool=solo

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

## Contributing:
Contributions are welcome! Please fork this repository and submit a pull request for any improvements.
