import json
import sqlite3


class Store:
    def __init__(self, db_file):
        self.db_file = db_file

    def __enter__(self):
        self.db = sqlite3.connect(self.db_file)
        return self

    def __exit__(self, *args):
        self.db.close()

    ########################################
    # Groups
    ########################################

    def fetch_all_groups(self):
        """
        Returns a list of all groups currently in the store.

        :returns: List of groups IDs
        """
        cursor = self.db.cursor()
        cursor.execute('''
        SELECT DISTINCT group_id
        FROM group_members
        ''')
        return [group[0] for group in cursor]

    ########################################
    # Group Membership
    ########################################

    def save_group_members(self, group_id, members):
        """
        Saves the provided membership of the specified group. Any existing
        membership will be overwritten.

        :param group_id: String ID of the group to save members for.
        :param members: List of string IDs of members of the group.
        """
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT OR REPLACE into group_members values(?, ?)
        ''', (group_id, json.dumps(members)))
        self.db.commit()

    def fetch_members_of_group(self, group_id):
        """
        Fetches the members of the specified group. If the specified group has
        no members, an empty list is returned. If the specified group does not
        exist, None is returned.

        :param group_id: Group to fetch members of.
        :returns: List of members of the specified group, or None.
        """
        cursor = self.db.cursor()
        cursor.execute('''
        SELECT member_ids FROM group_members WHERE group_id = ?
        ''', (group_id,))
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None

    def fetch_all_unique_group_members(self):
        """
        Fetches every unique member of all groups.

        :returns: List of every unique member of any group.
        """
        cursor = self.db.cursor()
        cursor.execute('''
        SELECT DISTINCT json_each.value
        FROM group_members, json_each(group_members.member_ids)
        ''')
        return [member[0] for member in cursor]

    def fetch_groups_of_member(self, member_id):
        """
        Fetches the groups that the specified member is a member of. If the
        specified ID is not a member of any groups, an empty list is returned.

        :param member_id: Member to fetch groups of.
        :returns: List of groups of the specified member.
        """
        cursor = self.db.cursor()
        cursor.execute('''
        SELECT group_id
        FROM group_members, json_each(group_members.member_ids)
        WHERE json_each.value = ?
        ''', (member_id,))
        return [group[0] for group in cursor]

    ########################################
    # Group Messages
    ########################################

    def create_group_messages(self, group_id, messages):
        """
        Creates the specified messages of the specified group.

        Messages can be a list or a single item. If messages is a list, every
        message will be create for the specified group. If messages is a single
        item, then that individual message will be created for the specified
        group.

        Any individual 'message' can be a dict or a string. If a 'message' is a
        dict, the 'id' and 'body' attributes will be used to create the message
        id and body. If a 'message' is a string, then that string will be used
        as a message_id and no body will be saved. In both cases, all writes
        will take place in a single database transaction.

        :param group_id: ID of the group to save messages for
        :param messages: The message or messages to save
        """
        if type(messages) is not list:
            messages = [messages]

        cursor = self.db.cursor()

        for message in messages:
            message = message.copy() if type(message) is dict else {
                'id': message,
                'body': None
            }
            message['group_id'] = group_id

            columns = ', '.join(message.keys())
            placeholders = ', '.join('?' * len(message))
            sql = '''
                INSERT into group_messages ({}) values({})
            '''.format(columns, placeholders)

            try:
                cursor.execute(sql, tuple(message.values()))
            except sqlite3.IntegrityError as e:
                if str(e) == 'UNIQUE constraint failed: group_messages.id':
                    continue
                raise e

        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

    def update_group_messages(self, messages):
        """
        Updates the specified messages.

        Messages can be a list or a single item. If messages is a list, every
        message will be updated. If messages is a single item, then that
        individual message will be updated. In both cases, all writes
        will take place in a single database transaction.

        Messages must be a dict. The 'id' attribute will be used to find the
        message, and any other specified attributes will be updated.

        :param messages: The message or messages to update
        """
        if type(messages) is not list:
            messages = [messages]

        cursor = self.db.cursor()

        for message in messages:
            if type(message) is not dict:
                raise TypeError("Message must be a dict")
            message = message.copy()
            message_id = message.pop('id')
            sets = ','.join(["%s = ?" % c for c in message.keys()])
            sql = '''
                UPDATE group_messages
                SET {}
                WHERE id = ?
            '''.format(sets)
            cursor.execute(sql, tuple(message.values()) + (message_id,))

        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

    def fetch_empty_group_messages(self):
        """
        Fetches IDs and groups of all group messages that do not currently have
        a body. Returned list includes dicts with 'id' for message ID and
        'group_id' for group ID.

        :return Iterable of dicts of messages that have no body
        """
        cursor = self.db.cursor()
        cursor.execute('''
        SELECT id, group_id
        FROM group_messages
        WHERE body IS NULL
        ''')
        return [{'message_id': m[0], 'group_id': m[1]} for m in cursor]

    ########################################
    # Member Profiles
    ########################################

    def save_member_profile(self, profile):
        """
        Saves the provided member profile. If a profile already exists that
        matches the provided profile's 'id' attribute, that profile will be
        overwritten by the provided one.

        :param profile: Dict of a profile to save.
        """
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT OR REPLACE into member_profiles values(?, ?)
        ''', (profile['id'], json.dumps(profile)))
        self.db.commit()

    def fetch_profile_of_member(self, member_id):
        """
        Fetches the profile of the specified member. If the specified member
        does not exist, None is returned.

        :param member_id: Member to fetch profile of.
        :returns: Dict of the member's profile, or None.
        """
        cursor = self.db.cursor()
        cursor.execute('''
        SELECT profile  FROM member_profiles WHERE id = ?
        ''', (member_id,))
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None
