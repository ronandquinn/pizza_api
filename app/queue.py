"""Background job queue helper.

Rails equivalent: ActiveJob/Sidekiq. Here we use RQ ("Redis Queue"):
enqueue a plain function by reference and a separate worker process runs it.
(Celery is the heavier, more common alternative; RQ keeps the sample small.)
"""
from flask import current_app
from rq import Queue


def get_queue() -> Queue:
    return Queue(
        "default",
        connection=current_app.extensions["redis"],
        is_async=current_app.config["QUEUE_ASYNC"],
    )
