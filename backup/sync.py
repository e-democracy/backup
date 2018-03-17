import logging
from multiprocessing import cpu_count, Value
from queue import Empty, Queue
import random
from threading import Thread
import time

from backup.client.edemocracy import EDemocracyClient
from backup.store.sqlite import Store

logger = logging.getLogger(__name__)


class Sync:
    def group_members(group, client, store):
        """
        Syncs the membership of provided group.
        :param groups: ID of the group to sync
        :param client: Client to sync from
        :param store: Store to sync to
        """
        store.save_group_members(group, client.get_group_members(group))

    def member_profile(member, client, store):
        """
        Syncs the profile of the provided member.
        :param members: ID of the member to sync
        :param client: Client to sync from
        :param store: Store to sync to
        """
        store.save_member_profile(client.get_profile_of_member(member))

    def message_ids_of_group_and_month(args, client, store):
        """
        Saves all of the message ids of the given group and month from
        the client to the store.

        :param args: Dict of arguments for the sync. Arguments include:
                     'group': ID of the group to sync
                     'month': Month of the group to sync, in the format YYYYMM
        :param client: Client to sync from
        :param store: Store to sync to
        """
        store.create_group_messages(args['group'],
            client.get_messages_of_group_and_month(args['group'],
                                                   args['month']))

    def message(args, client, store):
        """
        Syncs an individual message from a group.

        :param args: Dict of arguments for the sync. Arguments include:
                     'group_id': ID of the group to sync
                     'message_id': ID of the message to sync.
        :param client: Client to sync from
        :param store: Store to sync to
        """
        store.update_group_messages({
            'id': args['message_id'],
            'body': client.get_message_of_group(args['group_id'],
                                                args['message_id'])
        })


class Threaded:
    # Notes on multithreaded steps:
    # - item lists act as a work queue for syncing;
    # - each worker has it's own client (request sessions are not thread safe);
    # - every worker has it's own data store (sqlite objects are not
    #   threadsafe, though file access is thread safe).
    def __init__(self, func, items, master_client, db_path):
        self.func = func
        self.master_client = master_client
        self.db_path = db_path
        self.queue = Queue()

        for item in items:
            self.queue.put(item)

        self.current_count = Value('i', 0)
        self.total_count = Value('i', self.queue.qsize())

    def worker(func, queue, master_client, db_path,
               current_count, total_count):
        client = EDemocracyClient(master_client)
        with Store(db_path) as store:
            while True:
                try:
                    item = queue.get(False)
                except Empty:
                    break

                with current_count.get_lock():
                    current_count.value += 1
                    logger.info("Syncing item %s of %s" %
                                (current_count.value, total_count.value))

                try:
                    func(item, client, store)
                except Exception as e:
                    logger.exception(e)
                finally:
                    queue.task_done()
                    time.sleep(random.uniform(0.5, 1.5))

    def __call__(self):
        for i in range(cpu_count()):
            worker = Thread(target=Threaded.worker,
                            args=(self.func, self.queue,
                                  self.master_client, self.db_path,
                                  self.current_count, self.total_count))
            worker.start()

        self.queue.join()
