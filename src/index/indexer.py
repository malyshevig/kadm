import numpy as np

np.float_ = np.float64

from typing import List, Dict, Any
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s")

os_server = "gek"

class BookIndexer:
    def __init__(self, host: str = 'localhost', port: int = 9200,
                 auth: tuple = None, use_ssl: bool = False):
        """
        Инициализация клиента OpenSearch

        Args:
            host: Хост OpenSearch
            port: Порт OpenSearch
            auth: Кортеж (username, password) для аутентификации
            use_ssl: Использовать SSL
        """
        # Basic connection
        self.client = OpenSearch(
            hosts=[{'host': os_server, 'port': 9200}],
            http_compress=True,  # enables gzip compression for request bodies
            use_ssl=False,
            verify_certs=False,
            ssl_show_warn=False
        )
        # Проверка подключения
        try:
            info = self.client.info()
            logger.info(f"Подключено к OpenSearch: {info['version']['distribution']} {info['version']['number']}")
        except Exception as e:
            logger.error(f"Ошибка подключения к OpenSearch: {e}")
            raise

    def create_text_index(self, index_name: str):
        from idx_mappings import text_mappings, settings

        body = {**settings, **text_mappings}
        try:
            # Удаляем индекс если существует
            if self.client.indices.exists(index=index_name):
                logger.warning(f"Индекс {index_name} уже существует. Удаляем...")
                self.client.indices.delete(index=index_name)

            # Создаем новый индекс
            response = self.client.indices.create(
                index=index_name,
                body=body
            )
            logger.info(f"Индекс {index_name} успешно создан")
            return response.get('acknowledged', False)
        except Exception as e:
            logger.error(f"Ошибка создания индекса: {e}")
            return False


    def create_index(self, index_name: str, settings: Dict = None) -> bool:
        """
        Создание индекса

        Args:
            index_name: Название индекса
            settings: Настройки индекса
            mappings: Маппинги полей

        Returns:
            bool: Успешно ли создан индекс
        """
        # Настройки по умолчанию

        # Маппинги по умолчанию
        from idx_mappings import isbn_mappings, settings, mappings

        doc_mappings = mappings[index_name]


        # Объединяем настройки и маппинги
        body = {**settings, **doc_mappings}

        try:
            # Удаляем индекс если существует
            if self.client.indices.exists(index=index_name):
                logger.warning(f"Индекс {index_name} уже существует. Удаляем...")
                self.client.indices.delete(index=index_name)

            # Создаем новый индекс
            response = self.client.indices.create(
                index=index_name,
                body=body
            )
            logger.info(f"Индекс {index_name} успешно создан")
            return response.get('acknowledged', False)
        except Exception as e:
            logger.error(f"Ошибка создания индекса: {e}")
            return False

    def index_document(self, index_name: str, document: Dict,
                       document_id: str = None) -> bool:
        """
        Индексация одного документа

        Args:
            index_name: Название индекса
            document: Документ для индексации
            document_id: ID документа (если None - сгенерируется автоматически)

        Returns:
            bool: Успешно ли проиндексирован документ
        """
        try:
            # Добавляем временные метки если их нет
            if 'created_at' not in document:
                document['created_at'] = datetime.utcnow().isoformat()
            if 'updated_at' not in document:
                document['updated_at'] = datetime.utcnow().isoformat()

            response = self.client.index(
                index=index_name,
                body=document,
                id=document_id,
                refresh=True
            )

            if response['result'] in ['created', 'updated']:
                logger.info(f"Документ {response['_id']} успешно проиндексирован")
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка индексации документа: {e}")
            return False

    def bulk_index(self, index_name: str, documents: List[Dict],
                   id_field: str = None) -> bool:
        """
        Массовая индексация документов

        Args:
            index_name: Название индекса
            documents: Список документов
            id_field: Поле для использования в качестве ID

        Returns:
            bool: Успешно ли проиндексированы документы
        """
        actions = []

        for doc in documents:
            action = {
                "_index": index_name,
                "_source": doc
            }

            # Добавляем временные метки если их нет
            if 'created_at' not in doc:
                doc['created_at'] = datetime.utcnow().isoformat()
            if 'updated_at' not in doc:
                doc['updated_at'] = datetime.utcnow().isoformat()

            # Устанавливаем ID если указано поле
            if id_field and id_field in doc:
                action["_id"] = doc[id_field]

            actions.append(action)

        try:
            success, failed = bulk(
                self.client,
                actions,
                refresh=True,
                raise_on_error=False
            )

            logger.info(f"Массовая индексация: {success} успешно, {len(failed)} с ошибками")

            if failed:
                for fail in failed:
                    logger.error(f"Ошибка индексации: {fail}")

            return len(failed) == 0
        except Exception as e:
            logger.error(f"Ошибка массовой индексации: {e}")
            return False

    def search(self, index_name: str, query: str,
               fields: List[str] = None, size: int = 10,
               filters: Dict = None) -> Dict:
        """
        Поиск документов

        Args:
            index_name: Название индекса
            query: Поисковый запрос
            fields: Поля для поиска (если None - все текстовые поля)
            size: Количество результатов
            filters: Фильтры для поиска

        Returns:
            Dict: Результаты поиска
        """
        if fields is None:
            fields = ['title^2', 'content']  # title имеет больший вес

        # Базовый поисковый запрос
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": fields,
                                "type": "best_fields",
                                "fuzziness": "AUTO"
                            }
                        }
                    ]
                }
            },
            "highlight": {
                "fields": {
                    "*": {}
                },
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"]
            },
            "size": size,
            "_source": ["title", "content", "url", "category", "created_at"]
        }

        # Добавляем фильтры если есть
        if filters:
            filter_conditions = []
            for field, value in filters.items():
                if isinstance(value, list):
                    filter_conditions.append({"terms": {field: value}})
                else:
                    filter_conditions.append({"term": {field: value}})

            search_body["query"]["bool"]["filter"] = filter_conditions

        try:
            response = self.client.search(
                index=index_name,
                body=search_body
            )

            return self._format_search_results(response)
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return {"hits": [], "total": 0, "took": 0}

    def _format_search_results(self, response: Dict) -> Dict:
        """
        Форматирование результатов поиска

        Args:
            response: Ответ от OpenSearch

        Returns:
            Dict: Отформатированные результаты
        """
        hits = []

        for hit in response['hits']['hits']:
            formatted_hit = {
                'id': hit['_id'],
                'score': hit['_score'],
                'source': hit['_source'],
                'highlight': hit.get('highlight', {})
            }
            hits.append(formatted_hit)

        return {
            'hits': hits,
            'total': response['hits']['total']['value'],
            'took': response['took'],
            'timed_out': response['timed_out']
        }

    def delete_document(self, index_name: str, document_id: str) -> bool:
        """
        Удаление документа

        Args:
            index_name: Название индекса
            document_id: ID документа

        Returns:
            bool: Успешно ли удален документ
        """
        try:
            response = self.client.delete(
                index=index_name,
                id=document_id,
                refresh=True
            )

            if response['result'] == 'deleted':
                logger.info(f"Документ {document_id} успешно удален")
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка удаления документа: {e}")
            return False

    def get_index_stats(self, index_name: str) -> Dict:
        """
        Получение статистики индекса

        Args:
            index_name: Название индекса

        Returns:
            Dict: Статистика индекса
        """
        try:
            stats = self.client.indices.stats(index=index_name)
            return {
                'doc_count': stats['indices'][index_name]['total']['docs']['count'],
                'size': stats['indices'][index_name]['total']['store']['size_in_bytes'],
                'shards': stats['indices'][index_name]['shards']
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}



