from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.job import Job
from apscheduler.events import EVENT_JOB_ERROR
from django_apscheduler.jobstores import DjangoJobStore, register_events
from django.conf import settings
from .utils import renew_token, upload_data  # assuming these are your task functions
import logging

logger = logging.getLogger(__name__)

def job_listener(event):
    if event.exception:
        job = event.job_id
        logger.error(f"Job {job} failed!")
        print(f"Job {job} failed!")

def start_scheduler():
    scheduler = BackgroundScheduler(executors={'default': ThreadPoolExecutor(10)})  # Adjust thread pool size if needed
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # Task for renewing token every 50 minutes
    scheduler.add_job(renew_token, 'interval', minutes=50, id='renew_token_job', replace_existing=True)

    # Task for uploading data once a day at midnight
    scheduler.add_job(upload_data, 'cron', hour=0, minute=0, id='upload_data_job', replace_existing=True)

    # Register event listeners
    scheduler.add_listener(job_listener, EVENT_JOB_ERROR)

    register_events(scheduler)
    scheduler.start()

    print("Scheduler started...")

    return scheduler
