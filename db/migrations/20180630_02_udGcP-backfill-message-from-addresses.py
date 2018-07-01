from pathlib import Path
import sys
from yoyo import step
sys.path.append(str(Path().absolute()))
from backup.store.sqlite import Store  # noqa: E402

"""
backfill_message_from_addresses
"""

__depends__ = {'20180630_01_lNcqH-add-message-sender-column'}


def backfill_rows(cursor, conn):
    store = Store(None)
    store.db = conn
    count = 0
    while True:
        count += 1
        if (count % 10) == 0:
            print(count * 100)
        rows = cursor.fetchmany(100)
        if not rows:
            break
        store.update_group_messages(
                [
                  {
                    'id': r[0],
                    'group_id': r[1],
                    'body': r[2]
                  } for r in rows
                ])


def backfill(conn):
    sql = """
    SELECT id, group_id, body
        FROM group_messages
        WHERE from_address is null
    """
    cursor = conn.cursor()
    cursor.execute(sql)
    backfill_rows(cursor, conn)


steps = [
    step(backfill)
]
