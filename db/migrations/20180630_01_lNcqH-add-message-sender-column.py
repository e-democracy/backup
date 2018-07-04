"""
add message from_address column
"""

from yoyo import step

__depends__ = {'20180224_01_HdXi1-create-group-messages'}

steps = [
    step("""
        ALTER TABLE group_messages
            ADD COLUMN from_address TEXT
    """),
    step("""
        CREATE INDEX IF NOT EXISTS group_message_from_address
            ON group_messages (from_address)
    """, """
        DROP INDEX IF EXISTS group_message_from_address
    """)
]
