from util.db.dbutil import Cursor
from util.db.filedb import FileDb
from idx.indexer import BookIndexer
from src.tg.processor import BookProcessor


class TextProcessor:

    def __init__(self):
        self.db = FileDb()
        self.bp = BookProcessor()
        self.indexer = BookIndexer()
        self.indexer.create_text_index("pages")

    def process(self):
        q = f"select id,name, file_path from file where process_isbn is null for update skip locked limit 10"

        while True:
            row_count = 0
            with self.db.open_cursor_for_update(q, ()) as cursor:
                cur: Cursor = cursor
                while True:
                    file = cur.fetch()
                    if file is None:
                        break

                    row_count += 1
                    id: str = file["id"]
                    name: str = file["name"]
                    path: str = file["file_path"]

                    pages = [p for p in self.bp.pdf2text(path)]
                    docs = [
                        {
                            "id": f"{id}_{n + 1}",
                            "text_content": p,
                            "file_id": id,
                            "file_name": name,
                            "page_num": n+1
                        }

                        for n,p in enumerate(pages)
                    ]
                    self.indexer.bulk_index("pages", docs, "id")
            if row_count == 0:
                break

def main():
    p = TextProcessor()
    p.process()

if __name__ == "__main__":
    main()