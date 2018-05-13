from tests import config
from mock import call, patch, Mock, NonCallableMock
import unittest

from backup.client.edemocracy import EDemocracyClient
from backup.sync import Sync, Threaded


class SyncTestCase(unittest.TestCase):
    def setUp(self):
        self.client = EDemocracyClient()
        self.store = NonCallableMock()

        # Set some fixtures
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

        self.group_messages = {
            'message0': 'Hello',
            'message1': 'There'
        }

    def test_group_members(self):
        expected_members = ['member0', 'member1']
        self.client.get_group_members = Mock(return_value=expected_members)

        Sync.group_members('groupA', self.client, self.store)
        self.store.save_group_members.assert_called_with('groupA',
                                                         expected_members)

    def test_member_profiles(self):
        self.client.get_profile_of_member = Mock(
            return_value=self.member_profile
        )

        Sync.member_profile('member0', self.client, self.store)
        self.store.save_member_profile \
                  .assert_called_with(self.member_profile)

    def test_message_ids_of_group_and_month(self):
        self.client.get_messages_of_group_and_month = Mock(
            return_value=list(self.group_messages.keys())
        )

        Sync.message_ids_of_group_and_month({
            'group': 'someGroup',
            'month': '201801'},
            self.client, self.store)
        self.store.create_group_messages \
            .assert_called_with('someGroup', list(self.group_messages.keys()))

    def test_message(self):
        def group_message(_, message):
            return self.group_messages[message]
        self.client.get_message_of_group = Mock(side_effect=group_message)

        Sync.message({
            'group_id': 'someGroup',
            'message_id': 'message0'},
            self.client, self.store)
        self.store.update_group_messages.assert_called_with(
            {'id': 'message0', 'body': 'Hello'}
        )


class ThreadedTestCase(unittest.TestCase):
    @patch('time.sleep')  # Skip sleeping
    @patch('backup.sync.Store')
    @patch('backup.sync.EDemocracyClient')
    def test(self, mock_client, mock_store, mock_time):
        mock_store.return_value.__enter__.return_value = mock_store
        func = Mock()
        master_client = Mock()

        # Create and call the threaded function
        threaded = Threaded(func, [i for i in range(10)],
                            master_client, config['DatabasePath'])
        threaded()

        # Assert that the provided function was called with a Store
        # and EDemocracyClient
        func.assert_has_calls(
            [call(i,
                  mock_client.return_value,
                  mock_store)
             for i in range(10)],
            any_order=True
        )
