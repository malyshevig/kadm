import logging

from books_utill.dbutil import DbUtil

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s")

class DialogDb (DbUtil):

    def __init__(self):
        super().__init__("books")

    def create_dialog_if_not_exists(self, channel_id, name, offset=0):
         q = "select channel_id, name, msg_offset from dialog "
         q+= "where channel_id = %s"
         r = self.execute_query_select_dict(q,(channel_id,) )

         if r is None or len(r) == 0:
            q = ("insert into dialog (channel_id, name , msg_offset) values (%s, %s, %s) "+
                 "returning channel_id, name, msg_offset")
            res = self.execute_query_update_and_select(q, (channel_id, name, offset))
            return res[0]
         else:
            return r[0]

    def update_dialog_offset(self, channel_id, offset):
        q = "update dialog set msg_offset = %s where channel_id = %s"
        self.execute_query_update(q, (offset,channel_id))

    def create_file(self, id, name, file_path, file_desc, src="tg"):
            q = " insert into file (id, name, file_path, description, src ) "
            q+= " values (%s, %s, %s,%s, %s)"
            q+="  returning id, name, file_path, description, src"

            self.execute_query_update_and_select(q, (id, name, file_path, file_desc, src,))
            return False, None

    def check_if_exists(self, id) -> bool:
        q = "select id, name from file "
        q += "where id = %s"
        r = self.execute_query_select_dict(q, (id,))
        return r is not None and len(r) > 0
