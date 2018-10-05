import os

from pricealerts import create_app
from pricealerts.db import db
from pricealerts.models.model import AlertModel
from apscheduler.schedulers.blocking import BlockingScheduler

from pricealerts.settings import env

sched = BlockingScheduler()

@sched.scheduled_job('interval', seconds=env('ALERT_CHECK_TIMEOUT',default=10))
def job():
    app = create_app()
    with app.app_context():
        db.init_app(app)
        alerts_needing_update = AlertModel.find_needing_update()

        for alert in alerts_needing_update:
            alert.load_price_change()
            alert.send_email_if_price_limit_reached()

sched.start()