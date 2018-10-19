# -*- coding: utf-8 -*-
import logging
import os
import sys
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from twilio.rest import Client
from pricealerts.settings import env

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
    def send_email(cls, user_name, user_email, to_email, subject, message, secure=None,
                   timeout=env('EMAIL_SEND_TIMEOUT', default=10)):
        """
        Send emails with Mailgun Rest API
        If Mailgun fails, this method use SMTP server mg.techfitu.com for sending emails
        Docs: http://blog.tecladocode.com/learn-python-send-emails/

        """
        response = requests.post(
            env('API_BASE_URL'),
            auth=("api", env('API_KEY')),
            data={"from": "{} <{}>".format(env('BRAND_NAME') + " - " + env('PRODUCT_NAME'), env('EMAIL_FROM')),
                  "to": [to_email, "{} <{}>".format(user_name, user_email)],
                  "subject": subject,
                  "html": message,
                  "text": "Testing some Mailgun awesomness!"
                  })
        if response.status_code != 200:
            try:
                import smtplib
                from email.message import EmailMessage
                import email.utils

                port = int(env('SMTP_PORT', default=None))
                if not port:
                    port = smtplib.SMTP_PORT
                smtp = smtplib.SMTP(env('SMTP_SERVER'), port, timeout=int(timeout))
                msg = EmailMessage()
                msg['From'] = "{} <{}>".format(env('BRAND_NAME') + " - " + env('PRODUCT_NAME'), env('EMAIL_FROM'))
                msg['To'] = ','.join([to_email, "{} <{}>".format(user_name, user_email)])
                msg['Subject'] = subject
                msg['Date'] = email.utils.localtime()
                msg.set_content(message)

                username = env('SMTP_USER', default=None)
                password = env('SMTP_PASS', default=None)
                if username:
                    if secure is not None:
                        smtp.ehlo()
                        smtp.starttls(*secure)
                        smtp.ehlo()
                    smtp.login(username, password)
                smtp.send_message(msg)
                smtp.quit()
            except Exception as ex:
                logging.getLogger('root').error('Error sending email to users using SMTP server.\n{}'.format(str(ex)))
                raise


        return True
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
