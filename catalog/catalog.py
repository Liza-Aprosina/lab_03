import json
from dataclasses import asdict

from .errors import BadFile, BadItem, BadVersion, NotFound, SameId
from .model import Book


class Catalog:
    def __init__(self):
        self._data = {}

    def add(self, item):
        if not isinstance(item, Book):
            raise BadItem("нужен объект Book")
        if item.id in self._data:
            raise SameId("такой id уже есть: " + item.id)
        self._data[item.id] = item

    def get(self, item_id):
        if item_id not in self._data:
            raise NotFound("нет объекта: " + str(item_id))
        return self._data[item_id]

    def remove(self, item_id):
        item = self.get(item_id)
        del self._data[item_id]
        return item

    def find_by_category(self, category):
        res = []
        for item in self._data.values():
            if item.category == category:
                res.append(item)
        return res

    def find_by_name(self, query):
        query = query.lower()
        res = []
        for item in self._data.values():
            if query in item.name.lower():
                res.append(item)
        return res

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        # идем в порядке добавления
        return iter(self._data.values())

    def __contains__(self, item_id):
        return item_id in self._data

    def save(self, path):
        items = []
        for item in self._data.values():
            items.append(asdict(item))
        data = {"format_version": 1, "items": items}
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write("\n")
        except (OSError, UnicodeError) as err:
            raise BadFile("не получилось сохранить файл") from err

    def load(self, path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError, UnicodeError, RecursionError) as err:
            raise BadFile("не получилось прочитать JSON") from err

        if not isinstance(data, dict) or "format_version" not in data:
            raise BadFile("нет версии формата")
        ver = data["format_version"]
        if type(ver) is not int:
            raise BadFile("версия должна быть целым числом")
        if ver != 1:
            raise BadVersion("неизвестная версия: " + str(ver))
        if "items" not in data or not isinstance(data["items"], list):
            raise BadFile("нет списка items")

        # сначала проверяем весь файл
        new = Catalog()
        try:
            for row in data["items"]:
                if not isinstance(row, dict):
                    raise BadFile("в items должен быть объект")
                new.add(Book(**row))
        except (TypeError, BadItem, SameId) as err:
            raise BadFile("неверный объект в файле: " + str(err)) from err

        self._data = new._data
