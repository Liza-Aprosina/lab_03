import json
import unittest
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory

from catalog import BadFile, BadItem, BadVersion, Book, Catalog, CatalogError, NotFound, SameId


def kniga(id="b1", name="Капитанская дочка", cat="Повесть"):
    return Book(id, name, cat, 1836, "А. С. Пушкин", 192)


class TestCatalog(unittest.TestCase):
    def setUp(self):
        self.cat = Catalog()
        self.a = kniga()
        self.b = kniga("b2", "Дубровский", "Роман")
        self.c = kniga("b3", "Пиковая дама")

    def test_empty(self):
        self.assertEqual(len(self.cat), 0)
        self.assertEqual(list(self.cat), [])
        self.assertNotIn("b1", self.cat)
        self.assertEqual(self.cat.find_by_name(""), [])
        self.assertEqual(self.cat.find_by_category("Роман"), [])

    def test_add_get(self):
        self.cat.add(self.a)
        self.assertEqual(len(self.cat), 1)
        self.assertIn("b1", self.cat)
        self.assertEqual(self.cat.get("b1"), self.a)

    def test_bad_item(self):
        for item in (None, {}, "book", 12):
            with self.subTest(item=item):
                with self.assertRaises(BadItem):
                    self.cat.add(item)
        self.assertEqual(len(self.cat), 0)

    def test_same_id(self):
        self.cat.add(self.a)
        with self.assertRaises(SameId):
            self.cat.add(kniga("b1", "Другая книга"))
        self.assertEqual(list(self.cat), [self.a])

    def test_same_name(self):
        self.cat.add(self.a)
        self.cat.add(kniga("b2"))
        self.assertEqual(len(self.cat.find_by_name("дочка")), 2)

    def test_remove(self):
        self.cat.add(self.a)
        self.cat.add(self.b)
        self.assertEqual(self.cat.remove("b1"), self.a)
        self.assertNotIn("b1", self.cat)
        self.assertEqual(list(self.cat), [self.b])
        self.assertEqual(self.cat.find_by_category("Повесть"), [])
        self.assertEqual(self.cat.find_by_name("дочка"), [])
        with self.assertRaises(NotFound):
            self.cat.get("b1")

    def test_no_get(self):
        with self.assertRaises(NotFound):
            self.cat.get("нет")

    def test_no_remove(self):
        self.cat.add(self.a)
        with self.assertRaises(NotFound):
            self.cat.remove("нет")
        self.assertEqual(list(self.cat), [self.a])

    def test_category(self):
        self.cat.add(self.a)
        self.cat.add(self.b)
        self.cat.add(self.c)
        self.assertEqual(self.cat.find_by_category("Повесть"), [self.a, self.c])
        self.assertEqual(self.cat.find_by_category("Роман"), [self.b])
        self.assertEqual(self.cat.find_by_category("нет"), [])

    def test_name(self):
        self.cat.add(self.a)
        self.cat.add(self.b)
        for query in ("дочка", "ДОЧКА", "ДоЧкА"):
            with self.subTest(query=query):
                self.assertEqual(self.cat.find_by_name(query), [self.a])
        self.assertEqual(self.cat.find_by_name("нет"), [])
        self.assertEqual(self.cat.find_by_name(""), [self.a, self.b])

    def test_search_copy(self):
        self.cat.add(self.a)
        found = self.cat.find_by_category("Повесть")
        found.clear()
        found = self.cat.find_by_name("дочка")
        found.append(self.b)
        self.assertEqual(list(self.cat), [self.a])

    def test_order(self):
        self.cat.add(self.c)
        self.cat.add(self.a)
        self.cat.add(self.b)
        self.assertEqual(list(self.cat), [self.c, self.a, self.b])
        self.assertEqual(list(self.cat), [self.c, self.a, self.b])
        self.cat.remove("b1")
        self.cat.add(self.a)
        self.assertEqual(list(self.cat), [self.c, self.b, self.a])

    def test_errors(self):
        for err in (BadItem, SameId, NotFound, BadVersion, BadFile):
            self.assertTrue(issubclass(err, CatalogError))


