import unittest

from backup.utils.email_message_utility import EmailMessageUtility


class EmailMessageUtilityTestcase(unittest.TestCase):
    def setUp(self):
        self.utility = EmailMessageUtility()

    def test_get_sender_address(self):
        test_message = '''\
From dont@care.com Fri, 26 Jan 2018 01:23:45 +1100
Content-Type: text/plain; charset="us-ascii";
From: The Real Sender <real@sender.com>

Here is some body
'''

        self.assertEqual(self.utility.get_sender_address(test_message),
                         'real@sender.com')
