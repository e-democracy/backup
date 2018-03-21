import json
import logging
import logging.config
import os.path
import time
from backup.client.edemocracy import EDemocracyClient
from backup.store.sqlite import Store
from backup.sync import Sync, Threaded


DB_PATH = 'db/prod.sqlite'

LOG_CONFIG_PATH = 'config/logging.conf'
if os.path.isfile(LOG_CONFIG_PATH):
    logging.config.fileConfig(LOG_CONFIG_PATH)
logger = logging.getLogger('backup')


def get_username_password():
    username = input('Username: ')
    password = input('Password: ')
    return (username, password)


def sync_group_members_and_profiles():
    (username, password) = get_username_password()

    with EDemocracyClient() as master_client, \
            Store(DB_PATH) as master_store:
        try:
            # Login to the site; worker clients will use the same server
            # session
            master_client.login(username, password)

            # Fetch list of groups
            logger.info("Fetching list of groups")
            groups = master_client.get_groups()
            logger.info("Fetching list of groups complete")

            # Multithreaded sync of group membership
            logger.info("%i groups to sync membership of" % len(groups))
            Threaded(Sync.group_members, groups, master_client, DB_PATH)()
            logger.info("Group membership syncing complete")

            # List of all members to get profiles for
            members = master_store.fetch_all_unique_group_members()

            logger.info("%i member profiles to sync" % len(members))
            # Multithreaded sync of member profiles
            Threaded(Sync.member_profile, members, master_client, DB_PATH)()
            logger.info("Member Profile syncing complete")
        finally:
            master_client.logout()


def sync_message_ids_for_month():
    (username, password) = get_username_password()
    month = input('Month (YYYYMM): ')

    with EDemocracyClient() as master_client, \
            Store(DB_PATH) as master_store:
        try:
            # Login to the site; worker clients will use the same server
            # session
            master_client.login(username, password)

            # Get groups already in the store
            groups = master_store.fetch_all_groups()
            args = [{'group': group, 'month': month} for group in groups]

            # Multithreaded sync of message IDs
            logger.info("%i groups to message IDs for" % len(groups))
            Threaded(Sync.message_ids_of_group_and_month, args,
                     master_client, DB_PATH)()
            logger.info("Group message ID syncing complete")
        finally:
            master_client.logout()


def sync_message_ids_for_all_months():
    def get_months(group, client):
        logger.info("Fetching months for group %s" % group)
        try:
            time.sleep(0.5)
            return client.get_message_months_of_group(group)
        except Exception as e:
            logger.exception(e)
            return []

    (username, password) = get_username_password()

    with EDemocracyClient() as master_client, \
            Store(DB_PATH) as master_store:
        try:
            # Login to the site; worker clients will use the same server
            # session
            master_client.login(username, password)

            # Get groups already in the store
            groups = master_store.fetch_all_groups()

            # Get months to fetch for each group
            # This does a serial fetch of months from each group.
            logger.info(
                "Gathering all months which have posts from all groups")
            args = [
                {'group': group, 'month': month}
                for group in groups
                for month in get_months(group, master_client)
            ]
            logger.info("Finished gathering all months from all groups")

            # Multithreaded sync of message IDs
            logger.info("%i groups X months to get message IDs for" %
                        len(args))
            Threaded(Sync.message_ids_of_group_and_month, args,
                     master_client, DB_PATH)()
            logger.info("Group message ID syncing complete")
        finally:
            master_client.logout()


def sync_empty_messages():
    (username, password) = get_username_password()

    with EDemocracyClient() as master_client, \
            Store(DB_PATH) as master_store:
        try:
            # Login to the site; worker clients will use the same server
            # session
            master_client.login(username, password)

            # Get empty messages in the store
            messages = master_store.fetch_empty_group_messages()

            # Multithreaded sync of message IDs
            logger.info("%i message bodies to sync" % len(messages))
            Threaded(Sync.message, messages, master_client, DB_PATH)()
            logger.info("Message syncing complete")
        finally:
            master_client.logout()


def print_group_member_email_addresses():
    group = input('Group ID: ')
    output_file = input('Output File: ')
    with Store(DB_PATH) as store, open(output_file, 'w') as f:
        members = store.fetch_members_of_group(group)
        profiles = [store.fetch_profile_of_member(member) for member in
                    members]
        emails = [profile['email'][0] for profile in filter(None, profiles)]
        json.dump(emails, f)


if __name__ == '__main__':
    print("Commands")
    print("\t 1: Sync the memberships of groups and profiles of members")
    print("\t 2: Sync message IDs across all groups for a specific month")
    print("\t 3: Sync messages IDs across all groups for all time")
    print("\t 4: Sync messages in the DB that do not currently have a body")
    print("\t 5: Export email addresses of member of a group to a file")
    command = input('Command: ')
    {
        '1': sync_group_members_and_profiles,
        '2': sync_message_ids_for_month,
        '3': sync_message_ids_for_all_months,
        '4': sync_empty_messages,
        '5': print_group_member_email_addresses
    }[command]()
