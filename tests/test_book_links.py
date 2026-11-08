import unittest

from tools.check_links import problems


class BookLinks(unittest.TestCase):
    def test_links_exist_and_written_chapters_are_linked(self):
        self.assertEqual(problems(), [])


if __name__ == "__main__":
    unittest.main()
