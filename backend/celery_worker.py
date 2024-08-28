from lms import create_app
from lms.celery import celery
import lms.celeryconfig as celeryconfig

# Create Flask application instance
app = create_app()

# Push the application context to the Celery worker
app.app_context().push()

# Load the Celery configuration from the config file
celery.config_from_object(celeryconfig)
