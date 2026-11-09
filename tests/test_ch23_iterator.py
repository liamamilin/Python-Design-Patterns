import unittest
from itertools import islice

from examples import ch23_iterator as it
from examples import ch23_pythonic as py
from examples import ch23_photos_v1 as v1


def is_chengdu(photo):
    return photo["place"] == "成都"


class ListFirstTest(unittest.TestCase):
    def test_fetches_every_page_even_for_the_first_match(self):
        api = v1.FakePhotoApi()
        first = next(p for p in v1.all_photos(api) if is_chengdu(p))
        self.assertEqual(first["id"], 1)
        self.assertEqual(api.requests, 11)  # 10 页数据，加 1 次空页


class IteratorClassTest(unittest.TestCase):
    def test_fetches_only_what_is_needed(self):
        api = v1.FakePhotoApi()
        self.assertEqual(next(p for p in it.PhotoIterator(api) if is_chengdu(p))["id"], 1)
        self.assertEqual(api.requests, 1)

    def test_full_iteration_gives_everything_once(self):
        api = v1.FakePhotoApi()
        ids = [p["id"] for p in it.PhotoIterator(api)]
        self.assertEqual(ids, list(range(200)))
        self.assertEqual(api.requests, 11)

    def test_stop_iteration_is_sticky(self):
        api = v1.FakePhotoApi(total=3)
        iterator = it.PhotoIterator(api)
        self.assertEqual(len(list(iterator)), 3)
        self.assertEqual(list(iterator), [])
        self.assertEqual(api.requests, 2)  # 结束之后不再发请求


class GeneratorTest(unittest.TestCase):
    def test_same_items_as_the_class(self):
        self.assertEqual(list(py.iter_photos(v1.FakePhotoApi())), list(it.PhotoIterator(v1.FakePhotoApi())))

    def test_islice_takes_just_enough_pages(self):
        api = v1.FakePhotoApi()
        self.assertEqual(len(list(islice(py.iter_photos(api), 25))), 25)
        self.assertEqual(api.requests, 2)

    def test_an_iterator_is_used_up(self):
        photos = py.iter_photos(v1.FakePhotoApi(total=5))
        self.assertEqual(len(list(photos)), 5)
        self.assertEqual(list(photos), [])

    def test_an_iterable_can_be_looped_again(self):
        album = py.Album(v1.FakePhotoApi(total=5))
        self.assertEqual(len(list(album)), 5)
        self.assertEqual(len(list(album)), 5)

    def test_streaming_count(self):
        api = v1.FakePhotoApi()
        counts = py.places_by_year(api, 2024)
        self.assertEqual(sum(counts.values()), 40)
        self.assertEqual(api.requests, 11)


if __name__ == "__main__":
    unittest.main()
