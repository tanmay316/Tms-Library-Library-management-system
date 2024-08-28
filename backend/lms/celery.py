from celery import Celery
from celery.schedules import crontab

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config["CELERY_RESULT_BACKEND"],
        broker=app.config["CELERY_BROKER_URL"],
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = Celery(__name__)
celery.config_from_object("lms.celeryconfig")


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    from .tasks import daily_reminder, monthly_report

    sender.add_periodic_task(
        crontab(minute="*/1"), daily_reminder.s(), name="daily reminder"
    )
    sender.add_periodic_task(
        crontab(minute='*/1'), monthly_report.s(), name="monthly report"
    )
