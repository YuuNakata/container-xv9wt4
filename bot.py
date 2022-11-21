import asyncio
import datetime
import os
import pathlib
import re
import shutil
import traceback
import urllib
from distutils.dir_util import copy_tree
from time import sleep, time

import magic
import nest_asyncio
from aiohttp import hdrs, web
from httpx import AsyncClient
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.editor import AudioFileClip, VideoFileClip
from PIL import Image
from shazamio import Shazam
from telethon import Button, TelegramClient, events
from telethon import utils as t_utils
from telethon.tl.types import (DocumentAttributeAudio,
                               DocumentAttributeFilename,
                               DocumentAttributeVideo,
                               InputMediaUploadedDocument,
                               MessageMediaDocument)

from downloader import downloader
from downloader.trackers import download_url, unzip_file, zip_file
from downloader.utils import (async_task_maker, cancel_maker, check_files,
                              get_dir_size, get_file_size, progress,
                              sizeof_fmt)
from mega_def import mega as mega_d
from TamaBD import DBHelper
from to_async import to_async
from users.users_temp import (clear_users_selected, get_users_callback,
                              get_users_copy, get_users_path,
                              get_users_selected, get_users_yutulist,
                              set_users_callback, set_users_copy,
                              set_users_path, set_users_selected,
                              set_users_yutulist)
from utils import youtube_info
from utils.callback_helper import CallBack_Helper
from utils.FastTelethon import upload_file
from utils.func_utils import (cut_video, get_fileslist, make_button,
                              manage_tel_connects)
from utils.used_strings import hlp, pd, pd_2, pf
from vars import APP_NAME

nest_asyncio.apply()


bot_token = os.getenv("BOT_TOKEN")
api_id = 14126547
api_hash = "00c0b864b0d619b4a14d516f4c84a5e7"
db = DBHelper("postgres://okbsdinz:aDQS1IIeGW5H8ikfOQOsiJJzzjcX50rH@arjuna.db.elephantsql.com/okbsdinz")

path = os.getcwd() + "/UsersData/{0}/"

##Plantillas##


async def get_megafiles(chat_id, bot, mega):
    buttons = []
    try:
        msg = await bot.send_message(chat_id, "<b>Conectando con la cuenta...</b>")
        await msg.edit("<b>Obteniendo Archivos...</b>")
        files = mega.get_files()
        await msg.edit("<b>Agregando a la lista...</b>")
        Exclude_Mega = ["Cloud Drive", "Inbox", "Rubbish Bin"]
        for file in files:
            if files[file]["a"] != False:
                if not files[file]["a"]["n"] in Exclude_Mega:
                    buttons.append([Button.inline(files[file]["a"]["n"], "mega_d^" + files[file]["h"])])
        buttons.append([Button.inline(" ↼Atras", "m0^")])
        await msg.edit("<b>Seleccione el archivo a borrar:</b>", buttons=buttons)
    except:
        traceback.print_exc()


async def web_server():
    web_app = web.Application(logger=None)
    web_app.add_routes(routes)
    return web_app


async def hello(request):
    html = """
<head>
<title>Tamago-Bot</title>
<meta charset="UTF-8">
</head>
<body>
<h1>Tamago-bot<h1>
<h1>Un bot para descargar desde multilpes sitios web reconocidos<h1>
<a href="https://t.me/RSTamago_Bot">Ir al Chat</a>
</body>
    """
    return web.Response(text=html, content_type="text/html")


#######VARIABLES TEMP#######
async_tasks = []
routes = [web.get("/", hello)]
web_host = None
life_time = 0
############################


async def create_server(route, file_path=None):
    global web_host
    if file_path:
        routes.append(web.get(route, root_route_handler(file_path)))
    app = web.AppRunner(await web_server())
    await app.setup()
    bind_address = "0.0.0.0"
    web_host = web.TCPSite(app, bind_address, int(os.getenv("PORT", 8000)))
    return web_host


async def get_live_time():
    global life_time
    while True:
        life_time += 1
        await asyncio.sleep(1)


async def ping_server(URL):
    try:
        if "herokuapp" in URL:
            while True:
                await asyncio.sleep(1500)
                for _ in range(10):
                    try:
                        async with AsyncClient() as client:
                            await client.get(URL)
                        break
                    except:
                        pass

    except:
        traceback.print_exc()


async def start_server(bot):
    print("------------------- Initalizing Web Server -------------------")
    server = await create_server("/")
    await server.start()
    print("----------------------- Service Started -----------------------")
    URL = "https://{}/".format(APP_NAME)
    print(URL)
    tasks = []
    loop = asyncio.get_event_loop()
    tasks.append(loop.create_task(get_live_time()))
    tasks.append(loop.create_task(ping_server(URL)))
    tasks.append(loop.create_task(bot.send_message(991216025, "Bot Runing!")))
    await asyncio.gather(*tasks)


def root_route_handler(file_path):
    async def res_return(request):
        file_name = os.path.basename(file_path)
        ascii_filename = file_name.encode("ascii", errors="ignore").decode("ascii").replace('"', r"\"")
        return web.FileResponse(
            file_path,
            headers={
                hdrs.CONTENT_TYPE: "application/octet-stream",
                hdrs.CONTENT_DISPOSITION: " ".join(
                    [
                        "attachment;" f'filename="{ascii_filename}"',  # RFC-2616 sec2.2
                    ]
                ),
            },
        )

    return res_return


