import os
import unittest
from core.config import DATABASE_PATH


class TestDatabase(unittest.TestCase):
    def test_database_path_is_absolute(self):
        # Unless it's :memory:, the path should be absolute
        if DATABASE_PATH != ":memory:":
            self.assertTrue(
                os.path.isabs(DATABASE_PATH),
                f"Path should be absolute: {DATABASE_PATH}",
            )

    def test_init_db_creates_tables(self):
        from unittest.mock import patch

        # Use a temporary test database with an absolute path
        test_db = os.path.abspath("test_creation.db")
        if os.path.exists(test_db):
            os.remove(test_db)

        # Patch the DATABASE_PATH in core.database and core.config
        with (
            patch("core.database.DATABASE_PATH", test_db),
            patch("core.config.DATABASE_PATH", test_db),
        ):
            from core import database

            try:
                database.init_db()
                conn = database.db_connect()
                cur = conn.cursor()
                cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
                )
                self.assertIsNotNone(cur.fetchone())
                conn.close()
            finally:
                if os.path.exists(test_db):
                    os.remove(test_db)


if __name__ == "__main__":
    unittest.main()
