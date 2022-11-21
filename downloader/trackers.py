import asyncio
import asyncio.events as events
import os
import pathlib
import re
import traceback
import types
from functools import partial
from time import time
from zipfile import ZIP_DEFLATED, ZipFile

import httpx
import libtorrent as lt
from mega_def import megafolder
from mega_def.mega import Mega
from py7zr import SevenZipFile
from telethon import Button

from to_async import to_async

from . import multiFile
from .googleDriveFileDownloader import googleDriveFileDownloader
from .utils import get_dir_size, get_file_size, progress, progress_mega, sizeof_fmt

pd_2 = "<b>🗄Archivo:</b>{0}\n\n<b>♻️Estado:</b>{1}"
pd = "<b>🗄Archivo:</b>{0}\n\n<b>♻️Estado:</b>{1}\n\n<b>💾Tamaño:</b>{2}"
pf = "<b>✅Archivo Subido con exito!✅</b>\n\n<b>🆙Subido por:</b> @{0}\n\n<b>User:</b> /pass\n<b>Password:</b> /pass\n\n🔗Link:{1}"


import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)


async def download_file_from_google_drive(link, msg, name):
    try:
        a = googleDriveFileDownloader()
        await msg.edit(pd.format(os.path.basename(name), "Descargando...", "Indefinido hasta finalizar"))
        a.downloadFile(link, name)
        return name
    except:
        print(traceback.format_exc())


def req_file_size(req):
    try:
        return int(req.headers["content-length"])
    except:
        return 0.0


async def get_url_file_name(url, req):
    try:
        if "Content-Disposition" in req.headers.keys():
            return str(re.findall("filename=(.+)", req.headers["Content-Disposition"])[0])
        else:
            tokens = str(url).split("/")
            return tokens[len(tokens) - 1]
    except:
        traceback.print_exc()
        tokens = str(url).split("/")
        return tokens[len(tokens) - 1]


async def download_url(url, path, filename=None, msg=None, params=None):
    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0"}
    ) as client:
        async with client.stream("GET", url, params=params, timeout=5, follow_redirects=True) as req:
            if req.status_code == 200 or req.status_code == 302:
                try:
                    if not filename:
                        filename = await get_url_file_name(url, req)
                        filename = filename.replace('"', "")
                    pathdir = pathlib.Path(path)
                    with open(os.path.join(pathdir, filename), "wb") as file:
                        if msg != None:
                            await msg.edit(pd.format(filename, "Descargando...", sizeof_fmt(req_file_size(req))))
                        start = time()
                        start_summ = [start]
                        d_message = pd_2.format(filename, "Descargando...📥")
                        async for chunk in req.aiter_bytes():
                            file.write(chunk)
                            if msg != None:
                                await progress(req.num_bytes_downloaded, int(req.headers["Content-Length"]), msg, start, start_summ, d_message)
                    return filename
                except Exception as e:
                    traceback.print_exc()
                    await msg.edit(pd_2.format("ERROR", e))
            else:
                if msg != None:
                    await msg.edit(pd_2.format("URL invalida", "-"))
            pass


async def down_torrent(link, msg, path, args):
    try:
        fingerprint = lt.fingerprint("qB", 3, 3, 5, 0)
        ses = lt.session(fingerprint)
        ses.listen_on(6881, 6891)
        ses.add_dht_router("router.bittorrent.com", 6881)
        ses.add_dht_router("router.utorrent.com", 6881)
        ses.add_dht_router("dht.aelitis.com", 6881)
        ses.add_dht_router("dht.transmissionbt.com", 6881)
        sett = {
            "allow_multiple_connections_per_ip": True,
            # "dont_count_slow_torrents": True,
            "active_downloads": -1,
            "active_seeds": 7,
            "active_checking": 3,
        }

        ses.apply_settings(sett)
        params = {
            "save_path": f"{path}",
            "storage_mode": lt.storage_mode_t(2),
        }
        handle = lt.add_magnet_uri(ses, link, params)
        await msg.edit(pd.format("Analizando Torrent", "Downloading Metadata...", "Analizando Torrent"))
        while not handle.has_metadata():
            await asyncio.sleep(0.01)
        await msg.edit(pd.format("Analizando Torrent", "Iniciando Descarga...", "Analizando Torrent"))
        start = time()
        start_summ = [start]
        while handle.status().state != lt.torrent_status.seeding:

            s = handle.status()
            d_message = pd_2.format(s.name, "Descargando...📥")
            await progress(s.total_download, s.total, msg, start, start_summ, d_message, s.download_rate)
            await asyncio.sleep(1)
        del handle
        return s.name

    except:
        print(traceback.format_exc())


