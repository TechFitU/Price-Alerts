# -*- coding: utf-8 -*-
"""
NotificationsTest class
Class tested: NotificationDispatcher

Only test methods that depends on databases or work with other classes and methods of your app
"""
import unittest
from smtplib import SMTPServerDisconnected, SMTPAuthenticationError

from mock import patch, Mock, MagicMock
import pricealerts.utils.notifications as notifications
from tests.base_test import BaseTest


class NotificationDispatcherTest(BaseTest):
    def setUp(self):
        super(NotificationDispatcherTest, self).setUp()

    def test_send_email_ok(self):
        res = notifications.NotificationDispatcher.send_email('Alxe', 'alexmtnezf@gmail.com', 'alexmtnezf@gmail.com',
                                                              'Subject', 'Email content')
        self.assertTrue(res)

    def test_send_email_with_smtp(self):

        mocked_post_response = MagicMock()
        mocked_post_response.status_code = 500
        with patch('pricealerts.utils.notifications.requests.post', return_value=mocked_post_response) as mocked_requests:

            res = notifications.NotificationDispatcher.send_email('Alxe', 'alexmtnezf@gmail.com', 'alexmtnezf@gmail.com', 'dads', 'dads')
            self.assertFalse(res)

    def test_send_email_fails(self):

        mocked_post_response = MagicMock()
        mocked_post_response.status_code = 500
        with patch('pricealerts.utils.notifications.requests.post', return_value=mocked_post_response) as mocked_requests:

            with patch('pricealerts.utils.notifications.smtplib') as mocked_smtplib:
                mocked_smtplib.SMTP_SSL = Mock(side_effect=SMTPServerDisconnected)
                mocked_smtplib.SMTP = Mock(side_effect=SMTPAuthenticationError)
                res = notifications.NotificationDispatcher.send_email('Alxe', 'alexmtnezf@gmail.com', 'alexmtnezf@gmail.com', 'dads', 'dads')
                self.assertFalse(res)


if __name__ == "__main__":
    unittest.main()
    import doctest

    doctest.testmod()
