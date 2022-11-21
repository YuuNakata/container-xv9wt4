import os

from downloader.utils import check_files
from mega_def import mega as mega_d
from telethon import Button, TelegramClient
from users.users_temp import clear_users_selected, get_users_path, get_users_yutulist, set_users_path, set_users_yutulist

from utils import youtube_info
from utils.buttons_markup import Build_Markup
from utils.func_utils import create_thumb, get_fileslist, make_button
from utils.used_strings import pd_2


class CallBack_Helper:
    def __init__(self, bot: TelegramClient, user, chat_id: int, chat=None):
        self.bot = bot
        self.user = user
        self.chat_id = chat_id
        self.chat = chat
        pass

    async def m0(self, data_index, db):
        markup, message = Build_Markup("m0", data_index).build(self.user.username, db, self.chat_id)
        await self.bot.send_message(
            self.chat_id,
            message=message,
            buttons=markup,
        )

    async def m1(self, data_index, db):
        if "rename" == data_index[1]:
            await get_fileslist(self.chat_id, self.chat_id, self.bot, "m2^rnm")
        elif "zip_menu" == data_index[1]:
            await self.bot.send_message(
                self.chat_id,
                "<b>Seleccione la opcion que desee:</b>",
                buttons=[
                    [Button.inline("🗜Dividir en Partes", "m2^fl^z")],
                    [
                        Button.inline(
                            "🗜Comprimir",
                            "m2^fl^mark_list^one_zip",
                        )
                    ],
                    [
                        Button.inline(
                            "🗜Extraer",
                            "m2^fl^mark_list^un_zip",
                        )
                    ],
                    make_button("m0^1"),
                ],
            )
        elif "mega_buttons" == data_index[1]:
            mega = mega_d.Mega()
            mega.login(os.getenv("MEGA_USER"), os.getenv("MEGA_PASSWORD"))
            space = mega.get_storage_space(giga=True)
            buttons = [
                [Button.inline("Subir a Mega", "m2^fl^mark_list^up_mega")],
                [Button.inline("Borrar archivo", "m2^erase_mega")],
                make_button("m0^2"),
            ]
            await self.bot.send_message(
                self.chat_id,
                f"<b>Seleccione la opcion que desea realizar:</b>\n\n<b>Espacio disponible:</b>\nUsado: %0.2f" % (space["used"])
                + " GB de %0.2f" % (space["total"])
                + " GB",
                buttons=buttons,
            )
        elif "cut_video" == data_index[1]:
            await get_fileslist(self.chat_id, self.chat_id, self.bot, "m2^c_vid")
        elif "share_file" == data_index[1]:
            await get_fileslist(self.chat_id, self.chat_id, self.bot, "m2^share_file")
        elif "yutu_searcher" == data_index[1]:
            if len(data_index) == 2:
                try:
                    async with self.bot.conversation(self.chat) as conv:
                        msg = await conv.send_message("Por favor a continuacion escriba lo que desea buscar:")
                        search_string = await conv.get_response()
                        search_string = str(search_string.message)
                        await msg.delete()
                except:
                    await msg.edit(
                        "Ha demorado mucho en enviar el nombre vuelva a intentarlo",
                        buttons=make_button("m1^explorer"),
                    )
                    return
                msg = await self.bot.send_message(self.chat_id, pd_2.format(search_string, "Procesando..."))
                s_urls = await youtube_info.get_search_urls(search_string)
                s_urls = [s_urls[i] for i in range(20)]
                set_users_yutulist(self.chat_id, s_urls)
                index = 0
                await msg.delete()
            else:
                s_urls = get_users_yutulist(self.chat_id)
                index = int(data_index[2])
            yutu_preview = youtube_info.yutu_preview(s_urls[index], index, len(s_urls))
            markup = [
                [
                    Button.inline(
                        "⬅️",
                        "m1^yutu_searcher^" + (str(index - 1) if index > 0 else "0"),
                    ),
                    Button.inline(
                        "➡️",
                        "m1^yutu_searcher^" + (str(index + 1) if index < (len(s_urls) - 1) else str(len(s_urls) - 1)),
                    ),
                ],
                [
                    Button.inline("Descargar/Video", "yt_video^List_" + str(index)),
                    Button.inline(
                        "Descargar/Audio",
                        "yt_video^List_" + str(index) + "^mp3",
                    ),
                ],
                make_button("m0^5"),
            ]
            try:
                await self.bot.send_file(
                    self.chat_id,
                    file=yutu_preview["thumbnail"],
                    caption=yutu_preview["message"],
                    buttons=markup,
                )
            except:
                try:
                    await self.bot.send_file(
                        self.chat_id,
                        file=yutu_preview["thumbnail_sd"],
                        caption=yutu_preview["message"],
                        buttons=markup,
                    )
                except:
                    await self.bot.send_message(self.chat_id, yutu_preview["message"], buttons=markup)
        elif "copy_file" == data_index[1]:
            await get_fileslist(
                self.chat_id,
                self.chat_id,
                self.bot,
                "m2^copy_file",
                current_path=get_users_path(self.chat_id),
            )
        elif "explorer" == data_index[1]:
            current_path = get_users_path(self.chat_id)
            if len(data_index) == 2:
                await get_fileslist(self.chat_id, self.chat_id, self.bot, "m2^explorer", current_path=current_path)
            elif data_index[2] == "-1":
                back_path = "/"
                splited = str(current_path).split("/")
                if str(os.path.basename(current_path)) != str(self.chat_id):
                    for i in range(len(splited)):
                        if i != len(splited) - 1:
                            back_path = os.path.join(back_path, splited[i])
                    set_users_path(self.chat_id, back_path)
                    current_path = back_path
                await get_fileslist(self.chat_id, self.chat_id, self.bot, "m2^explorer", current_path=current_path)
        elif "f_delete" == data_index[1]:
            await get_fileslist(self.chat_id, self.chat_id, self.bot, "m2^file_d")
        elif "min_create" == data_index[1]:
            if db.get_u(self.chat_id):
                await create_thumb(self.bot, self.chat, self.chat_id, db, make_button("m0^4"))
        elif "min_get" == data_index[1] or "min_delete" == data_index[1]:
            if db.get_u(self.chat_id):
                thumbs = db.get_thumb_list(self.chat_id)
                markup = []
                back_button = [Button.inline(" ↼Atras", "m0^4")]
                if len(thumbs) > 1:
                    for t in thumbs.split(os.linesep):
                        if len(t) > 1 and not "User.thumb_list" in t:
                            t_split = t.split("|")
                            if "min_get" == data_index[1]:
                                markup.append(
                                    [
                                        Button.inline(
                                            t_split[0],
                                            "m2^min_see^" + t_split[1],
                                        )
                                    ]
                                )
                            else:
                                markup.append(
                                    [
                                        Button.inline(
                                            t_split[0],
                                            "m2^min_delete^" + t_split[1],
                                        )
                                    ]
                                )
                    markup.append(back_button)
                    await self.bot.send_message(
                        self.chat_id,
                        "<b>Lista de miniaturas creadas:</b>",
                        buttons=markup,
                    )
                else:
                    await self.bot.send_message(self.chat_id, "<b>No se encontraron miniaturas</b>", buttons=back_button)

    async def m2(self, data_index, db):
        id = self.chat_id
        chat_id = self.chat_id
        if "fl" == data_index[1]:
            clear_users_selected(id)
            action = data_index[2] + ("^" + data_index[3] if len(data_index) > 3 else "")
            await get_fileslist(id, self.chat_id, self.bot, action, zip_size=db.get_zips(id) if "z" in action else None)
        elif "rnm" == data_index[1]:
            file_id = int(data_index[2])
            files = check_files(get_users_path(id))
            file = files[file_id]
            arch_old = os.path.join(get_users_path(id), file)
            async with self.bot.conversation(self.chat) as conv:
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
            await self.bot.send_message(
                self.chat_id,
                f"Archivo <b>{f2}</b> renombrado a <b>{f}</b> con exito-tama",
                buttons=make_button("m0^1"),
            )
        elif "erase_mega" == data_index[1]:
            mega = mega_d.Mega()
            mega.login(os.getenv("MEGA_USER"), os.getenv("MEGA_PASSWORD"))
            await get_megafiles(self.chat_id, self.bot, mega)

        elif "min_see" == data_index[1]:
            link = data_index[2]
            await self.bot.send_file(
                self.chat_id,
                file=link,
                caption="",
                buttons=[Button.inline(" ↼Atras", "m0^4")],
            )

        elif "min_set_v1" == data_index[1]:
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
                        await self.bot.send_file(
                            self.chat_id,
                            file=default_thumb,
                            caption="<b>Miniatura Actual  ⤴️\n\nElije la miniatura por defecto:</b>",
                            buttons=markup,
                        )
                    else:
                        await self.bot.send_message(
                            self.chat_id,
                            "<b>Elije la miniatura por defecto:</b>",
                            buttons=markup,
                        )
        elif "min_set_v2" == data_index[1]:
            link = data_index[2]
            value = link == "delete"
            if db.set_thumb_default(id, link, value) and not value:
                await self.bot.send_file(
                    self.chat_id,
                    file=link,
                    caption="Miniatura por defecto guardada!",
                    buttons=make_button("m0^2"),
                )
            else:
                await self.bot.send_message(
                    self.chat_id,
                    "Miniatura por defecto eliminada!",
                    buttons=make_button("m0^2"),
                )

        elif "min_delete" == data_index[1]:
            link = data_index[2]
            if db.get_thumb_default(id) == link:
                if db.delete_thumb_list(id, link) and db.set_thumb_default(id, "", True):
                    await self.bot.send_message(
                        self.chat_id,
                        "Miniatura borrada con exito!",
                        buttons=make_button("m0^4"),
                    )
                else:
                    await self.bot.send_message(
                        self.chat_id,
                        "Error al borrar miniatura",
                        buttons=make_button("m0^4"),
                    )
            else:
                if db.delete_thumb_list(id, link):
                    await self.bot.send_message(
                        self.chat_id,
                        "Miniatura borrada con exito!",
                        buttons=make_button("m0^4"),
                    )
                else:
                    await self.bot.send_message(
                        self.chat_id,
                        "Error al borrar miniatura",
                        buttons=make_button("m0^4"),
                    )

        elif "c_vid" == data_index[1]:
            file_id = int(data_index[2])
            files = check_files(get_users_path(id))
            file = files[file_id]
            msg = await self.bot.send_message(self.chat_id, pd.format(os.path.basename(file), "Analizando", "-"))
            await cut_video(os.path.join(get_users_path(id), file), msg, self.bot, self.chat, self.chat_id, pd, make_button("m0^1"))
        elif "share_file" == data_index[1]:
            file_id = int(data_index[2])
            files = check_files(get_users_path(id))
            file = files[file_id]
            file_path = os.path.join(get_users_path(id), file)
            if os.path.isfile(file_path):
                msg = await self.bot.send_message(chat_id, pd.format(file, "Compartiendo...", "-"))
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
                msg = await self.bot.send_message(chat_id, pd.format("ERROR", "Aun no disponible compartir carpetas", "-"))
        elif "copy_file" == data_index[1]:
            file_id = int(data_index[2])
            current_path = get_users_path(id)
            files = check_files(current_path)
            file = files[file_id]
            set_users_copy(id, os.path.join(current_path, file))
            await get_fileslist(id, self.chat_id, self.bot, "m2^explorer", current_path=current_path)
        elif "paste_file" == data_index[1]:
            current_path = get_users_path(id)
            src = get_users_copy(id)
            msg = await self.bot.send_message(
                self.chat_id,
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
            await get_fileslist(id, self.chat_id, self.bot, "m2^explorer", current_path=current_path)

        elif "create_folder" == data_index[1]:
            current_path = get_users_path(id)

            try:
                async with self.bot.conversation(chat) as conv:
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
            await get_fileslist(id, self.chat_id, self.bot, "m2^explorer", current_path=current_path)

        elif "explorer" == data_index[1]:
            file_id = int(data_index[2])
            current_path = get_users_path(id)

            files = check_files(current_path)
            file = files[file_id]
            file_path = os.path.join(current_path, file)
            cover = None
            if os.path.isfile(file_path):
                size = sizeof_fmt(await get_file_size(file_path))
                val = magic.from_file(file_path)
                mime = magic.from_file(file_path, mime=True)
                msg = await self.bot.send_message(
                    self.chat_id,
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
                    msg = await self.bot.send_file(
                        self.chat_id,
                        file=cover,
                        caption="<b>Nombre:</b> {}\n<b>Tamaño:</b> {}\n<b>Tipo:</b> {}\n<b>Info:</b> {}".format(file, size, mime, val),
                        buttons=make_button("m1^explorer"),
                    )
                else:
                    msg = await self.bot.send_message(
                        self.chat_id,
                        "<b>Nombre:</b> {}\n<b>Tamaño:</b> {}\n<b>Tipo:</b> {}\n<b>Info:</b> {}".format(file, size, mime, val),
                        buttons=make_button("m1^explorer"),
                    )

            else:
                set_users_path(id, file_path)
                await get_fileslist(id, self.chat_id, self.bot, "m2^explorer", current_path=file_path)

        elif "file_d" == data_index[1]:
            file_id = int(data_index[2])
            files = check_files(get_users_path(id))
            file = files[file_id]
            try:
                file_path = os.path.join(get_users_path(id), file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                else:
                    shutil.rmtree(file_path)
            except Exception as e:
                await self.bot.send_message(chat_id, e)
            await self.bot.send_message(chat_id, f"Archivo <b>{file}</b> borrado con exito")
            await get_fileslist(id, self.chat_id, self.bot, "m2^file_d")
        elif "file_d_all" == data_index[1]:
            files = check_files(get_users_path(id))
            try:
                for file in files:
                    file_path = os.path.join(get_users_path(id), file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    else:
                        shutil.rmtree(file_path)
            except Exception as e:
                await self.bot.send_message(chat_id, e)
            await self.bot.send_message(
                self.chat_id,
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
                    message = self.bot.iter_messages(chat, ids=reply_id)
                    async for m in message:
                        CLEANR = re.compile("<.*?>")
                        url = re.sub(CLEANR, "", m.text)
                else:
                    url = get_users_yutulist(id)[int(splited.split("_")[1])]
                    reply_id = splited
                markup = []
                msg = await self.bot.send_message(
                    self.chat_id,
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
                            elif d["audio_ext"] != "none" and "filesize" in d and d["video_ext"] == "none" and d["height"] == None and "^mp3" in data:
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
                msg = await self.bot.send_message(chat_id, "<b>Conectando con la cuenta...</b>")
                mega.login(os.getenv("MEGA_USER"), os.getenv("MEGA_PASSWORD"))
                await msg.edit("<b>Borrando archivo...</b>")
                mega.destroy(file_id)
                await get_megafiles(chat_id, self.bot, mega)
            except:
                traceback.print_exc()

        elif "df^" in data:
            # file_id=int(data.split('^')[1])
            splited = data.split("^")[1]

            if not "List_" in splited:
                file_id = int(splited)
                link = None
                message = self.bot.iter_messages(chat, ids=file_id)
            else:
                link = get_users_yutulist(id)[int(splited.split("_")[1])]
                file_id = None
                message = None
            download = downloader.Downloader(
                file_id,
                self.bot,
                message,
                chat,
                self.chat_id,
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
            msg = await self.bot.send_message(chat_id, pd.format(file, "Comprimiendo...🗜", sizeof_fmt(size)))
            await zip_file(os.path.join(get_users_path(id), file), db, msg, id, back_button=make_button("m0^1"))
