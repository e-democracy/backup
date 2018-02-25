import json
import requests_mock
import unittest

from backup.client.edemocracy import EDemocracyClient, \
    EDemocracyClientException


@requests_mock.Mocker()
class EDemocracyClientTestCase(unittest.TestCase):
    def setUp(self):
        self.client = EDemocracyClient()

        # Set some fixtures
        self.group_a_members_json = json.dumps(['member0', 'member1'])
        self.member_profile = {
            "id": "member0",
            "givenName": "First",
            "familyName": "Last",
            "fn": "First Last",
            "biography": "This is my life",
            "neighbourhood": "Neighborhood",
            "region": "Region",
            "locality": "Locality",
            "countryName": "Country",
            "adr_postal_code": "12345",
            "url": "http://example.com",
            "org": "Organization",
            "org_url": "http://organization.example.com",
            "tz": None,
            "email": [
                "person@example.com",
                "personA@example.com"
            ]
        }
        self.member_profile_json = json.dumps(self.member_profile)

        self.group_a_messages = ['message1', 'message2']
        self.group_a_messages_list_json = json.dumps(self.group_a_messages)
        self.group_a_message0 = """
        This is a message
        It Has Lines
        """

        with open('tests/fixtures/pages/groups.html') as f:
            self.group_page_html = f.read()
        with open('tests/fixtures/pages/messages_export.html') as f:
            self.group_message_export_html = f.read()

    def test_init_with_existing_client(self, mr):
        self.client.session.cookies['__ac'] = 'foo'
        self.client.session.cookies['SERVERID'] = 'bar'

        new_client = EDemocracyClient(self.client)
        self.assertEqual('foo', new_client.session.cookies['__ac'])
        self.assertEqual('bar', new_client.session.cookies['SERVERID'])

    ########################################
    # Group Membership
    ########################################

    def test_get_groups(self, mr):
        mr.get('http://forums.e-democracy.org/groups/',
               text=self.group_page_html)
        expectedGroups = ['another_group', 'city-central', 'city-issues',
                          'design', 'hub', 'other_secret', 'secret']

        self.assertEqual(self.client.get_groups(), expectedGroups)

    def test_get_groups_retrieval_error(self, mr):
        mr.get('http://forums.e-democracy.org/groups/',
               status_code=500)

        with self.assertRaises(EDemocracyClientException):
            self.client.get_groups()

    def test_get_group_members(self, mr):
        mr.get('http://forums.e-democracy.org/groups/a_group/members.json',
               text=self.group_a_members_json)
        expectedMembers = ['member0', 'member1']

        self.assertEqual(self.client.get_group_members('a_group'),
                         expectedMembers)

    def test_group_members_retrieval_error(self, mr):
        mr.get('http://forums.e-democracy.org/groups/a_group/members.json',
               status_code=500)

        with self.assertRaises(EDemocracyClientException):
            self.client.get_group_members('a_group')

    ########################################
    # Member Profiles
    ########################################

    def test_get_profile_of_member(self, mr):
        mr.get('http://forums.e-democracy.org/p/member0/profile.json',
               text=self.member_profile_json)

        self.assertEqual(self.client.get_profile_of_member('member0'),
                         self.member_profile)

    def test_get_profile_of_member_retrieval_error(self, mr):
        mr.get('http://forums.e-democracy.org/p/member0/profile.json',
               status_code=500)

        with self.assertRaises(EDemocracyClientException):
            self.client.get_profile_of_member('member0')

    ########################################
    # Group Messages
    ########################################

    def test_get_messages_of_group_and_month(self, mr):
        mr.get('http://forums.e-democracy.org/groups/a_group/messages/'
               'gs-group-messages-export-posts.json?month=201801',
               text=self.group_a_messages_list_json)

        self.assertCountEqual(self.client.get_messages_of_group_and_month(
            'a_group', '201801'), self.group_a_messages)

    def test_get_messages_of_group_and_month_retrieval_error(self, mr):
        mr.get('http://forums.e-democracy.org/groups/a_group/messages/'
               'gs-group-messages-export-posts.json?month=201801',
               status_code=500)

        with self.assertRaises(EDemocracyClientException):
            self.client.get_messages_of_group_and_month('a_group', '201801')

    def test_get_message_of_group(self, mr):
        mr.get('http://forums.e-democracy.org/groups/a_group/messages/'
               'gs-group-messages-export-mbox/message0',
               text=self.group_a_message0)

        self.assertCountEqual(self.client.get_message_of_group(
            'a_group', 'message0'), self.group_a_message0)

    def test_get_message_of_group_retrieval_error(self, mr):
        mr.get('http://forums.e-democracy.org/groups/a_group/messages/'
               'gs-group-messages-export-mbox/message0',
               status_code=500)

        with self.assertRaises(EDemocracyClientException):
            self.client.get_message_of_group('a_group', 'message0')

    def test_get_message_months_of_group(self, mr):
        mr.get('http://forums.e-democracy.org/groups/hub/messages/export.html',
               text=self.group_message_export_html)
        expected_months = ['201510', '201403']

        self.assertEqual(self.client.get_message_months_of_group('hub'),
                         expected_months)

    def test_get_message_months_of_group_retrieval_error(self, mr):
        mr.get('http://forums.e-democracy.org/groups/hub/messages/export.html',
               status_code=500)

        with self.assertRaises(EDemocracyClientException):
            self.client.get_message_months_of_group('hub')
