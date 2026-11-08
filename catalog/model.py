from dataclasses import dataclass

from .errors import BadItem


@dataclass(frozen=True)
class Book:
    id: str
    name: str
    category: str
    year: int
    author: str
    pages: int

    def __post_init__(self):
        for s in (self.id, self.name, self.category, self.author):
            if not isinstance(s, str) or not s.strip():
                raise BadItem("id, название, категория и автор нужны непустыми строками")
        if type(self.year) is not int or not 1 <= self.year <= 9999:
            raise BadItem("год должен быть целым числом от 1 до 9999")
        if type(self.pages) is not int or self.pages <= 0:
            raise BadItem("число страниц должно быть целым и положительным")
