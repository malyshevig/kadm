import json
import logging


from util.db.dbutil import DbUtil

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s")

class FileDb (DbUtil):

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


    def check_if_exists(self, file_id) -> bool:
        q = "select id, name from file "
        q += "where id = %s"
        r = self.execute_query_select_dict(q, (file_id,))
        return r is not None and len(r) > 0

    def update_isbn_processed (self, file_id:str, isbn_status:str):
        q= f"update file set process_isbn=%s where id=%s"
        self.execute_query_update(q, (isbn_status, file_id))

    def get_file_by_id(self, file_id):
        q = "select id, name, file_path from file where id = %s"

        return self.execute_query_select_dict(q, (file_id,))

    def get_user_settings(self, user_id):
        q = "select settings from user_settings where user_id = %s"
        return self.execute_query_select_dict(q, (user_id,))

    def save_user_settings(self, user_id, settings):
        settings_str = json.dumps(settings)

        q  = "insert into user_settings (user_id,settings) values (%s, %s) \n"
        q += "on conflict(user_id) do update set settings=%s"

        self.execute_query_update(q, (user_id, settings_str, settings_str))

        return self.get_user_settings(user_id)

