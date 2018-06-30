from email.parser import HeaderParser
from email.utils import parseaddr


class EmailMessageUtility:
    def __init__(self):
        self.hp = HeaderParser()

    def get_sender_address(self, msg):
        """
        Get the email address of the sender of a message.

        :param msg: Complete email message with headers as a string
        :returns: Email address of the sender as a string
        """
        headers = self.hp.parsestr(msg)
        return parseaddr(headers['from'])[1]