async def upload_to_tl(file, msg, chat_id, bot, cancel_string, ev):
    try:
        f, ext = os.path.splitext(file)
        filename = os.path.basename(f)
        thumbnail = ""
        d_message = pd_2.format(filename, "Subiendo...📤" + "\n <code>/cancel " + cancel_string + "</code>")
        loop = asyncio.get_event_loop()

        format_list = [
            [
                ".mp4",
                ".mkv",
                ".ogv",
                ".webm",
                ".flv",
                ".avi",
                ".wmv",
                ".mpg",
                ".mpeg",
                ".3gp",
                ".m4v",
            ],
            [".mp3", ".m4a", "webm", "wav", "aac", "flac", "wma"],
        ]

        with open(file, "rb") as out:

            async def up_make(start, start_summ):
                async def pr(d, t):
                    await progress(d, t, msg, start, start_summ, d_message)

                return await upload_file(ev.client, out, pr)

            res = await manage_tel_connects(
                up_make,
                msg,
                pd_2.format(filename, "Subida(En cola){}📤 Posicion: {}"),
            )
            await msg.edit(pd_2.format(filename, "Agregando atributos..."))
            attributes, mime_type = t_utils.get_attributes(
                file,
            )
            default_thumb = db.get_thumb_default(chat_id)
            is_video, is_audio = False, False
            try:
                clip = VideoFileClip(file)
                is_video = True
            except:
                try:
                    clip = AudioFileClip(file)
                    is_audio = True
                except:
                    pass
            if is_video:
                duration = clip.duration
                max_duration = round(duration)
                width, height = clip.size
                if default_thumb == "" or default_thumb == "User.default_thumb":
                    thumbnail = cancel_string + "_thumb.jpg"
                    clip.save_frame(thumbnail, t=duration * 0.1)
                else:
                    thumbnail = await download_url(default_thumb, "", cancel_string + ".jpg")
                    imagen = Image.open(thumbnail)
                    imagen = imagen.resize((1920, 1080))
                    imagen.save(thumbnail)
                media = InputMediaUploadedDocument(
                    file=res,
                    mime_type=mime_type,
                    attributes=[
                        DocumentAttributeFilename(os.path.basename(file)),
                        DocumentAttributeVideo(max_duration, width, height, supports_streaming=True),
                    ],
                    thumb=await bot.upload_file(thumbnail),
                    force_file=False,
                )

            elif is_audio:
                duration = clip.duration
                max_duration = round(duration)
                if default_thumb == "" or default_thumb == "User.default_thumb":
                    thumbnail = None
                else:
                    thumbnail = await download_url(default_thumb, "", cancel_string + ".jpg")
                    imagen = Image.open(thumbnail)
                    imagen = imagen.resize((512, 512))
                    imagen.save(thumbnail)
                media = InputMediaUploadedDocument(
                    file=res,
                    mime_type=mime_type,
                    attributes=[DocumentAttributeFilename(os.path.basename(file)), DocumentAttributeAudio(max_duration, title=filename)],
                    thumb=await bot.upload_file(thumbnail) if thumbnail else thumbnail,
                    force_file=False,
                )

                # if not await async_task_maker(async_tasks, task, cancel_string):
                #     await msg.edit(pd_2.format(filename, "TAREA CANCELADA!"))
                #     return
            else:
                if default_thumb == "" or default_thumb == "User.default_thumb":
                    thumbnail = None
                else:
                    thumbnail = await download_url(default_thumb, "", cancel_string + ".jpg")
                    imagen = Image.open(thumbnail)
                    imagen = imagen.resize((512, 512))
                    imagen.save(thumbnail)
                media = InputMediaUploadedDocument(
                    file=res,
                    mime_type=mime_type,
                    attributes=[
                        DocumentAttributeFilename(os.path.basename(file)),
                    ],
                    thumb=await bot.upload_file(thumbnail) if thumbnail else thumbnail,
                    force_file=False,
                )
            await ev.reply(f"<b>{filename}</b>", file=media)

        await msg.delete()
        if thumbnail:
            os.remove(thumbnail)
    except:
        traceback.print_exc()


async def process_file(file, msg, chat_id, bot, cancel_string, ev):
    try:
        if await get_file_size(file) > 1024 * 1024 * 1999:
            await msg.edit(
                pd.format(
                    "ERROR!-Archivo sobrepasa los " + str(1999) + "MB",
                    "El archivo es muy grande primeramente debe dividirlo en partes menores y despues volver a intentar",
                    "-",
                )
            )
            return False
        return await upload_to_tl(file, msg, chat_id, bot, cancel_string, ev)
    except:
        return


async def upload_mega(msg, id, file):
    mega = mega_d.Mega()
    try:
        mega.login(os.getenv("MEGA_USER"), os.getenv("MEGA_PASSWORD"))
        upload = mega.upload(file)
        link = mega.get_upload_link(upload)
        await msg.edit(pd_2.format(os.path.basename(file), "Link :\n" + link + "\n\n" + "➜/main"))
    except:
        traceback.print_exc()


