# -*- coding: utf-8 -*-

import os
import sys
from email.message import EmailMessage

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from twilio.rest import Client
from pricealerts.settings import env
import smtplib

class NotificationDispatcher(object):
    @classmethod
    def send_sms(cls, from_name, to_name, to_phone, text):
        client = Client(
            env('ACCOUNT_SID'),
            env('AUTH_TOKEN'))

        message = client.messages.create(
            body='\nFrom: {}\nTo: {}\n{}'.format(from_name, to_name, text),
            from_=env('FROM_PHONE'),
            to=to_phone)

        return message.sid

    @classmethod
    def send_email(cls, user_name, user_email, to_email, subject, message):
        """
        Sending emails with Mailgun, if fails with SMTP server in my domain (credentials in file local.env)
        Docs: http://blog.tecladocode.com/learn-python-send-emails/

        """
        return requests.post(
            env('API_BASE_URL'),
            auth=("api", env('API_KEY')),
            data={"from": "{} <{}>".format(env('BRAND_NAME') + " - " + env('PRODUCT_NAME'), env('ADMIN_EMAIL')),
                  "to": [to_email, "{} <{}>".format(user_name, user_email)],
                  "subject": subject,
                  "html": message,
                  "text": "Testing some Mailgun awesomness!"
                  })
        #You can see a record of this email in your logs: https://app.mailgun.com/app/logs

    @classmethod
    def send_test_email(cls):
        return requests.post(
            env('API_BASE_URL'),
            auth=("api", env('API_KEY')),
            data={"from": env('EMAIL_FROM'),
                  "to": ["admin@techfitu.com", "alexmtnezf@gmail.com"],
                  "subject": "Hello",
                  "text": "Testing some Mailgun awesomness!"})




if __name__ == "__main__":
    # NotificationDispatcher.send_sms('Alex', 'Niobis', '+12106105564','Felicidades')
    NotificationDispatcher.send_test_email()
