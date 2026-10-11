import asyncio
import logging


from telethon import TelegramClient
from telethon.tl import types


from books_utill.DialogDb import DialogDb

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s")

api_id = 29093757
api_hash = "0d64c0d51b514dd14b4efad572cbb5db"
download_dir = "d:/books/download"


class TgScanner:
    def __init__(self, client:TelegramClient):
        self.client = client
        self.db = DialogDb()
       # self.processor = BookProcessor()

    def to_download(self, name:str)-> bool:
        if name is None:
            return False

        name = name.lower()
        return  name.endswith("pdf") or name.endswith("epub") or name.endswith("fb2")


    async def __call__(self):
        logger.info("Scan started")
        await self.scan()


    def get_files(self, doc:types.Document)-> list:
         if  hasattr(doc, "attributes"):
             files = [ f.file_name for f in doc.attributes if isinstance(f, types.DocumentAttributeFilename)]
             return files

         return []

    async def scan_dialog(self, d):
        logger.info(f"scanning dialog {d}")
        channel_id, name = None, None

        if isinstance(d, types.Dialog):
            channel_id = d.dialog.peer.channel_id
            name = d.name
        else:
            channel_id = d.id
            name = d.title

        r = self.db.create_dialog_if_not_exists(channel_id,name)
        offset = r["msg_offset"]

        msgs = await self.client.get_messages(d, reverse=True, filter=types.InputMessagesFilterDocument,
                                              offset_id=offset, limit=1000)
        for m in msgs:
            msg: types.Message = m
            offset_id = msg.id

            if m.file is not None and self.to_download(msg.file.name):
                file_id = msg.file.id
                file_name = msg.file.name
                file_mime_type = self.get_file_type(msg.media)
                file_desc = msg.message

                logger.info(f"Received msg: id={msg.id} offset_id= {offset_id} text={msg.message} "+
                            f"file_name={file_mime_type} "+
                            f"file_id={file_id} file_name={file_name}")

                if self.db.check_if_exists(file_id):
                    logger.info(f"File with id {file_id} exists received nane = {file_name}")
                else:
                    logger.info("Downloading")
                    file_path = await self.client.download_media(msg, download_dir)
                    self.db.create_file(file_id, file_name, file_path, file_desc)
                    # self.processor.process(file_id, file_name, file_path)

            if offset < offset_id:
                self.db.update_dialog_offset(channel_id, offset_id)
            await asyncio.sleep(5)


    def get_file_type(self, media) -> str:
        """Определить тип файла"""
        if hasattr(media, 'document'):
            # Проверяем подтипы документа
            mime_type = media.document.mime_type or ''

            if 'image' in mime_type:
                return 'image'
            elif 'video' in mime_type:
                return 'video'
            elif 'audio' in mime_type:
                return 'audio'
            elif 'pdf' in mime_type:
                return 'pdf'
            elif 'zip' in mime_type or 'rar' in mime_type or '7z' in mime_type:
                return 'archive'
            else:
                return 'document'

        elif hasattr(media, 'photo'):
            return 'photo'

        elif hasattr(media, 'video'):
            return 'video'

        elif hasattr(media, 'audio'):
            return 'audio'

        elif hasattr(media, 'voice'):
            return 'voice'

        elif hasattr(media, 'sticker'):
            return 'sticker'

        return 'unknown'

    async def get_folder_id(self, folder_name):
        await self.client.get


    async def get_channels(self, folder_names: set):
        res = await self.client(types.GetDialogFiltersRequest())
        folders = res.filters
        if folders is None:
            return []

        flds = [f for f in folders if isinstance(f, types.DialogFilter) and f.title.text in folder_names]
        channels = []
        for f in flds:
            channels.extend(
                [await self.client.get_entity(peer) for peer in f.include_peers if isinstance(peer, types.InputPeerChannel)])

        return channels

    async def scan(self):
        channels = await self.get_channels("Books")

        #dlgs:list[Dialog] = [d for d in await self.client.get_dialogs() if d.is_channel]
        dlgs = channels

        for d in dlgs:
            await self.scan_dialog(d)
            await asyncio.sleep(2)


async def main ():
    client = TelegramClient("im", api_id, api_hash)
    scanner = TgScanner(client)

    async with client:
        await scanner()


if __name__ == "__main__":
    asyncio.run(main())