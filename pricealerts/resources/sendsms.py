# -*- coding: utf-8 -*-
from flask_restful import Resource

from utils.notifications import NotificationDispatcher


class SMSResource(Resource):
    def post(self, from_name, to_name, to_phone, text):
        return {
            "message":
                NotificationDispatcher.send_sms(from_name, to_name, to_phone,
                                                to_name)
        }
