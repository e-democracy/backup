from backup import config, ConfigKey
import json
import sqlite3
import unittest
from backup.store.sqlite import Store


class SQLiteStoreTestCase(unittest.TestCase):

    def setUp(self):
        print(ConfigKey.DATABASE_PATH)
        print(config)
        self.db = sqlite3.connect(config[ConfigKey.DATABASE_PATH])
        self.store = Store(config[ConfigKey.DATABASE_PATH])

    def tearDown(self):
        self.clearDatabase()
        self.db.close()

    def clearDatabase(self):
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT name from sqlite_master where type = 'table'
        ''')
        for table in [table[0] for table in cursor
                      if table[0] != '_yoyo_migration']:
            cursor.execute('DELETE from %s' % table)
        self.db.commit()

    def populate_mock_group_members(self):
        mock_group_members = {
            'groupA': ['member0', 'member1', 'member2'],
            'groupB': ['member0', 'member1'],
            'groupC': ['member0']
        }
        cursor = self.db.cursor()
        for mock_group in mock_group_members:
            cursor.execute('INSERT into group_members values (?, ?)',
                           (mock_group,
                            json.dumps(mock_group_members[mock_group])))
        self.db.commit()
        return mock_group_members

    def populate_mock_member_profile(self, id):
        mock_profile = {
            'id': id,
            'attr9': 'value9'
        }
        cursor = self.db.cursor()
        cursor.execute('INSERT into member_profiles values (?, ?)',
                       (id, json.dumps(mock_profile)))
        self.db.commit()
        return mock_profile

    def populate_mock_messages(self, group_id, messages):
        if type(messages) is not list:
            messages = [messages]
        cursor = self.db.cursor()
        for message in messages:
            if type(message) is not dict:
                message = {'id': message, 'body': None}
            cursor.execute('INSERT into group_messages values (?, ?, ?)',
                           (message['id'], group_id, message['body']))
        self.db.commit()

    ########################################
    # Group Membership
    ########################################

    def test_fetch_all_groups(self):
        # Initial state: groups A, B, and C exist
        mock_groups = list(self.populate_mock_group_members().keys())

        with self.store as store:
            self.assertCountEqual(mock_groups, store.fetch_all_groups())

    ########################################
    # Group Membership
    ########################################

    def test_save_group_members(self):
        # Initial state: No group members.

        # Save members of groupA as members 0 and 1.
        expected_members = ['member0', 'member1']
        with self.store as store:
            store.save_group_members('groupA', expected_members)

        # Assert that groupA's membership is 0 and 1.
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT member_ids from group_members WHERE group_id = 'groupA'
        ''')
        saved_members = json.loads(cursor.fetchone()[0])
        self.assertCountEqual(expected_members, saved_members)

    def test_save_group_members_overwrite(self):
        # Initial state: groupA has members 9, 8, and 0.
        cursor = self.db.cursor()
        cursor.execute('INSERT into group_members values (?, ?)',
                       ('groupA',
                        json.dumps(['member9', 'member8', 'member0'])))
        self.db.commit()

        # Save members of groupA as members 0 and 1.
        expected_members = ['member0', 'member1']
        with self.store as store:
            store.save_group_members('groupA', expected_members)

        # Assert that groupA's membership is 0 and 1.
        cursor.execute('''
            SELECT member_ids from group_members WHERE group_id = 'groupA'
        ''')
        saved_members = json.loads(cursor.fetchone()[0])
        self.assertCountEqual(expected_members, saved_members)

    def test_fetch_members_of_group(self):
        # Initial State: 3 groups with overlapping membership
        mock_group_members = self.populate_mock_group_members()

        # Fetch and assert groups of members
        for group in mock_group_members:
            with self.store as store:
                groups = store.fetch_members_of_group(group)
                self.assertCountEqual(mock_group_members[group], groups)

    def test_fetch_members_of_group_no_members(self):
        # Initial State: A group with no members
        cursor = self.db.cursor()
        cursor.execute('INSERT into group_members values (?, ?)',
                       ('groupZ', json.dumps([])))
        self.db.commit()

        # Fetch and assert group has no members
        with self.store as store:
            members = store.fetch_members_of_group('groupZ')
            self.assertEqual([], members)

    def test_fetch_members_of_group_no_group(self):
        # Initial State: A group doesn't exist
        # Fetch and assert group is None
        with self.store as store:
            members = store.fetch_members_of_group('groupZ')
            self.assertIsNone(members)

    def test_all_unique_group_members(self):
        # Initial State: 3 groups with overlapping membership
        self.populate_mock_group_members()
        expected_unique_members = ['member0', 'member1', 'member2']

        # Fetch and assert unique members of all groups
        with self.store as store:
            unique_members = store.fetch_all_unique_group_members()
            self.assertCountEqual(expected_unique_members, unique_members)

    def test_all_unique_group_members_no_members(self):
        # Initial State: No members

        # Fetch and assert empty list of unique members
        with self.store as store:
            unique_members = store.fetch_all_unique_group_members()
            self.assertEqual([], unique_members)

    def test_fetch_groups_of_member(self):
        # Initial State: 3 groups with overlapping membership
        self.populate_mock_group_members()

        # Fetch and assert groups of members
        with self.store as store:
            groups = store.fetch_groups_of_member('member0')
            self.assertCountEqual(['groupA', 'groupB', 'groupC'], groups)

        with self.store as store:
            groups = store.fetch_groups_of_member('member1')
            self.assertCountEqual(['groupA', 'groupB'], groups)

        with self.store as store:
            groups = store.fetch_groups_of_member('member2')
            self.assertCountEqual(['groupA'], groups)

    def test_fetch_groups_of_member_no_groups(self):
        # Initial State: Nobody is a member of any group
        with self.store as store:
            groups = store.fetch_groups_of_member('member99')
            self.assertEqual([], groups)

    ########################################
    # Group Messages
    ########################################
    def test_create_group_messages_one_id(self):
        # Initial state: No message IDs.

        # Save message 0 of groupA.
        expected_message_id = 'message0'
        with self.store as store:
            store.create_group_messages('groupA', expected_message_id)

        # Assert that groupA has message id 0.
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT id from group_messages WHERE group_id = 'groupA'
        ''')
        saved_message_ids = [r[0] for r in cursor.fetchall()]
        self.assertCountEqual([expected_message_id], saved_message_ids)

    def test_create_group_messages_one_id_with_body(self):
        # Initial state: No message IDs.

        # Save message 0 of groupA.
        expected_message = {
            'id': 'message0',
            'body': 'Foo'
        }
        with self.store as store:
            store.create_group_messages('groupA', expected_message)

        # Assert that groupA has message id 0 with body.
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT id, body from group_messages WHERE group_id = 'groupA'
        ''')
        saved_message = cursor.fetchone()
        self.assertEqual(expected_message['id'], saved_message[0])
        self.assertEqual(expected_message['body'], saved_message[1])

    def test_create_group_messages_multiple_ids(self):
        # Initial state: No message IDs.

        # Save message 0 and 1 of groupA.
        expected_message_ids = ['message0', 'message1']
        with self.store as store:
            store.create_group_messages('groupA', expected_message_ids)

        # Assert that groupA has message ids 0 and 1.
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT id from group_messages WHERE group_id = 'groupA'
        ''')
        saved_message_ids = [r[0] for r in cursor.fetchall()]
        self.assertCountEqual(expected_message_ids, saved_message_ids)

    def test_create_messages_of_group_no_overwrite(self):
        # Initial state: Message 0 of Group A exists.
        self.populate_mock_messages('groupA',
                                    {
                                        'id': 'message0',
                                        'body': 'Stuff'
                                    })

        # Assert that creating messages 0 and 1 leaves message 0 untouched and
        # message 1 is created
        with self.store as store:
            store.create_group_messages('groupA', ['message0', 'message1'])

        cursor = self.db.cursor()
        cursor.execute('''
            SELECT id, body from group_messages WHERE group_id = 'groupA'
        ''')
        saved_message = cursor.fetchone()
        self.assertEqual('message0', saved_message[0])
        self.assertEqual('Stuff', saved_message[1])
        saved_message = cursor.fetchone()
        self.assertEqual('message1', saved_message[0])

    def test_update_message_of_group(self):
        # Initial state: Message 0 of Group A exists.
        self.populate_mock_messages('groupA', 'message0')

        # Update message 0 of group A
        mock_body = 'Mock'
        with self.store as store:
            store.update_group_messages({
                'id': 'message0',
                'body': mock_body
            })

        # Assert that message 0 of group A was updated.
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT id, group_id, body from group_messages
            WHERE id = 'message0'
        ''')
        saved_message = cursor.fetchone()
        self.assertEqual('message0', saved_message[0])
        self.assertEqual('groupA', saved_message[1])
        self.assertEqual(mock_body, saved_message[2])

    def test_update_messages_of_group(self):
        # Initial state: Message 0 and 1 of Group A exists.
        self.populate_mock_messages('groupA', ['message0', 'message1'])

        # Update messages 0 and 1
        message_updates = [
            {
                'id': 'message0',
                'body': 'foo'
            },
            {
                'id': 'message1',
                'body': 'bar'
            }
        ]
        with self.store as store:
            store.update_group_messages(message_updates)

        # Assert that body of message 0 and 1 were updated, and that group was
        # not.
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT id, group_id, body from group_messages
            WHERE id in ('message0', 'message1')
            ORDER BY id ASC
        ''')
        saved_messages = cursor.fetchall()
        self.assertCountEqual([m['id'] for m in message_updates],
                              [m[0] for m in saved_messages])
        for saved_message in saved_messages:
            self.assertEqual('groupA', saved_message[1])
        self.assertCountEqual([m['body'] for m in message_updates],
                              [m[2] for m in saved_messages])

    def test_fetch_empty_group_messages(self):
        # Initial state: Message 0 and 1 exist and are empty, message 2 exists
        # and has a body.
        self.populate_mock_messages('group_id', [
            'message0',
            'message1',
            {
                'id': 'message2',
                'body': 'Something!'
            }
        ])

        # Assert that messages 0 and 1 are found
        with self.store as store:
            self.assertCountEqual([
                {
                    'message_id': 'message0',
                    'group_id': 'group_id'
                },
                {
                    'message_id': 'message1',
                    'group_id': 'group_id'
                }], store.fetch_empty_group_messages())

    ########################################
    # Member Profiles
    ########################################

    def test_save_member_profile(self):
        # Initial State: No member profiles.

        # Save profile of member0.
        expected_profile = {
            'id': 'member0',
            'attr1': 'value1',
            'attr2': 'value2'
        }
        with self.store as store:
            store.save_member_profile(expected_profile)

        # Assert that member0's profile was saved.
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT profile from member_profiles WHERE id = 'member0'
        ''')
        saved_profile = json.loads(cursor.fetchone()[0])
        self.assertCountEqual(expected_profile, saved_profile)

    def test_save_member_profile_overwrite(self):
        # Initial state: member0 has a profile.
        self.populate_mock_member_profile('member0')

        # Save profile of member0.
        expected_profile = {
            'id': 'member0',
            'attr1': 'value1',
            'attr2': 'value2'
        }
        with self.store as store:
            store.save_member_profile(expected_profile)

        # Assert that member0's profile changed.
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT profile from member_profiles WHERE id = 'member0'
        ''')
        saved_profile = json.loads(cursor.fetchone()[0])
        self.assertCountEqual(expected_profile, saved_profile)

    def test_save_member_profile_no_id(self):
        # Assert that saving a profile without an ID raises
        with self.assertRaises(KeyError):
            with self.store as store:
                store.save_member_profile({
                    'attr': 'value'
                })

    def test_fetch_profile_of_member(self):
        # Initial state: member0 has a profile.
        expected_profile = self.populate_mock_member_profile('member0')

        # Fetch and assert profile of member
        with self.store as store:
            fetched_profile = store.fetch_profile_of_member('member0')
            self.assertEqual(expected_profile, fetched_profile)

    def test_fetch_profile_of_member_nonexistant(self):
        # Initial state: There are no member profiles.

        # Assert None when attempting to fetch nonexistant member
        with self.store as store:
            fetched_profile = store.fetch_profile_of_member('member0')
            self.assertIsNone(fetched_profile)
