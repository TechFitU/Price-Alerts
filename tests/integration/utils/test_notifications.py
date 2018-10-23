# -*- coding: utf-8 -*-
"""
NotificationsTest class
Class tested: NotificationDispatcher

Only test methods that depends on databases or work with other classes and methods of your app
"""
import datetime
import os
from smtplib import SMTPServerDisconnected

from mock import patch, Mock, MagicMock
import  pricealerts.utils.notifications as notifications
from tests.base_test import BaseTest


class NotificationDispatcherTest(BaseTest):
    def setUp(self):
        super(NotificationDispatcherTest, self).setUp()

    def test_send_email_ok(self):

        res = notifications.NotificationDispatcher.send_email('Alxe', 'alexmtnezf@gmail.com', 'alexmtnezf@gmail.com', 'dads', 'dads')
        self.assertTrue(res)