def main():
    indexer = BookIndexer(
        host='localhost',
        port=9200,
        auth=('admin', 'admin'),  # если требуется аутентификация
        use_ssl=False
    )
    indexer.create_index("isbn")

    print("\n\nСтатистика индекса:")
    indexer.client.indices.get("*")


"""
# Пример использования
def main():
    # Инициализация индексатора
    indexer = SimpleOpenSearchIndexer(
        host='localhost',
        port=9200,
        auth=('admin', 'admin'),  # если требуется аутентификация
        use_ssl=False
    )

    # Создание индекса
    INDEX_NAME = "documents"
    indexer.create_index(INDEX_NAME)

    # Пример документов для индексации
    documents = [
        {
            "title": "Введение в Python",
            "content": "Python - это язык программирования высокого уровня...",
            "url": "https://example.com/python-intro",
            "category": "programming",
            "tags": ["python", "programming", "tutorial"],
            "metadata": {"author": "John Doe", "level": "beginner"}
        },
        {
            "title": "Машинное обучение на Python",
            "content": "Scikit-learn - популярная библиотека для машинного обучения...",
            "url": "https://example.com/ml-python",
            "category": "machine-learning",
            "tags": ["python", "machine-learning", "scikit-learn"],
            "metadata": {"author": "Jane Smith", "level": "advanced"}
        },
        {
            "title": "Web разработка на Django",
            "content": "Django - это мощный фреймворк для веб-разработки на Python...",
            "url": "https://example.com/django-web",
            "category": "web-development",
            "tags": ["python", "django", "web"],
            "metadata": {"author": "Bob Johnson", "level": "intermediate"}
        }
    ]

    # Индексация документов
    print("Индексация документов...")
    indexer.bulk_index(INDEX_NAME, documents, id_field="url")

    # Поиск документов
    print("\nПоиск по запросу 'Python программирование':")
    results = indexer.search(INDEX_NAME, "Python программирование")

    print(f"Найдено документов: {results['total']}")
    print(f"Время выполнения: {results['took']} мс")

    for i, hit in enumerate(results['hits'], 1):
        print(f"\n{i}. {hit['source']['title']} (релевантность: {hit['score']:.2f})")
        print(f"   Категория: {hit['source']['category']}")
        print(f"   URL: {hit['source']['url']}")

        # Показываем подсвеченные фрагменты
        if hit.get('highlight'):
            for field, snippets in hit['highlight'].items():
                for snippet in snippets[:1]:  # только первый сниппет
                    print(f"   Фрагмент: {snippet}")

    # Поиск с фильтрацией
    print("\n\nПоиск с фильтром по категории 'programming':")
    results = indexer.search(
        INDEX_NAME,
        "Python",
        filters={"category": "programming"}
    )

    print(f"Найдено документов: {results['total']}")

    # Получение статистики
    print("\n\nСтатистика индекса:")
    stats = indexer.get_index_stats(INDEX_NAME)
    print(f"Количество документов: {stats.get('doc_count', 0)}")
    print(f"Размер индекса: {stats.get('size', 0) / 1024:.2f} KB")

"""

if __name__ == "__main__":
    main()