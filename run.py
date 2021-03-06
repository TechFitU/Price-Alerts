# -*- coding: utf-8 -*-
import argparse

from pricealerts import create_app
from pricealerts.db import db
from pricealerts.models import UserModel

application = create_app()
# a simple page that says hello
with application.app_context():
    db.init_app(application)

    if application.config['ENV'] == 'development':
        @application.before_first_request
        def create_all_tables():
            db.drop_all()
            db.create_all()

            # Create initial data
            user = UserModel.find_by(username='alexmtnezf@gmail.com')
            if not user:
                user = UserModel('Alex', 'alexmtnezf@gmail.com', '123456', is_admin=True)
                db.session.add(user)
                db.session.commit()

    if application.config['ENV'] == 'production':
        @application.before_first_request
        def create_all_tables():
            db.create_all()

            # Create initial data
            user = UserModel.find_by(username='alexmtnezf@gmail.com')
            if not user:
                user = UserModel('Alex', 'alexmtnezf@gmail.com', '123456', is_admin=True)
                db.session.add(user)
                db.session.commit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    application.run(port=args.port, host=args.host)
