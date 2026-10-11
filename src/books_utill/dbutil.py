import logging
from typing import Optional

import psycopg2
from psycopg2 import pool

host = "localhost"
port = 5432

user = "postgres"
password = "begemot"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s")

class Cursor:
    def __init__ (self, con_pool, query, values):
        self.pool = con_pool
        self.conn = None
        self.cur = None
        self.query = query
        self.values = values
        self.cols = []

    def __enter__(self):
        self.conn = self.pool.getconn()
        if self.conn is None:
            raise Exception("Cant get connection")

        self.cur = self.conn.cursor()
        self.cur.execute(self.query, self.values)
        self.cols = [desc[0] for desc in self.cur.description]
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            if self.conn is not None:
                self.conn.commit()
        else:
            if self.conn is not None:
                self.conn.rollback()
            logger.exception(exc_type)

        if self.cur is not None:
            self.cur.close()
        logger.info ("Close connection")
        self.pool.putconn(self.conn)


    def fetch (self)-> Optional[dict]:
        try:
            row = self.cur.fetchone()
            if row is None:
                return None
            return dict(zip(self.cols, row))
        except Exception as _:
            return None

    def execute(self,query, values):
        cur = self.conn.cursor()
        cur.execute(query, values)


class DbUtil:
    def __init__(self, dbname:str):
        self.dbname = dbname

        self. pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,  # Минимальное количество соединений
            maxconn=5,   # Максимальное количество соединений
            host = host, port = port, dbname=self.dbname, user = user, password=password
            )

    def __del__(self):
        if self.pool:
            self.pool.closeall()

    def get_connections_info(self):
        pool = self.pool
        return pool.maxconn


    def query_template(self, callback):
        cur = None

        with self.pool.getconn() as conn:
            #logging.info(f"get connection {conn} {th.current_thread()}")
            if not conn:
                raise Exception("Cant get connection")

            try:
                cur = conn.cursor()
                r = callback(conn, cur)

                return r
            except Exception as e:
                logging.exception(e)
                raise e
            finally:
                if cur:
                    cur.close()
                #logging.info(f"put connection {conn} {th.current_thread()}")
                self.pool.putconn(conn)

    def execute_query_update(self, query, values) -> int:

        logging.debug(f"Execute query update: {query}")
        def call (conn, cur):
            cur.execute(query,values)
            c = cur.rowcount
            conn.commit()
            return c

        return self.query_template (call)

    def execute_query_select (self, query, vals, limit=1):

        logging.debug(f"Execute query select: {query}")
        def call (_, cur):
            cur.execute(query, vals)
            data = cur.fetchall ()
            return data[:limit] if limit else data

        return self.query_template(call)

    def execute_query_update_and_select(self, query, values, limit=1):

        logging.debug(f"Execute query select: {query}")

        def call(con, cur):
            cur.execute(query,values)
            cols = [desc[0] for desc in cur.description]
            data = cur.fetchall()
            if con:
                con.commit()
            data = data[:limit] if limit else data
            return [dict(zip(cols, row)) for row in data]

        return self.query_template(call)

    def execute_query_select_dict (self, query, vals, limit=1):
        logging.debug(f"Execute query select: {query}")
        def call (_, cur):
            cur.execute(query, vals)
            cols = [desc[0] for desc in cur.description]
            data = cur.fetchall ()

            result = [dict(zip(cols, row)) for row in data]
            return result[:limit] if limit else result

        return self.query_template(call)


    def execute_query_for_update(self, query, values, q_update, callback ):
        logging.debug(f"Execute query select: {query}")

        def call(con, cur):
            cur.execute(query, values)
            cols = [desc[0] for desc in cur.description]
            data = cur.fetchall()
            data_dict = [dict(zip(cols, row)) for row in data]
            res = callback (data_dict)

            id = data[0][0]
            cur.execute (q_update, (id,))
            if con:
                con.commit()
            return res

        return self.query_template(call)


    def open_cursor_for_update (self, query, values)-> Cursor:
        return Cursor(self.pool,query,values)