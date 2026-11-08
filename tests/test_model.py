import unittest
from dataclasses import FrozenInstanceError, is_dataclass

from catalog import BadItem, Book


def dannye():
    return {
        "id": "b1",
        "name": "Капитанская дочка",
        "category": "Повесть",
        "year": 1836,
        "author": "А. С. Пушкин",
        "pages": 192,
    }


class TestBook(unittest.TestCase):
    def test_ok(self):
        book = Book(**dannye())
        self.assertTrue(is_dataclass(book))
        self.assertEqual(book.id, "b1")
        self.assertEqual(book.name, "Капитанская дочка")
        self.assertEqual(book.category, "Повесть")
        self.assertEqual(book.year, 1836)
        self.assertEqual(book.author, "А. С. Пушкин")
        self.assertEqual(book.pages, 192)

    def test_bad_text(self):
        for field in ("id", "name", "category", "author"):
            for value in ("", "  \n", None, 123, [], True):
                with self.subTest(field=field, value=value):
                    data = dannye()
                    data[field] = value
                    with self.assertRaises(BadItem):
                        Book(**data)

    def test_bad_year(self):
        for year in (0, -1, 10000, "2000", 2000.0, None, True):
            with self.subTest(year=year):
                data = dannye()
                data["year"] = year
                with self.assertRaises(BadItem):
                    Book(**data)

    def test_bad_pages(self):
        for pages in (0, -1, "100", 100.5, None, True):
            with self.subTest(pages=pages):
                data = dannye()
                data["pages"] = pages
                with self.assertRaises(BadItem):
                    Book(**data)

    def test_year_limits(self):
        for year in (1, 9999):
            data = dannye()
            data["year"] = year
            self.assertEqual(Book(**data).year, year)

    def test_no_change(self):
        book = Book(**dannye())
        for field, value in (("id", "b2"), ("pages", -1), ("category", "Роман")):
            with self.subTest(field=field):
                with self.assertRaises(FrozenInstanceError):
                    setattr(book, field, value)


if __name__ == "__main__":
    unittest.main()
