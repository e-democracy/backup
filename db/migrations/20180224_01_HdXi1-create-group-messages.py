"""
create_group_messages
"""

from yoyo import step

__depends__ = {}

steps = [
    step("""
        CREATE TABLE IF NOT EXISTS
        group_messages
        (id TEXT PRIMARY KEY ASC, group_id TEXT, body TEXT)
    """, """
        DROP TABLE group_messages
    """)
]
