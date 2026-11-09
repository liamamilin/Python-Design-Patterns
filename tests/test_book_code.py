import unittest

from tools.check_book_code import problems


class BookCodeMatchesExamples(unittest.TestCase):
    def test_every_python_block_is_taken_from_an_example_file(self):
        self.assertEqual(problems(), [])


if __name__ == "__main__":
    unittest.main()
