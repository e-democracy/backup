"""
create_member_profiles
"""

from yoyo import step

__depends__ = {}

steps = [
    step("""
        CREATE TABLE IF NOT EXISTS
        member_profiles
        (id TEXT PRIMARY KEY ASC, profile JSON)
    """, """
        DROP TABLE member_profiles
    """)
]