async def zip_file(file_path, db, msg, id, compress_list=None, back_button=None):
    try:
        file_name = os.path.basename(file_path)
        chunk_size = 1024 * 1024 * db.get_zips(id)
        start = time()
        start_summ = [start]
        d_message = pd_2.format(file_name, "Comprimiendo...")
        d_message_part = pd_2.format(file_name, "Comprimiendo...     Parte <b>{}</b> de <b>{}</b>")
        file_size = 0
        if not compress_list:
            file_size = await get_file_size(file_path) if os.path.isfile(file_path) else get_dir_size(file_path)
        else:
            for file in compress_list:
                file_size += await get_file_size(file) if os.path.isfile(file) else get_dir_size(file)

        def partial_progress(total_size, original_write, self, buf):
            partial_progress.bytes += len(buf)
            partial_progress.obytes += 1024 * 8  # Hardcoded in zipfile.write
            asyncio.run(
                progress(
                    partial_progress.bytes,
                    total_size,
                    msg,
                    start,
                    start_summ,
                    d_message
                    if compress_list
                    else d_message_part.format(
                        ((partial_progress.bytes // chunk_size) + 1),
                        ((total_size // chunk_size) + (1 if total_size != chunk_size else 0)),
                    ),
                )
            )
            return original_write(buf)

        def sh_make_archive(compress_list, file_path=file_path, zipF=None):
            def make_archive(file, zipF, prefix=""):
                if os.path.isfile(file):
                    zipF.write(file, arcname=os.path.join(prefix, os.path.basename(file)))
                else:
                    zipF.write(file, arcname=os.path.join(prefix, os.path.basename(file)))
                    for item in os.listdir(file):
                        make_archive(os.path.join(file, item), zipF, os.path.join(prefix, os.path.basename(file)))

            if not zipF:
                with ZipFile(file_path + ".7z", "w") as zipF:
                    partial_progress.bytes = 0
                    partial_progress.obytes = 0
                    zipF.fp.write = types.MethodType(partial(partial_progress, file_size, zipF.fp.write), zipF.fp)
                    for file in compress_list:
                        make_archive(file, zipF)
            else:
                make_archive(file_path, zipF)

        if (file_size > chunk_size) and not compress_list:

            mult_file = multiFile.MultiFile(file_path + ".7z", chunk_size)

            with ZipFile(mult_file, mode="w", compression=ZIP_DEFLATED) as zip:
                partial_progress.bytes = 0
                partial_progress.obytes = 0
                zip.fp.write = types.MethodType(partial(partial_progress, file_size, zip.fp.write), zip.fp)
                # zip.write(file_path)
                sh_make_archive([], zipF=zip)
                files_length = len(multiFile.files)
                multiFile.files.clear()
                await msg.edit(f"Archivo <b>{file_name}</b> Dividido en <b>{files_length}</b> partes de forma existosa", buttons=back_button)
            return
        elif compress_list:
            sh_make_archive(compress_list)
            return
        elif os.path.exists(file_path) and not compress_list:
            await sh_make_archive([file_path])
            return
        else:
            await msg.edit("<b>Es demasiado pequeño para dividirlo!</b>", buttons=[Button.inline("Atras", "m1^zip_menu")])
            return
    except:
        print(traceback.format_exc())
        await msg.edit("(Error Subida) - " + traceback.format_exc())
        return False


async def unzip_file(file_path, msg, dest_path, back_button):
    try:
        file_name = os.path.basename(file_path)
        start = time()
        start_summ = [start]
        d_message = pd_2.format(file_name, "Extrayendo...")
        file_size = 0
        file_size = await get_file_size(file_path) if os.path.isfile(file_path) else get_dir_size(file_path)

        def partial_progress(total_size, original_write, self, buf):
            partial_progress.bytes += buf
            partial_progress.obytes += 1024 * 8  # Hardcoded in zipfile.write
            asyncio.run(progress(partial_progress.bytes, total_size, msg, start, start_summ, d_message))
            return original_write(buf)

        if os.path.splitext(file_path)[1] == ".001":
            splited_path = os.path.split(file_path)
            file_list = []
            for file in os.listdir(splited_path[0]):
                if os.path.splitext(file)[0] == os.path.splitext(splited_path[1])[0] and not file in file_list:
                    file_list.append(os.path.join(splited_path[0], file))
            file_list = sorted(file_list)
            new_file = os.path.join(splited_path[0], os.path.splitext(splited_path[1])[0])
            with open(new_file, "ab") as outfile:
                for file in file_list:
                    with open(file, "rb") as infile:
                        outfile.write(infile.read())
            with ZipFile(new_file, "r") as zip:
                partial_progress.bytes = 0
                partial_progress.obytes = 0
                zip.fp.read = types.MethodType(partial(partial_progress, file_size, zip.fp.read), zip.fp)
                zip.extractall(path=dest_path)
                await msg.edit(f"Archivo <b>{file_name}</b> extraido de forma existosa", buttons=back_button)
                os.remove(new_file)

        else:
            with ZipFile(file_path, "r") as zip:
                partial_progress.bytes = 0
                partial_progress.obytes = 0
                zip.fp.read = types.MethodType(partial(partial_progress, file_size, zip.fp.read), zip.fp)
                zip.extractall(path=dest_path)
                await msg.edit(f"Archivo <b>{file_name}</b> extraido de forma existosa", buttons=back_button)

    except:
        print(traceback.format_exc())
        await msg.edit("(Error Subida) - " + traceback.format_exc())
        return False


async def down_mega(msg, path, text):
    mega = Mega()
    try:
        mega.login()
    except:
        await msg.edit("Error en la cuenta de MEGA")
    try:
        ##GetName##
        REGEXP1 = re.compile(r"mega.[^/]+/folder/([0-z-_]+)#([0-z-_]+)(?:/folder/([0-z-_]+))*")
        f_folder = re.search(REGEXP1, text)
        if not f_folder:
            info = mega.get_public_url_info(text)
            file_name = info["name"]

            pathdir = pathlib.Path(path)
            await msg.edit(pd.format(file_name, "Descargando...", "-"))
            await asyncio.sleep(0)

            start = time()
            d_message = pd_2.format(file_name, "Descargando...📥")
            await mega.download_url(
                text,
                dest_path=str(pathdir),
                dest_filename=file_name,
                progressfunc=lambda d, file, current, total, speed, time, args: progress_mega(current, total, msg, start, d_message),
                args=(),
            )

            await msg.edit(
                pd.format(file_name, "Descargado con Exito", sizeof_fmt(await get_file_size(os.path.join(pathdir, file_name)))),
                buttons=[Button.inline("Menu", "m0^0")],
            )

        else:
            files = megafolder.get_files_from_folder(text)
            await msg.edit(pd_2.format("Mega Folder", "Analizando contenido de la carpeta..."))
            pathdir = pathlib.Path(path)
            start = time()
            for i in range(len(files)):
                d_message = pd_2.format(files[i]["name"], "Descargando...📥    <b>Archivo: {}/{}</b>".format(i + 1, len(files)))
                await mega._download_file_from_folder(
                    None,
                    file_key=files[i]["key"],
                    dest_path=str(pathdir),
                    dest_filename=None,
                    is_public=False,
                    file=None,
                    progressfunc=lambda d, file, current, total, speed, time, args: progress_mega(current, total, msg, start, d_message),
                    args=(),
                    f_data=files[i]["data"],
                )
            await msg.edit(pd.format("Mega Folder", "Contenido de la carpeta descargado exitosamente!", "-"), buttons=[Button.inline("Menu", "m0^0")])
    except:
        await msg.edit(pd.format("-", "Error en la descarga", "-"))
        print(traceback.format_exc())
