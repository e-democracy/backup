"""
create_group_members
"""

from yoyo import step

__depends__ = {}

steps = [
    step("""
        CREATE TABLE IF NOT EXISTS
        group_members
        (group_id TEXT PRIMARY KEY ASC, member_ids JSON)
    """, """
        DROP TABLE group_members
    """)
]
