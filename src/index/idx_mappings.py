# opensearch

settings = {
    "settings": {
        "index": {
            "number_of_shards": 1,
            "number_of_replicas": 1,
            "refresh_interval": "1s"
        },
        "analysis": {
            "analyzer": {
                "russian": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "russian_stop", "russian_stemmer"]
                }
            },
            "filter": {
                "russian_stop": {
                    "type": "stop",
                    "stopwords": "_russian_"
                },
                "russian_stemmer": {
                    "type": "stemmer",
                    "language": "russian"
                }
            }
        }
    }
}

isbn_mappings = {
    "mappings": {
        "properties": {
            "title": {
                "type": "text",
                "analyzer": "russian",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "file_name": {
                "type": "text",
                "analyzer": "russian",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "description":{
                "type": "text",
                "analyzer": "russian",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "file_path": {"type": "keyword"},
            "authors": {
                "type": "keyword",
                "fields": {
                    "text": {
                        "type": "text",
                        "analyzer": "russian"
                    }
                }
            },
            "publisher": {"type": "keyword"},
            "language": {"type": "keyword"},
            "year": {"type": "integer"},  # integer вместо short
            "file_uuid": {"type": "keyword"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"}
        }
    }
}

kw_mappings = {
    "mappings": {
        "properties": {
            "file_name": {
                "type": "text",
                "analyzer": "russian",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "description": {
                "type": "text",
                "analyzer": "russian",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },
            "file_path": {"type": "keyword"},
            "kw": {
                "type": "keyword",
                "fields": {
                    "text": {
                        "type": "text",
                        "analyzer": "russian"
                    }
                }
            },
            "file_id": {"type": "keyword", "index": False},
        }
    }
}


text_mappings = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "properties": {
            "text_content": {
                "type": "text",
                "analyzer": "russian",
                "index_options": "positions",  # Для phrase search
                "term_vector": "with_positions_offsets",  # Для highlighting
                "fielddata": True,  # Для агрегаций по тексту
                "fields": {
                    "exact": {
                        "type": "keyword",  # Для точного поиска фраз
                        "ignore_above": 256
                    },
                    "simple": {
                        "type": "text",
                        "analyzer": "simple"  # Для базового поиска
                    }
                }
            },
            "file_id": {"type": "text", "index": False},
            "page_num": {"type": "integer", "index": False},
            "file_name": {"type": "keyword"},
        }
    }

}

author_mappings = {
    "mappings": {
            "properties": {
                "name": {
                    "type": "keyword",
                    "fields": {
                            "search": {
                                "type": "text",
                                "analyzer": "russian"
                            }
                    }
                }
            }
        }
}


publisher_mappings = {
    "mappings": {
            "properties": {
                "name": {
                    "type": "keyword",
                    "fields": {
                            "search": {
                                "type": "text",
                                "analyzer": "russian"
                            }
                    }
                }
            }
        }
}

mappings = {
    "isbn": isbn_mappings,
    "kw": kw_mappings,
    "text": text_mappings
}