class TestJson(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "books.json"
        self.cat = Catalog()
        self.a = kniga()
        self.cat.add(self.a)

    def write(self, data):
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def check_bad(self, data, err=BadFile):
        self.write(data)
        with self.assertRaises(err):
            self.cat.load(self.path)
        self.assertEqual(list(self.cat), [self.a])
        self.assertEqual(self.cat.get("b1"), self.a)

    def test_round_trip(self):
        b = Book("b2", "Мёртвые души", "Поэма", 1842, "Н. В. Гоголь", 352)
        self.cat.add(b)
        self.cat.save(self.path)
        with self.path.open(encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["format_version"], 1)
        self.assertEqual(data["items"], [asdict(self.a), asdict(b)])
        new = Catalog()
        new.load(self.path)
        self.assertEqual(list(new), [self.a, b])
        self.assertEqual(new.get("b2"), b)

    def test_empty(self):
        Catalog().save(self.path)
        self.cat.load(self.path)
        self.assertEqual(len(self.cat), 0)

    def test_load_replaces(self):
        b = kniga("b2", "Дубровский", "Роман")
        self.write({"format_version": 1, "items": [asdict(b)]})
        self.cat.load(self.path)
        self.assertEqual(list(self.cat), [b])
        self.assertNotIn("b1", self.cat)

    def test_bad_json(self):
        self.path.write_text('{"format_version": 1, "items": [', encoding="utf-8")
        with self.assertRaises(BadFile):
            self.cat.load(self.path)
        self.assertEqual(list(self.cat), [self.a])

    def test_bad_encoding(self):
        self.path.write_bytes(b"\xff\xfe")
        with self.assertRaises(BadFile):
            self.cat.load(self.path)
        self.assertEqual(list(self.cat), [self.a])

    def test_no_file(self):
        with self.assertRaises(BadFile):
            self.cat.load(self.path)
        self.assertEqual(list(self.cat), [self.a])

    def test_bad_save(self):
        with self.assertRaises(BadFile):
            self.cat.save(Path(self.tmp.name) / "no_dir" / "books.json")

    def test_version(self):
        self.check_bad({"format_version": 2, "items": []}, BadVersion)

    def test_bad_version(self):
        for ver in (True, 1.0, "1", None):
            with self.subTest(ver=ver):
                self.check_bad({"format_version": ver, "items": []})

    def test_bad_root(self):
        for data in ([], None, "text", {}, {"items": []}):
            with self.subTest(data=data):
                self.check_bad(data)

    def test_bad_items(self):
        for items in (None, {}, "books"):
            with self.subTest(items=items):
                self.check_bad({"format_version": 1, "items": items})
        self.check_bad({"format_version": 1})

    def test_bad_row(self):
        for row in (None, [], "book", {}):
            with self.subTest(row=row):
                self.check_bad({"format_version": 1, "items": [row]})

    def test_no_partial_load(self):
        good = asdict(kniga("b2"))
        bad = asdict(kniga("b3"))
        bad["pages"] = -1
        self.check_bad({"format_version": 1, "items": [good, bad]})
        self.assertNotIn("b2", self.cat)

    def test_same_id_in_file(self):
        row = asdict(kniga("b2"))
        self.check_bad({"format_version": 1, "items": [row, row]})

    def test_missing_field(self):
        row = asdict(kniga("b2"))
        del row["author"]
        self.check_bad({"format_version": 1, "items": [asdict(self.a), row]})

    def test_extra_field(self):
        row = asdict(kniga("b2"))
        row["extra"] = "???"
        self.check_bad({"format_version": 1, "items": [row]})


if __name__ == "__main__":
    unittest.main()
