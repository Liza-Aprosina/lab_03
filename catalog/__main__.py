from .catalog import Catalog
from .errors import SameId
from .model import Book


def main():
    cat = Catalog()
    cat.add(Book("b1", "Капитанская дочка", "Повесть", 1836, "А. С. Пушкин", 192))
    cat.add(Book("b2", "Дубровский", "Роман", 1841, "А. С. Пушкин", 224))
    cat.add(Book("b3", "Мёртвые души", "Поэма", 1842, "Н. В. Гоголь", 352))

    print("Книг:", len(cat))
    print("Книга b1:", cat.get("b1"))
    print("Есть b2:", "b2" in cat)
    print("По названию:", cat.find_by_name("ДОЧКА"))
    print("По категории:", cat.find_by_category("Роман"))

    try:
        cat.add(Book("b1", "Другая книга", "Роман", 2000, "Автор", 100))
    except SameId as err:
        print("Ошибка:", err)

    cat.save("out.json")
    new = Catalog()
    new.load("out.json")
    print("После загрузки:")
    for book in new:
        print(book.name)

    new.remove("b2")
    print("После удаления:", len(new))


if __name__ == "__main__":
    main()
