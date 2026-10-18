from prefect import flow, task, get_run_logger
from prefect.results import ResultStorage

from books_utill import filedb
from books_utill.filedb import FileDb
from books_utill.models import File
from isbn.isbnutil import extract_isbns, ISBNExtractor

from books_utill.isbndb import IsbnDb

@task
def extract_isbn(file_uuid):
    file_manager = FileDb ()
    file: File|None = file_manager.get_file_by_uuid(file_uuid)
    if file:
        isbn_set = ISBNExtractor ().get_isbn_set(file.file_path)
        get_run_logger().info(isbn_set)
        IsbnDb().save_isbns(file_uuid, isbn_set)
        return isbn_set
    else:
        raise Exception (f"Can't open file {file_uuid}")

@task
def get_isbn_info(file_uuid):
    isbn_set = IsbnDb().get_by_file_uuid(file_uuid)
    for isbn in isbn_set:
        isbn_info= ISBNExtractor().get_book_info(isbn)
        IsbnDb.save_isbn_info (isbn_info)

    return isbn_set



@task
def index_file(file_uuid):
    pass

@task
def index_to_rag(file_uuid):
    return

from prefect import flow
from prefect.filesystems import LocalFileSystem

@flow(
    name="process_book",
    result_storage="local-file-system/books-storage",
    persist_result=True,
)
def process_book(file_uuid):
     extract_isbn(file_uuid)
     get_isbn_info(file_uuid)
     index_file (file_uuid)
     index_to_rag(file_uuid)




