# Установка: pip install isbntools
import logging

import re
import time
from typing import Optional

import PyPDF2
import isbnlib
from isbnlib import ISBNLibException


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s")



def clean_isbn_string(isbn_str: str) -> Optional[str]:
    """
    Очищает строку ISBN от нежелательных символов и нормализует формат.

    Args:
        isbn_str: Строка, содержащая возможный ISBN

    Returns:
        Очищенная строка ISBN или None, если не удалось извлечь валидный ISBN
    """
    if not isbn_str:
        return None

    # Приводим к верхнему регистру
    isbn_str = isbn_str.upper().strip()

    # Удаляем префикс "ISBN" и двоеточия
    isbn_str = re.sub(r'^ISBN[:\-]*\s*', '', isbn_str, flags=re.IGNORECASE)

    # Удаляем все символы, кроме цифр и X (последний символ может быть X)
    # Оставляем дефисы для последующей обработки
    clean_str = re.sub(r'[^\dX\-]', '', isbn_str)

    if not clean_str:
        return None

    # Удаляем дефисы и пробелы для стандартизации
    clean_str = clean_str.replace('-', '').replace(' ', '')

    # Проверяем длину - ISBN должен быть 10 или 13 цифр
    # (X считается как символ, но только в конце для ISBN-10)
    if len(clean_str) not in (10, 13):
        return None

    # Для ISBN-10: должен содержать только цифры или X в конце
    if len(clean_str) == 10:
        # Проверяем, что первые 9 символов - цифры
        if not clean_str[:-1].isdigit():
            return None
        # Проверяем, что последний символ - цифра или X
        if not (clean_str[-1].isdigit() or clean_str[-1] == 'X'):
            return None

    # Для ISBN-13: должен содержать только цифры
    elif len(clean_str) == 13:
        if not clean_str.isdigit():
            return None

    return clean_str


def normalize_isbn(isbn_str: str) -> Optional[str]:
    """
    Нормализует ISBN к стандартному формату с дефисами.

    Args:
        isbn_str: Очищенная строка ISBN

    Returns:
        ISBN в стандартном формате с дефисами
    """
    if not isbn_str or len(isbn_str) not in (10, 13):
        return None

    if len(isbn_str) == 10:
        # Формат ISBN-10: группа-издатель-номер-контрольная цифра
        # Точное расположение дефисов зависит от регистрации
        # Возвращаем без дефисов, так как размещение дефисов неоднозначно
        return isbn_str
    else:
        # ISBN-13: префикс (978/979)-группа-издатель-номер-контрольная цифра
        # Основные группы для книг: 978 или 979
        if isbn_str[:3] in ('978', '979'):
            # Форматируем как ISBN-13 с дефисами
            # EAN-13: 978-группа-издатель-номер-контрольная
            return f"{isbn_str[:3]}-{isbn_str[3:4] or ''}-{isbn_str[4:6] or ''}-{isbn_str[6:12]}-{isbn_str[12]}"

    return isbn_str


def is_valid_isbn(isbn_str: str) -> bool:
    """
    Проверяет валидность ISBN с помощью контрольной суммы.

    Args:
        isbn_str: Очищенная строка ISBN

    Returns:
        True если ISBN валиден, False в противном случае
    """
    if not isbn_str:
        return False

    cleaned = clean_isbn_string(isbn_str)
    if not cleaned:
        return False

    # Проверка контрольной суммы для ISBN-10
    if len(cleaned) == 10:
        total = 0
        for i, char in enumerate(cleaned):
            if i == 9 and char == 'X':
                total += 10
            elif char.isdigit():
                total += int(char) * (10 - i)
            else:
                return False

        return total % 11 == 0

    # Проверка контрольной суммы для ISBN-13
    elif len(cleaned) == 13:
        if not cleaned.isdigit():
            return False

        total = 0
        for i, char in enumerate(cleaned):
            digit = int(char)
            # Умножаем на 1 для нечётных позиций, на 3 для чётных (с 0 индекса)
            weight = 1 if i % 2 == 0 else 3
            total += digit * weight

        return total % 10 == 0

    return False


def normalize_dashes(text: str) -> str:
    """
    Заменяет различные тире и дефисы на обычный дефис.

    Args:
        text: Текст с различными типами тире

    Returns:
        Текст с нормализованными дефисами
    """
    # Заменяем длинные тире (en dash, em dash) на обычный дефис
    # en dash: U+2013, em dash: U+2014, figure dash: U+2012
    text = re.sub(r'[\u2012\u2013\u2014\u2015]', '-', text)
    return text


def extract_isbns(text: str) -> list:
    # Паттерны для ISBN-10 и ISBN-13
    isbn_patterns = [
        r'ISBN[\s-]*((?:[0-9][\s-]*){9,13}[0-9X])',
        r'ISBN[ \-]*(?:1[03])?[ \-]*[:]?[ \-]*([0-9\- Xx]{10,17})',
        r'\b(?:97[89][- ]?)?(?:\d[- ]?){9,12}[\dXx]\b',
        r'\b(?:ISBN[-:]?\s*)?(?:97[89][- ]?){1}[0-9]{1,5}[- ]?[0-9]+[- ]?[0-9]+[- ]?[0-9Xx]\b',
        r'ISBN[\-\s]*(?:1[03])?[\-\s]*[:]?[\-\s]*',
        r'((?:97[89][\-\s]?)?5[\-\s]?\d[\-\s]?\d[\-\s]?\d[\-\s]?\d[\-\s]?\d[\-\s]?\d[\-\s]?\d[\-\s]?\d[\-\s]?[\dX])'

    ]
    text = normalize_dashes(text)

    found_isbns = []
    for pattern in isbn_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # Очистка и валидация ISBN
            clean_isbn = clean_isbn_string(match)
            if is_valid_isbn(clean_isbn):
                found_isbns.append(clean_isbn)

    return found_isbns


class ISBNExtractor:
    def __init__(self):
        pass


    def pdf2text(self, f):
        with open(f, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text = page.extract_text()
                yield text

    def get_isbn_set (self, f):
        try:
            pages = [p for p in self.pdf2text(f)]
            isbn_set = set()
            for p in pages[:20]:
                isbn_list = extract_isbns(p)
                isbn_set.update(isbn_list)

            return isbn_set
        except Exception as e:
            logger.exception(f"Can not get isdn set {e}")
            return set()

    def get_meta(self, isbn):
        book = None
        errors = []

        for srv in ["openl", "wiki", "goob"]:
           try:
               book = isbnlib.meta(isbn, srv)
               return book
           except Exception as e:
               errors.append((srv, e))
        raise IsbnServiceException("Isbn to meta error", errors)


    #@retry(Exception, delay=10, tries=3)
    def _get_book_info(self, isbn):
        res = {}
        try:
            isbn = isbnlib.clean(isbn)

            if isbnlib.is_isbn10(isbn):
                isbn = isbnlib.to_isbn13(isbn)

            book = self.get_meta(isbn)
            for k,v in book.items():
                res[k.lower()] =v

            return res

        except ISBNLibException as e:
            logger.exception(e)
            if str(e).find("429")>0:
                logger.error("Got Error 429, sleep for 3600 sec")
                time.sleep(3600)
            raise e

    def get_book_info(self, isbn):
        try:
            return self._get_book_info(isbn)
        except ISBNLibException as _:
            return {}