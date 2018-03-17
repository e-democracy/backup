from bs4 import BeautifulSoup
import json
import logging
import re
import requests

BASE_URL = 'http://forums.e-democracy.org'

logger = logging.getLogger(__name__)


class EDemocracyClientException(Exception):
    pass


class EDemocracyLoginException(Exception):
    pass


class EDemocracyClient:

    def __init__(self, client=None):
        """
        A Client used to fetch data from the E-Democracy forums.
        If another instance of this client is provided, it's server session
        will also be used by the newly created client.

        :param client: An existing client to use the server session of
        """
        self.session = requests.Session()
        if client is not None:
            self.session.cookies = client.session.cookies.copy()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.session.close()

    def login(self, username, password):
        logger.info("Logging In")
        response = self.session.post('%s/login.html' % BASE_URL, {
            'login': username,
            'password': password
        }, allow_redirects=False)

        if response.status_code not in [302, 200]:
            raise EDemocracyClientException(
                'Error encountered logging into E-Democracy')

        if response.status_code != 302 or '__ac' not in response.cookies:
            raise EDemocracyLoginException('Login to E-Democracy unsuccessful')

        logger.info("Log In Successful")

    def logout(self):
        logger.info("Logging Out")
        self.session.get('%s/logout.html' % BASE_URL)

    def whoami(self):
        """
        :returns: Username of the logged in user, or None if not logged in.
        """
        profile = self.session.head('%s/p/' % BASE_URL)
        if profile.status_code != 302:
            raise EDemocracyClientException(
                'Problem retrieving logged in username from E-Democracy')

        if profile.headers['location'].startswith('/p/'):
            return profile.headers['location'][3:]
        else:
            return None

    def get_groups(self):
        """Fetches the list of currently available groups from the E-Democracy
        group list."""

        links_page = self.session \
                         .get('%s/groups/' % BASE_URL)
        if links_page.status_code != 200:
            raise EDemocracyClientException(
                'Problem retrieving groups from E-Democracy')

        soup = BeautifulSoup(links_page.text, 'html.parser')
        links = soup.find(id='bodyblock') \
                    .find_all('a', href=re.compile("^/groups/"))
        return sorted(list(set(
            [link.get('href').split('/')[2] for link in links
             if not link.get('href').startswith('/groups/leave.html')]
        )))

    def get_group_members(self, group_id):
        """Fetches the list of members of the provided group."""

        res = self.session \
                  .get('%s/groups/%s/members.json' % (BASE_URL, group_id))
        if res.status_code != 200:
            raise EDemocracyClientException(
                'Problem retrieving group membership for %s from '
                'E-Democracy' % group_id)

        return json.loads(res.text)

    def get_profile_of_member(self, member_id):
        """Fetches the profile of the provided member."""
        res = self.session \
                  .get('%s/p/%s/profile.json' % (BASE_URL, member_id))
        if res.status_code != 200:
            raise EDemocracyClientException(
                'Problem retrieving profile for %s from '
                'E-Democracy' % member_id)

        return json.loads(res.text)

    def get_messages_of_group_and_month(self, group_id, month):
        """
        Fetches a list of message IDs for messages posted to the specified
        group in the specified month.

        :param group_id: ID of the group to get messages for
        :param month: Month to get messages for. String of the format 'YYYYMM'
        :returns: List of messages posted to the group in the specified month.
        """
        res = self.session \
                  .get('%s/groups/%s/messages/'
                       'gs-group-messages-export-posts.json?month=%s' %
                       (BASE_URL, group_id, month))
        if res.status_code != 200:
            raise EDemocracyClientException(
                'Problem retrieving list of messages for %s in %s from '
                'E-Democracy' % (group_id, month))

        return json.loads(res.text)

    def get_message_of_group(self, group_id, message_id):
        """
        Fetches the body of a specific message from a specific group.

        :param group_id: ID of the group to get message from
        :param message_id: ID of the message to fetch
        :returns: Text of the message
        """
        res = self.session \
                  .get('%s/groups/%s/messages/'
                       'gs-group-messages-export-mbox/%s' %
                       (BASE_URL, group_id, message_id))
        if res.status_code != 200:
            raise EDemocracyClientException(
                'Problem retrieving message %s from group %s'
                'E-Democracy' % (message_id, group_id))

        return res.text

    def get_message_months_of_group(self, group_id):
        """
        Fetches a list of all months that the specified group has messages in.

        :param group_id: ID of group to fetch months of messages for.
        :returns: List of months that have messages, in the format YYYYMM.
        """
        export_page = self.session \
                          .get('%s/groups/%s/messages/export.html' %
                               (BASE_URL, group_id))
        if export_page.status_code != 200:
            raise EDemocracyClientException(
                'Problem retrieving groups from E-Democracy')

        soup = BeautifulSoup(export_page.text, 'html.parser')
        items = soup.find(id='bodyblock') \
                    .find(id='gs-group-messages-export-list') \
                    .find_all('button',
                              class_='gs-group-messages-export-list-item-'
                                     'buttons-generate')
        return [item.get('data-month') for item in items]
