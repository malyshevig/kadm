from prefect import flow, task, get_run_logger

from books_utill import filedb
from books_utill.filedb import FileDb
from books_utill.models import File
from isbn.isbnutil import extract_isbns, ISBNExtractor


@task
def extract_isbn(file_uuid):
    file_manager = FileDb ()
    file: File = file_manager.get_file_by_uuid(file_uuid)
    if file:
        isbn_set = ISBNExtractor ().get_isbn_set(file.file_path)

    extract_isbns()
    return

@task
def get_isbn_info(file_uuid):
    return

@task
def index_file(file_uuid):
    return


@flow(name="process_book")
def process_book(file_uuid):
     extract_isbn(file_uuid)
     get_isbn_info(file_uuid)
     index_file (file_uuid)


