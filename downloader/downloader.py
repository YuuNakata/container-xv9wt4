import asyncio
import os
import pathlib
import re
import traceback
from time import time

from telethon.tl.types import DocumentAttributeFilename
from yt_dlp import YoutubeDL

from downloader import googledrive
from downloader.trackers import (down_mega, down_torrent,
                                 download_file_from_google_drive, download_url)
from downloader.utils import (check_files, get_dir_size, get_file_size,
                              progress, progress_yutu, sizeof_fmt, slugify)
from utils import youtube_info
from utils.FastTelethon import download_file, upload_file
from utils.func_utils import manage_tel_connects

pd_2 = "<b>🗄Archivo:</b>{0}\n\n<b>♻️Estado:</b>{1}"
pd = "<b>🗄Archivo:</b>{0}\n\n<b>♻️Estado:</b>{1}\n\n<b>💾Tamaño:</b>{2}"
pf = "<b>✅Archivo Subido con exito!✅</b>\n\n<b>🆙Subido por:</b> @{0}\n\n<b>User:</b> /pass\n<b>Password:</b> /pass\n\n🔗Link:{1}"


class Downloader:
    def __init__(self, file_id, bot, message, chat, chat_id, path, manage_button, data=None, auto=False, link=None, ev=None):
        self.file_id = file_id
        self.bot = bot
        self.chat = chat
        self.chat_id = chat_id
        self.message = message if not auto else bot.iter_messages(chat, ids=message)
        self.path = path
        self.manage_button = manage_button
        self.data = data
        self.link = link
        self.ev = ev
        pathdir = pathlib.Path(path)
        if not os.path.exists(pathdir):
            os.makedirs(pathdir)

    async def download_identifier(self, args=()):
        if not self.link:
            file_id = self.file_id
            message = self.message
            async for m in message:
                CLEANR = re.compile("<.*?>")
                link = re.sub(CLEANR, "", m.text)
                m = m
            if m.file:
                filename = m.media.document.attributes
                mime_type = m.media.document.mime_type
                for i in range(len(filename)):
                    if type(filename[i]) == DocumentAttributeFilename:
                        filename = filename[i].file_name
                    if len(filename) < 2:
                        ty_name = mime_type.split("/")
                        filename = ty_name[-2] + "_desconocido." + ty_name[-1]
                count = 1
                while os.path.exists(self.path + filename):
                    f, ext = os.path.splitext(filename)
                    f += str(count)
                    filename = f + ext
                    count += 1
                size = int(m.media.document.size)
                d_message = pd_2.format(filename, "Descargando...📥")
                msg = await self.bot.send_message(self.chat_id, pd_2.format(filename, "Descarga(En cola)...📥"), reply_to=file_id, parse_mode="html")
                # await m.download_media(
                #     file=os.path.join(self.path, filename),
                #     progress_callback=lambda d, t: asyncio.get_event_loop().create_task(progress(d, t, msg, start, d_message)),

                async def down_make(start, start_summ):
                    return await download_file(
                        self.ev.client,
                        self.ev.document,
                        out,
                        lambda d, t: asyncio.get_event_loop().create_task(progress(d, t, msg, start, start_summ, d_message)),
                    )

                with open(os.path.join(self.path, filename), "wb") as out:
                    await manage_tel_connects(
                        down_make,
                        msg,
                        pd_2.format(filename, "Descarga(En cola){}📥 Posicion: {}"),
                    )
                await msg.edit(
                    pd.format(filename, "Descargado con Exito", sizeof_fmt(size)),
                    buttons=self.manage_button,
                )
        else:
            file_id = None
            link = self.link

        #####LINK####

        if "drive.google" in link:
            try:
                msg = await self.bot.send_message(
                    self.chat_id,
                    pd.format("-", "-", "-"),
                    parse_mode="html",
                    reply_to=self.file_id,
                )
                info = googledrive.get_info(link)
                name = slugify(info["file_name"])
                file_id = info["file_id"]
                file = await download_file_from_google_drive(
                    "https://drive.google.com/uc?id=" + file_id + "&export=download",
                    msg,
                    os.path.join(self.path, name),
                )
                await msg.edit(
                    pd.format(
                        file,
                        "Descargado con Exito",
                        sizeof_fmt(await get_file_size(file)),
                    ),
                    buttons=self.manage_button,
                )
            except:
                traceback.print_exc()

        elif "youtube.com" in link or "youtu.be" in link or "twitch.tv" in link:
            msg = await self.bot.send_message(
                self.chat_id,
                pd.format("-", "-", "-"),
                parse_mode="html",
                reply_to=file_id,
            )
            try:
                data_split = self.data.split("^")
                await msg.edit(pd.format("Analizando...", "Analizando...", "Analizando..."))
                data_y = youtube_info.getVideoData(link)
                video_format = str(data_split[3])
                g_format = str(data_split[2])
                name = ""
                islist = False
                if data_y:
                    name = data_y["name"]
                    name = name.replace("/", "_-_")
                    f2, ext3 = os.path.splitext(name)
                    if ext3 in name:
                        name = name.replace("." + ext3, "_-_(" + data_split[5] + ")" + "." + "mkv")
                    elif data_split[4] == "mp4":
                        name += "_-_(" + data_split[5] + ")" + "." + "mkv"
                    else:
                        name += "_-_(" + data_split[5] + ")" + "." + data_split[4]
                await msg.edit(pd.format(name, "Analizando...", "Analizando..."))

                output = os.path.join(self.path, name)
                if "videos" in data_y.keys():
                    name = ""
                    link = data_y["videos"]
                    islist = True
                d_message = pd_2.format(name, "Descargando...📥")
                start = time()
                ydl_opts = {
                    "progress_hooks": [lambda d: asyncio.run(progress_yutu(d, msg, start, pd_2))],
                    "outtmpl": (
                        output
                        if name != "" and not "twitch.tv" in link
                        else (os.path.join(self.path, "%(title)s" + "_-_(" + data_split[5] + ")" + ".%(ext)s"))
                    ),
                    "restrictfilenames": False,
                    "quiet": True,
                    "format": video_format if "mp3" in g_format else video_format + "+ba",
                }
                f35, ext56 = os.path.splitext(name)
                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download(link)
                for fil in check_files(self.path):
                    if f35 in fil:
                        output = os.path.join(self.path, fil)
                        name = fil
                if not name:
                    name = "Revise su video/audio descargado en el administrador de archivos debido a que no se pudo obtener nombre"
                await msg.edit(
                    pd.format(
                        name if not islist else "List -> Check Folder",
                        "Descargado con Exito",
                        sizeof_fmt(await get_file_size(output) if os.path.isfile(output) else 0) if not islist else "-",
                    ),
                    buttons=self.manage_button,
                )
            except:
                await msg.edit(
                    pd.format(
                        "ERROR!",
                        "<i>Video no soportado por formato default-tama</i>",
                        "-",
                    )
                )
                print(traceback.format_exc())

        elif "mega.nz" in link or "mega.co.nz" in link:
            try:
                msg = await self.bot.send_message(self.chat_id, pd.format("-", "Procesando link de MEGA", "-"))
                loop = asyncio.get_event_loop()
                loop.create_task(down_mega(msg, self.path, link))

            except:
                print(traceback.format_exc())

        elif "magnet:?xt=urn:btih" in m.text:
            link = m.text
            msg = await self.bot.send_message(self.chat_id, pd.format("-", "-", "-"))
            loop = asyncio.get_event_loop()
            name = await down_torrent(link, msg, self.path, [args[1], args[2]])
            # task = loop.create_task(down_torrent(link, msg, self.path, [args[1], args[2]]))
            # name = await async_task_maker(args[1], task, args[2])
            # if not name:
            #     return
            file_path = os.path.join(self.path, name)
            await msg.edit(
                pd.format(
                    name,
                    "Descargado con Exito",
                    sizeof_fmt((await get_file_size(file_path) if os.path.isfile(file_path) else get_dir_size(file_path))),
                ),
                buttons=self.manage_button,
            )

        elif "https" in link or "http" in link:
            try:
                msg = await self.bot.send_message(
                    self.chat_id,
                    pd.format("-", "-", "-"),
                    parse_mode="html",
                    reply_to=file_id,
                )

                file = await download_url(link, self.path, msg=msg)
                if file:
                    size = await get_file_size(os.path.join(self.path, file))
                    await msg.edit(
                        pd.format(file, "Descargado con Exito", sizeof_fmt(size)),
                        buttons=self.manage_button,
                    )
            except:
                print(traceback.format_exc())