########-Manage Bot-###########


def acceso(id):
    if str(id) in os.getenv("OwnerID"):
        return True
    return False


def acceso_v2(id):
    banned = os.getenv("BANNED_USERS")
    if str(id) in banned:
        return False
    return True


def init():

    try:
        bot = TelegramClient("bot", api_id=api_id, api_hash=api_hash, flood_sleep_threshold=120).start(bot_token=bot_token)

        bot.parse_mode = "html"

        @bot.on(events.NewMessage(pattern="/start"))
        async def start(ev: events.NewMessage.Event):
            if ev.message.from_id:
                id = ev.message.from_id.user_id
            else:
                id = ev.chat_id
            chat_id = ev.chat_id
            if acceso(chat_id):
                user = await bot.get_entity(id)
                start_message = f"<b>Hola {user.first_name}-tama</b>\n\nPuedo descargar cualquier cosa y subirla a telegram-tama"
                if not db.get_u(id):
                    db.new_u(id)
                    start_message += "\n\nSu cuenta en el bot acaba se ser creada con exito-tama"
                else:
                    start_message += "\n\nYa tienes cuenta en el bot-tama"
                start_message += "\n\n<b>Tiempo activo de Tama:</b> {:02d}:{:02d}:{:02d}".format(
                    life_time // 3600, (life_time % 3600) // 60, life_time % 60
                )
            await bot.send_message(chat_id, start_message, reply_to=ev._message_id)

        @bot.on(events.NewMessage(pattern="/help"))
        async def getbk(ev: events.NewMessage.Event):
            chat_id = ev.chat_id
            if acceso(chat_id):
                await bot.send_message(chat_id, hlp)

        @bot.on(events.NewMessage(pattern="/clear"))
        async def clear(ev: events.NewMessage.Event):
            chat_id = ev.chat_id
            if acceso(chat_id):
                shutil.rmtree(path.format(chat_id))
                await bot.send_message(chat_id, "Sus archivos locales han sido borrados con exito")

        @bot.on(events.NewMessage(pattern="/space"))
        async def space(ev: events.NewMessage.Event):
            chat_id = ev.chat_id
            if acceso(chat_id):
                total, used, free = shutil.disk_usage(os.getcwd())
                root_path = os.path.join(os.getcwd(), "UsersData")
                id_space = []
                if os.path.exists(root_path):
                    content = os.listdir(root_path)
                    for directory in content:
                        if not os.path.isfile(directory):
                            id_space.append(
                                "{} : {}".format(
                                    os.path.basename(directory),
                                    sizeof_fmt(get_dir_size(os.path.join(root_path, directory))),
                                )
                            )
                await bot.send_message(
                    chat_id,
                    f"Total: {sizeof_fmt(total)}\nUsado: {sizeof_fmt(used)}\nLibre: {sizeof_fmt(free)} \n\n"
                    + "\n\nUsuarios:\n\n"
                    + "".join(item + os.linesep for item in id_space),
                )

        @bot.on(events.NewMessage(pattern="/main"))
        async def main(ev: events.NewMessage.Event):
            if acceso(ev.chat_id):
                markup = [
                    [Button.inline("👤Perfil", "m0^3")],
                    [Button.inline("🔍Menu de Exploracion", "m0^5")],
                    [Button.inline("🎛Menu de Subidas", "m0^2")],
                    [Button.inline("💾Menu de Archivos", "m0^1")],
                ]
                await bot.send_message(
                    ev.chat_id,
                    "<b>Menu Principal</b>\n\nQue desea hacer?:",
                    reply_to=ev._message_id,
                    buttons=markup,
                )

        @bot.on(events.NewMessage(pattern="/cancel"))
        async def tasks(ev: events.NewMessage.Event):
            try:
                for t in async_tasks:
                    for task in t[1]:
                        task.cancel()
                        if task.cancelled():
                            print("Tarea Cancelada")
            except:
                traceback.print_exc()

        @bot.on(events.NewMessage(pattern="/zip"))
        async def zipp(ev: events.NewMessage.Event):
            if ev.message.from_id:
                id = ev.message.from_id.user_id
            else:
                id = ev.chat_id
            chat_id = ev.chat_id
            zips = db.get_zips(id)
            found = False
            szips = str(ev.message.message).split(" ")
            for z in szips:
                if z.isdecimal():
                    zips = int(z)
                    db.set_zips(id, zips)
                    found = True
                    break
            if found:
                await bot.send_message(chat_id, f"Tamaño de lo zips establecido a {zips} MB")
            else:
                await bot.send_message(
                    chat_id,
                    "Por favor escriba el comando adecuadamente\n\n/zip *tamaño en MB a dividir las partes*\n--Obviamente eliminando los *",
                    reply_to=ev._message_id,
                )

        @bot.on(events.NewMessage(incoming=True))
        async def process(ev: events.NewMessage.Event):
            try:
                if ev.message.from_id:
                    id = ev.message.from_id.user_id
                else:
                    id = ev.chat_id
                chat_id = ev.chat_id
                reply_id = ev.original_update.message.id
                if acceso(chat_id):
                    if acceso_v2(id):
                        ##Tipo de mensaje##
                        text = str(ev.message)
                        if type(ev.media) == MessageMediaDocument:
                            mime_type = ev.media.document.mime_type
                            if not "image/webp" in mime_type and not "audio/ogg" in mime_type:
                                filename = ev.media.document.attributes
                                for i in range(len(filename)):
                                    if type(filename[i]) == DocumentAttributeFilename:
                                        filename = filename[i].file_name
                                    if len(filename) < 2:
                                        ty_name = mime_type.split("/")
                                        filename = ty_name[-2] + "_desconocido." + ty_name[-1]
                                markup = [Button.inline("Descargar", f"df^{reply_id}")]
                                download = downloader.Downloader(
                                    reply_id,
                                    bot,
                                    ev._message_id,
                                    ev.chat,
                                    chat_id,
                                    get_users_path(id),
                                    [Button.inline("Menu de Archivos", "m0^0")],
                                    auto=True,
                                    ev=ev,
                                )
                                loop = asyncio.get_event_loop()
                                await download.download_identifier()
                                # msg=await bot.send_message(ev.chat_id,f'Archivo:{filename}',reply_to=reply_id,buttons=markup)
                        elif "magnet:?xt=urn:btih" in text:
                            markup = [Button.inline("Descargar", f"df^{reply_id}")]
                            download = downloader.Downloader(
                                reply_id,
                                bot,
                                ev._message_id,
                                ev.chat,
                                chat_id,
                                get_users_path(id),
                                [Button.inline("Menu de Archivos", "m0^0")],
                                auto=True,
                            )
                            loop = asyncio.get_event_loop()
                            cancel_string = cancel_maker()
                            task = loop.create_task(download.download_identifier([db, async_tasks, cancel_string]))
                            async_tasks.append([cancel_string, [task]])
                            # await download.download_identifier([db])
                            # msg=await bot.send_message(ev.chat_id,f'Link de Torrent Detectado!',reply_to=reply_id,buttons=markup)
                        elif "youtube.com" in text or "youtu.be" in text or "bilibili" in text:
                            markup = [
                                [Button.inline("Video", f"yt_video^{reply_id}")],
                                [Button.inline("Audio", f"yt_video^{reply_id}^mp3")],
                            ]
                            await bot.send_message(
                                ev.chat_id,
                                f"Elije la opcion a descargar-tama",
                                reply_to=reply_id,
                                buttons=markup,
                            )
                        elif "twitch.tv" in text:
                            markup = [[Button.inline("Elegir Formato", f"yt_video^{reply_id}")]]
                            await bot.send_message(
                                ev.chat_id,
                                f"Elije la opcion a descargar-tama",
                                reply_to=reply_id,
                                buttons=markup,
                            )
                        elif "https" in text or "http" in text:
                            markup = [Button.inline("Descargar", f"df^{reply_id}")]
                            download = downloader.Downloader(
                                reply_id,
                                bot,
                                ev._message_id,
                                ev.chat,
                                chat_id,
                                get_users_path(id),
                                [Button.inline("Menu de Archivos", "m0^0")],
                                auto=True,
                            )
                            loop = asyncio.get_event_loop()
                            loop.create_task(download.download_identifier([db]))
                            # await download.download_identifier()
                            # msg=await bot.send_message(ev.chat_id,f'Link Detectado!',reply_to=reply_id,buttons=markup)
                    else:
                        daten = int(os.getenv("BAN_DAY")) - datetime.datetime.now().day
                        await bot.send_message(
                            ev.chat_id,
                            f"<b>🚫Ha sido baneado del uso del bot temporalmente🚫</b>\n\n-Motivo:Por no mostrar interes en el progreso del bot\n\nTiempo restante:{daten} dias",
                            reply_to=ev._message_id,
                        )
                        await ev.delete()

            except:
                print(traceback.format_exc())

        @bot.on(events.CallbackQuery)
        async def callbackdata(ev: events.CallbackQuery):

            ######INDICE#######
            # Categorias de data nivel 1:
            #   m0 - menu 0
            #   m1 - menu 1
            ###################

            await asyncio.sleep(0)
            if ev.original_update:
                id = ev.original_update.user_id
            else:
                id = ev.query.user_id
            data = ev.data
            data = data.decode()
            chat_id = ev.chat_id
            chat = ev.chat
            message_id = ev._message_id

            call_message = bot.iter_messages(chat, ids=message_id)
            the_message = None
            async for m in call_message:
                the_message = m

            pathdir = pathlib.Path(get_users_path(id))
            if not os.path.exists(pathdir):
                os.makedirs(pathdir)

            await ev.answer("Procesando...")

            data_splited = data.split("^")

            if data_splited[0] == "m3":
                if "mark_list" == data_splited[1]:
                    data_mark = data.replace("mark_list^", "")
                    select_list = get_users_selected(id)
                    if "one_zip" in data_mark:
                        file_id = int(data_mark.split("one_zip^")[1])
                        files = check_files(get_users_path(id))
                        file = files[file_id]
                        select_list.append(file)
                        set_users_selected(id, select_list)
                        await get_fileslist(
                            id,
                            chat_id,
                            bot,
                            "mark_list^one_zip",
                            select_list,
                            the_message,
                        )
                    elif "up_mega" in data_mark:
                        file_id = int(data_mark.split("up_mega^")[1])
                        files = check_files(get_users_path(id))
                        file = files[file_id]
                        select_list.append(file)
                        set_users_selected(id, select_list)
                        await get_fileslist(
                            id,
                            chat_id,
                            bot,
                            "mark_list^up_mega",
                            select_list,
                            the_message,
                        )
                    elif "un_zip" in data_mark:
                        file_id = int(data_mark.split("un_zip^")[1])
                        files = check_files(get_users_path(id))
                        file = files[file_id]
                        select_list.append(file)
                        set_users_selected(id, select_list)
                        await get_fileslist(
                            id,
                            chat_id,
                            bot,
                            "mark_list^un_zip",
                            select_list,
                            the_message,
                        )
                    elif "u" in data_mark:
                        file_id = int(data_mark.split("u^")[1])
                        files = check_files(get_users_path(id))
                        file = files[file_id]
                        select_list.append(file)
                        set_users_selected(id, select_list)
                        await get_fileslist(id, chat_id, bot, "mark_list^u", select_list, the_message)
                    return
                elif "build_zip" == data_splited[1]:
                    select_list = get_users_selected(id)
                    async with bot.conversation(chat) as conv:
                        main = await conv.send_message("<b>Escribe a continuacion el nombre del comprimido:</b>")
                        zip_name = await conv.get_response()
                        zip_name = str(zip_name.message)
                        await main.delete()

                    msg = await bot.send_message(chat_id, pd.format(zip_name, "Organizando Archivos", "-"))

                    for i in range(len(select_list)):
                        select_list[i] = os.path.join(get_users_path(id), select_list[i])
                    await msg.edit(pd.format(zip_name, "Comprimiendo", "-"))
                    await zip_file(os.path.join(get_users_path(id), zip_name), db, msg, id, select_list, back_button=make_button("m0^1"))
                    await msg.edit(
                        pd.format(
                            zip_name,
                            "Finalizada la compresion",
                            sizeof_fmt(await get_file_size(os.path.join(get_users_path(id), zip_name + ".7z"))),
                        ),
                        buttons=make_button("m0^1"),
                    )
                    clear_users_selected(id)

                elif "upl" == data_splited[1]:
                    select_list = get_users_selected(id)
                    for file in select_list:
                        size = await get_file_size(os.path.join(get_users_path(id), file))
                        msg = await bot.send_message(
                            chat_id,
                            pd.format(file, "Subida(En cola)...📤", sizeof_fmt(size)),
                            reply_to=id,
                        )
                        cancel_string = cancel_maker()
                        loop = asyncio.get_event_loop()
                        task = loop.create_task(process_file(os.path.join(get_users_path(id), file), msg, chat_id, bot, cancel_string, ev))
                        asyncio.gather(task)
                        # async_tasks.append([cancel_string, [task]])

                    clear_users_selected(id)
                elif "up_mega" == data_splited[1]:

                    select_list = get_users_selected(id)
                    for file in select_list:
                        size = await get_file_size(os.path.join(get_users_path(id), file))
                        msg = await bot.send_message(
                            chat_id,
                            pd.format(file, "Subiendo...", sizeof_fmt(size)),
                            reply_to=id,
                        )
                        loop = asyncio.get_event_loop()
                        loop.create_task(upload_mega(msg, id, os.path.join(get_users_path(id), file)))
                    clear_users_selected(id)
                elif "un_zip_all" == data_splited[1]:
                    select_list = get_users_selected(id)
                    for file in select_list:
                        file_path = os.path.join(get_users_path(id), file)
                        if os.path.isfile(file_path):
                            size = await get_file_size(file_path)
                            msg = await bot.send_message(
                                chat_id,
                                pd.format(file, "Extrayendo...", sizeof_fmt(size)),
                                reply_to=id,
                            )
                            loop = asyncio.get_event_loop()
                            loop.create_task(unzip_file(file_path, msg, get_users_path(id), make_button("m0^1")))
                        else:
                            await bot.send_message(pd_2.format("ERROR", "El directorio seleccionado no es un archivo"))
                    clear_users_selected(id)
            try:
                await ev.delete()
            except:
                await the_message.edit("Tamago-bot", buttons=None)

            if data_splited[0] == "m0":
                clear_users_selected(id)

                callback_func = CallBack_Helper(bot, await bot.get_entity(id), chat_id)
                await callback_func.m0(data_splited[1], db)

            elif data_splited[0] == "m1":
                callback_func = CallBack_Helper(bot, await bot.get_entity(id), chat_id, chat)
                await callback_func.m1(data_splited, db)

            elif data_splited[0] == "m2":
                if "fl" == data_splited[1]:
                    clear_users_selected(id)
                    action = data_splited[2] + ("^" + data_splited[3] if len(data_splited) > 3 else "")
                    await get_fileslist(id, chat_id, bot, action, zip_size=db.get_zips(id) if "z" in action else None)
                elif "rnm" == data_splited[1]:
                    file_id = int(data_splited[2])
                    files = check_files(get_users_path(id))
                    file = files[file_id]
                    arch_old = os.path.join(get_users_path(id), file)
                    async with bot.conversation(chat) as conv:
                        await conv.send_message(f"Escribe el nombre nuevo para <b>{file}</b>:")
                        arch_new = await conv.get_response()
                        arch_new = str(arch_new.message)
                    f, ext = os.path.splitext(os.path.join(get_users_path(id), arch_new))
                    f2, ext2 = os.path.splitext(arch_old)
                    if not "." in ext:
                        arch_new = arch_new + ext2
                    arch_new = os.path.join(get_users_path(id), arch_new)
                    os.rename(arch_old, arch_new)
                    f = f.split("/")[-1]
                    f2 = f2.split("/")[-1]
                    await bot.send_message(
                        chat_id,
                        f"Archivo <b>{f2}</b> renombrado a <b>{f}</b> con exito-tama",
                        buttons=make_button("m0^1"),
                    )
                elif "erase_mega" == data_splited[1]:
                    mega = mega_d.Mega()
                    mega.login(os.getenv("MEGA_USER"), os.getenv("MEGA_PASSWORD"))
                    await get_megafiles(chat_id, bot, mega)

                elif "min_see" == data_splited[1]:
                    link = data_splited[2]
                    await bot.send_file(
                        chat_id,
                        file=link,
                        caption="",
                        buttons=[Button.inline(" ↼Atras", "m0^4")],
                    )

                elif "min_set_v1" == data_splited[1]:
                    if db.get_u(id):
                        thumbs = db.get_thumb_list(id)
                        markup = []
                        back_button = [Button.inline(" ↼Atras", "m0^2")]
                        if len(thumbs) > 1:
                            for t in thumbs.split(os.linesep):
                                if len(t) > 1 and not "User.thumb_list" in t:
                                    t_split = t.split("|")
                                    markup.append(
                                        [
                                            Button.inline(
                                                t_split[0],
                                                "m2^min_set_v2^" + t_split[1],
                                            )
                                        ]
                                    )
                            markup.append([Button.inline("🗑Eliminar", "m2^min_set_v2^delete")])
                            markup.append(back_button)
                            default_thumb = db.get_thumb_default(id)
                            if default_thumb != "" and default_thumb != "User.default_thumb":
                                await bot.send_file(
                                    chat_id,
                                    file=default_thumb,
                                    caption="<b>Miniatura Actual  ⤴️\n\nElije la miniatura por defecto:</b>",
                                    buttons=markup,
                                )
                            else:
                                await bot.send_message(
                                    chat_id,
                                    "<b>Elije la miniatura por defecto:</b>",
                                    buttons=markup,
                                )
                elif "min_set_v2" == data_splited[1]:
                    link = data_splited[2]
                    value = link == "delete"
                    if db.set_thumb_default(id, link, value) and not value:
                        await bot.send_file(
                            chat_id,
                            file=link,
                            caption="Miniatura por defecto guardada!",
                            buttons=make_button("m0^2"),
                        )
                    else:
                        await bot.send_message(
                            chat_id,
                            "Miniatura por defecto eliminada!",
                            buttons=make_button("m0^2"),
                        )
                elif "min_delete" == data_splited[1]:
                    link = data_splited[2]
                    if db.get_thumb_default(id) == link:
                        if db.delete_thumb_list(id, link) and db.set_thumb_default(id, "", True):
                            await bot.send_message(
                                chat_id,
                                "Miniatura borrada con exito!",
                                buttons=make_button("m0^4"),
                            )
                        else:
                            await bot.send_message(
                                chat_id,
                                "Error al borrar miniatura",
                                buttons=make_button("m0^4"),
                            )
                    else:
                        if db.delete_thumb_list(id, link):
                            await bot.send_message(
                                chat_id,
                                "Miniatura borrada con exito!",
                                buttons=make_button("m0^4"),
                            )
                        else:
                            await bot.send_message(
                                chat_id,
                                "Error al borrar miniatura",
                                buttons=make_button("m0^4"),
                            )

                elif "c_vid" == data_splited[1]:
                    file_id = int(data_splited[2])
                    files = check_files(get_users_path(id))
                    file = files[file_id]
                    msg = await bot.send_message(chat_id, pd.format(os.path.basename(file), "Analizando", "-"))
                    await cut_video(os.path.join(get_users_path(id), file), msg, bot, chat, chat_id, pd, make_button("m0^1"))
                elif "share_file" == data_splited[1]:
                    file_id = int(data_splited[2])
                    files = check_files(get_users_path(id))
                    file = files[file_id]
                    file_path = os.path.join(get_users_path(id), file)
                    if os.path.isfile(file_path):
                        msg = await bot.send_message(chat_id, pd.format(file, "Compartiendo...", "-"))
                        link = "/files/{}/{}".format(chat_id, urllib.parse.quote(file, encoding="utf-8"))
                        await web_host.stop()
                        server = await create_server(link, file_path)
                        await server.start()
                        await msg.edit(
                            "<b>🗄Archivo: {}</b>\n\n<b>🔗Link:</b> {}\n\n<b>💾Tamaño: {}</b>".format(
                                file,
                                "<a href='https://{}{}'>{}</a>".format(APP_NAME, link, file),
                                sizeof_fmt(await get_file_size(file_path)),
                            )
                        )
                    else:
                        msg = await bot.send_message(chat_id, pd.format("ERROR", "Aun no disponible compartir carpetas", "-"))
                elif "copy_file" == data_splited[1]:
                    file_id = int(data_splited[2])
                    current_path = get_users_path(id)
                    files = check_files(current_path)
                    file = files[file_id]
                    set_users_copy(id, os.path.join(current_path, file))
                    await get_fileslist(id, chat_id, bot, "m2^explorer", current_path=current_path)
                elif "paste_file" == data_splited[1]:
                    current_path = get_users_path(id)
                    src = get_users_copy(id)
                    msg = await bot.send_message(
                        chat_id,
                        pd.format(
                            os.path.basename(src),
                            "Copiando...",
                            sizeof_fmt(await get_file_size(src)),
                        ),
                    )

                    @to_async(executor=None)
                    def copy2():
                        if os.path.isfile(src):
                            shutil.copy2(src, current_path)
                        else:
                            try:
                                copy_tree(src, os.path.join(current_path, os.path.basename(src)))
                            except:
                                traceback.format_exc()

                    await copy2()

                    set_users_copy(id, None)
                    await msg.delete()
                    await get_fileslist(id, chat_id, bot, "m2^explorer", current_path=current_path)

                elif "create_folder" == data_splited[1]:
                    current_path = get_users_path(id)

                    try:
                        async with bot.conversation(chat) as conv:
                            msg = await conv.send_message("Por favor a continuacion envie el nombre de la carpeta:")
                            folder_name = await conv.get_response()
                            folder_name = str(folder_name.message)
                            await msg.delete()
                    except:
                        await msg.edit(
                            "Ha demorado mucho en enviar el nombre vuelva a intentarlo",
                            buttons=make_button("m1^explorer"),
                        )
                        return
                    os.makedirs(os.path.join(current_path, folder_name))
                    await get_fileslist(id, chat_id, bot, "m2^explorer", current_path=current_path)

                elif "explorer" == data_splited[1]:
                    file_id = int(data_splited[2])
                    current_path = get_users_path(id)

                    files = check_files(current_path)
                    file = files[file_id]
                    file_path = os.path.join(current_path, file)
                    cover = None
                    if os.path.isfile(file_path):
                        size = sizeof_fmt(await get_file_size(file_path))
                        val = magic.from_file(file_path)
                        mime = magic.from_file(file_path, mime=True)
                        msg = await bot.send_message(
                            chat_id,
                            pd.format(os.path.basename(file_path), "Loading...", size),
                        )
                        if "video" in mime or "audio" in mime:
                            isVideo, isAudio = False, False
                            try:
                                clip = VideoFileClip(file_path)
                                isVideo = True
                            except:
                                try:
                                    clip = AudioFileClip(file_path)
                                    isAudio = True
                                except:
                                    pass
                            if isVideo:
                                val = """
    >Fps: {}
    >Alto: {}
    >Ancho: {}
    >Duracion: {}
                                """.format(
                                    "{:.2f}".format(clip.fps),
                                    clip.h,
                                    clip.w,
                                    "{:02d}:{:02d}:{:02d}".format(
                                        clip.duration // 3600,
                                        (clip.duration % 3600) // 60,
                                        clip.duration % 60,
                                    ),
                                )

                            elif isAudio:
                                try:
                                    shazam = Shazam()
                                    out = await shazam.recognize_song(file_path)
                                    song = out["track"]["title"]
                                    artist = out["track"]["subtitle"]
                                    subject = out["track"]["share"]["subject"]
                                    cover = out["track"]["images"]["coverart"]
                                    val = """
    >Titulo: {}
    >Autor: {}
    >Subject: {}
    >Duracion: {}
                                    """.format(
                                        song,
                                        artist,
                                        subject,
                                        "{:02d}:{:02d}:{:02d}".format(
                                            clip.duration // 3600,
                                            (clip.duration % 3600) // 60,
                                            clip.duration % 60,
                                        ),
                                    )

                                except:
                                    pass
                        await msg.delete()
                        if cover:
                            msg = await bot.send_file(
                                chat_id,
                                file=cover,
                                caption="<b>Nombre:</b> {}\n<b>Tamaño:</b> {}\n<b>Tipo:</b> {}\n<b>Info:</b> {}".format(file, size, mime, val),
                                buttons=make_button("m1^explorer"),
                            )
                        else:
                            msg = await bot.send_message(
                                chat_id,
                                "<b>Nombre:</b> {}\n<b>Tamaño:</b> {}\n<b>Tipo:</b> {}\n<b>Info:</b> {}".format(file, size, mime, val),
                                buttons=make_button("m1^explorer"),
                            )

                    else:
                        set_users_path(id, file_path)
                        await get_fileslist(id, chat_id, bot, "m2^explorer", current_path=file_path)

                elif "file_d" == data_splited[1]:
                    file_id = int(data_splited[2])
                    files = check_files(get_users_path(id))
                    file = files[file_id]
                    try:
                        file_path = os.path.join(get_users_path(id), file)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                        else:
                            shutil.rmtree(file_path)
                    except Exception as e:
                        await bot.send_message(chat_id, e)
                    await bot.send_message(chat_id, f"Archivo <b>{file}</b> borrado con exito")
                    await get_fileslist(id, chat_id, bot, "m2^file_d")
                elif "file_d_all" == data_splited[1]:
                    files = check_files(get_users_path(id))
                    try:
                        for file in files:
                            file_path = os.path.join(get_users_path(id), file)
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                            else:
                                shutil.rmtree(file_path)
                    except Exception as e:
                        await bot.send_message(chat_id, e)
                    await bot.send_message(
                        chat_id,
                        f"Borrados todos los archivos con exito",
                        buttons=make_button("m0^1"),
                    )

            # elif 'upload_mega' in data:
            #     await get_fileslist(id,chat_id,bot,'up_mega')
            elif "yt_video" in data:
                try:
                    splited = data.split("^")[1]
                    if not "List_" in splited:
                        reply_id = int(splited)
                        message = bot.iter_messages(chat, ids=reply_id)
                        async for m in message:
                            CLEANR = re.compile("<.*?>")
                            url = re.sub(CLEANR, "", m.text)
                    else:
                        url = get_users_yutulist(id)[int(splited.split("_")[1])]
                        reply_id = splited
                    markup = []
                    msg = await bot.send_message(
                        chat_id,
                        "<b>Procesando Solicitud...</b>",
                        reply_to=reply_id if not "List_" in str(reply_id) else None,
                    )
                    data_y = youtube_info.getVideoData(url)
                    if data_y:
                        for d in data_y["formats"]:
                            if not "twitch.tv" in url:
                                if d["height"] != None and "filesize" in d and not "^mp3" in data and d["audio_ext"] == "none":
                                    if d["filesize"] != None:
                                        markup.append(
                                            [
                                                Button.inline(
                                                    d["format_note"] + " - (" + d["video_ext"] + ") " + sizeof_fmt(int(d["filesize"])),
                                                    f"df^{reply_id}^mp4^" + str(d["format_id"]) + "^" + d["video_ext"] + "^" + d["format_note"],
                                                )
                                            ]
                                        )
                                elif (
                                    d["audio_ext"] != "none"
                                    and "filesize" in d
                                    and d["video_ext"] == "none"
                                    and d["height"] == None
                                    and "^mp3" in data
                                ):
                                    if d["filesize"] != None:
                                        markup.append(
                                            [
                                                Button.inline(
                                                    d["format_note"] + " - (" + d["audio_ext"] + ") " + sizeof_fmt(int(d["filesize"])),
                                                    f"df^{reply_id}^mp3^" + str(d["format_id"]) + "^" + d["audio_ext"] + "^" + d["format_note"],
                                                )
                                            ]
                                        )
                            elif "filesize_approx" in d:
                                markup.append(
                                    [
                                        Button.inline(
                                            d["format_id"] + " - (" + d["video_ext"] + ") " + sizeof_fmt(int(d["filesize_approx"])),
                                            f"df^{reply_id}^mp4^" + str(d["format_id"]) + "^" + d["video_ext"] + "^" + d["format_id"],
                                        )
                                    ]
                                )
                    if not "^mp3" in data:
                        markup.append(
                            [
                                Button.inline(
                                    "Default/best",
                                    f"df^{reply_id}^mp4^" + "b" + "^" + "mp4",
                                )
                            ]
                        )
                    else:
                        markup.append(
                            [
                                Button.inline(
                                    "Default/best",
                                    f"df^{reply_id}^mp3^" + "ba" + "^" + "mp3",
                                )
                            ]
                        )
                    await msg.edit("<b>Seleccione la calidad del video:</b>\n\n", buttons=markup)
                except:
                    traceback.print_exc()

            elif "mega_d^" in data:
                file_id = data.split("mega_d^")[1]
                try:
                    mega = mega_d.Mega()
                    msg = await bot.send_message(chat_id, "<b>Conectando con la cuenta...</b>")
                    mega.login(os.getenv("MEGA_USER"), os.getenv("MEGA_PASSWORD"))
                    await msg.edit("<b>Borrando archivo...</b>")
                    mega.destroy(file_id)
                    await get_megafiles(chat_id, bot, mega)
                except:
                    traceback.print_exc()

            elif "df^" in data:
                # file_id=int(data.split('^')[1])
                splited = data.split("^")[1]

                if not "List_" in splited:
                    file_id = int(splited)
                    link = None
                    message = bot.iter_messages(chat, ids=file_id)
                else:
                    link = get_users_yutulist(id)[int(splited.split("_")[1])]
                    file_id = None
                    message = None
                download = downloader.Downloader(
                    file_id,
                    bot,
                    message,
                    chat,
                    chat_id,
                    get_users_path(id),
                    make_button(),
                    data,
                    link=link,
                )
                await download.download_identifier([db])

            elif "z^" in data:
                file_id = int(data.split("z^")[1])
                files = check_files(get_users_path(id))
                file = files[file_id]
                size = await get_file_size(os.path.join(get_users_path(id), file))
                msg = await bot.send_message(chat_id, pd.format(file, "Comprimiendo...🗜", sizeof_fmt(size)))
                await zip_file(os.path.join(get_users_path(id), file), db, msg, id, back_button=make_button("m0^1"))

        asyncio.run(start_server(bot))
        bot.run_until_disconnected()

    except:
        print(traceback.format_exc())


if __name__ == "__main__":
    init()
