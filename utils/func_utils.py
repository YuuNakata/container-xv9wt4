import asyncio
import os
import traceback
from time import time

import pyimgur
from downloader.utils import check_files, get_dir_size, get_file_size, sizeof_fmt
from moviepy.editor import VideoFileClip
from PIL import Image
from telethon import Button
from users.users_temp import get_users_copy, get_users_path

async_tasks = []


def make_button(callback="m0^0"):
    return [Button.inline(" ↼Atras", callback)]


async def manage_tel_connects(func, msg, type_of):
    try:
        loop = asyncio.get_event_loop()
        async_tasks.append(func)
        # load = ["   ", ".  ", ".. ", "..."]
        load = ["◇◇◇", "◈◇◇", "◈◈◇", "◈◈◈", "◇◈◈", "◇◇◈"]
        count = 0
        start_while = time()
        while func != async_tasks[0]:
            now = time()
            index = async_tasks.index(func) + 1
            try:
                if round(now - start_while) >= 5.00:
                    if count == len(load):
                        count = 0
                    await msg.edit(type_of.format(load[count], index))
                    count += 1
                    start_while = time()
            except:
                pass
            await asyncio.sleep(1)
        start_summ = [time()]
        task = loop.create_task(func(time(), start_summ))
        result = loop.run_until_complete(task)

        async_tasks.remove(func)

        return result
    except:
        traceback.print_exc()


async def create_thumb(bot, chat, id, db, back_button):
    async with bot.conversation(chat) as conv:
        name = ""
        try:
            msg = await conv.send_message("Por favor a continuacion envie la foto para añadirla a su coleccion:")
            photo = await conv.get_response()
            await photo.download_media(file="temp_photo.jpg")
            await msg.delete()
        except:
            await msg.edit(
                "Ha demorado mucho en enviar la foto por favor vuelva a intentarlo",
                buttons=back_button,
            )
        try:
            imagen = Image.open("temp_photo.jpg")
            try:
                msg = await conv.send_message("Por favor a continuacion envie el nombre con el que guardar la miniatura:")
                name = await conv.get_response()
                name = str(name.message).replace("|", "")
                await msg.delete()
            except:
                await msg.edit(
                    "Ha demorado mucho en enviar el nombre vuelva a intentarlo",
                    buttons=back_button,
                )
                return
            imagen.save(name + ".jpg")
            try:
                os.remove("temp_photo.jpg")
            except:
                pass
        except:
            await bot.send_message(id, "Por favor mande una foto!", buttons=back_button)
            os.remove("temp_photo.jpg")
            return
        im = pyimgur.Imgur("df4a0942592f83c")
        uploaded_image = im.upload_image(path=name + ".jpg")
        link = str(uploaded_image.link)
        os.remove(name + ".jpg")
        if db.set_thumb_list(id, f"{name}|{link}"):
            await bot.send_message(
                id,
                "Su confuguracion de miniatura ha sido agregada exitosamente!",
                buttons=back_button,
            )
        else:
            await bot.send_message(
                id,
                "Ha ocurrido un error al agregar la miniatura , vuelva a intentarlo o contacte con los admins",
                buttons=back_button,
            )


async def cut_video(file, msg, bot, chat, chat_id, pd, back_button):
    try:
        clip = VideoFileClip(file)
    except:
        print(traceback.format_exc())
        await msg.edit("El archivo seleccionado no es un video por favor seleccione correctamente")
        return
    try:

        async with bot.conversation(chat) as conv:
            main = await conv.send_message(
                f"Escribe el segundo de inicio y la duracion del clip separador por ,\n\nDuracion total del video en segundos: <b>{clip.duration}</b>"
            )
            duracion_raw = await conv.get_response()
            await msg.delete()
            duracion_raw = str(duracion_raw.message)
            await main.delete()
        f, ext = os.path.splitext(file)
        start = None
        msg = await bot.send_message(chat_id, pd.format(os.path.basename(file), "Extrayendo video...", "-"))
        if not "mp4" in ext:
            os.rename(file, f + ".mp4")
        if not start:
            start = time()
        new_name = f + f"({duracion_raw})" + ".mp4"
        splited = duracion_raw.split(",")
        clip = VideoFileClip(f + ".mp4").subclip(float(splited[0]), float(splited[1]))
        clip.write_videofile(new_name)
        now = time() - start
        await msg.edit(
            pd.format(
                os.path.basename(file),
                f"Convertido con Exito - Timeout: <b>%0.2f</b>" % (now),
                sizeof_fmt(await get_file_size(new_name)),
            ),
            buttons=back_button,
        )
    except Exception as e:
        print(traceback.format_exc())
        await msg.edit(pd.format("ERROR!!", e, "-"))


async def get_fileslist(id, chat_id, bot, letter, select_list=[], message=None, current_path=None, zip_size=None):
    if not current_path:
        current_path = get_users_path(id)
    files = check_files(current_path)
    buttons = []
    count = 0
    try:
        if "m2^explorer" in letter or "paste_file" in letter:
            buttons.append(
                [
                    Button.inline("📂", "m2^create_folder"),
                    Button.inline(
                        "🗂" if not get_users_copy(id) else "📋",
                        "m1^copy_file" if not get_users_copy(id) else "m2^paste_file",
                    ),
                    Button.inline("🔙", "m1^explorer^-1"),
                ]
            )
        if files != []:
            if "mark_list" in letter:
                letter = "m3^" + letter
            for f in files:
                file_path = os.path.join(current_path, f)
                name = f + " " + sizeof_fmt(await get_file_size(file_path) if os.path.isfile(file_path) else get_dir_size(file_path))
                if not f in select_list:
                    if len(f) > 35:
                        name = name[:15] + "..." + name[len(f) - 15 :]
                    buttons.append([Button.inline(name, data=letter + f"^{count}")])
                count += 1
            if "mark_list" in letter:
                data2 = letter.split("^")[2]
                files = ""
                back_button = [Button.inline(" ↼Atras", "m0^0")]
                for file in select_list:
                    files += file + "\n"
                if "one_zip" in data2:
                    buttons.append([Button.inline("Finalizar", "m3^build_zip")])
                    buttons.append(back_button)
                    if message != None:
                        await message.edit(
                            "<b>Seleccione los archivos a comprimir:</b>\n\nAgregados:\n{0}".format(files),
                            buttons=buttons,
                        )
                    else:
                        await bot.send_message(
                            chat_id,
                            "<b>Seleccione los archivos a comprimir:</b>\n\nAgregados:\n{0}".format(files),
                            buttons=buttons,
                        )
                    return
                elif "up_mega" in data2:
                    buttons.append([Button.inline("Finalizar", "m3^up_mega")])
                    buttons.append(back_button)
                    if message != None:
                        await message.edit(
                            "<b>Seleccione los archivo a subir:</b>\n\nAgregados:\n{0}".format(files),
                            buttons=buttons,
                        )
                    else:
                        await bot.send_message(
                            chat_id,
                            "<b>Seleccione los archivo a subir:</b>\n\nAgregados:\n{0}".format(files),
                            buttons=buttons,
                        )
                    return
                elif "un_zip" in data2:
                    buttons.append([Button.inline("Finalizar", "m3^un_zip_all")])
                    buttons.append(back_button)
                    if message != None:
                        await message.edit(
                            "<b>Seleccione los archivo a descomprimir:</b>\n\nAgregados:\n{0}".format(files),
                            buttons=buttons,
                        )
                    else:
                        await bot.send_message(
                            chat_id,
                            "<b>Seleccione los archivo a descomprimir:</b>\n\nAgregados:\n{0}".format(files),
                            buttons=buttons,
                        )
                    return
                elif "u" in data2:
                    buttons.append([Button.inline("Finalizar", "m3^upl")])
                    buttons.append(back_button)
                    if message != None:
                        await message.edit(
                            "<b>Seleccione los archivo a subir:</b>\n\n--<i>Recuerde que el archivo debe ser menor a "
                            + os.getenv("PART_SIZE")
                            + "MB , de lo contrario comprimalo en el menu de Comprimir</i>\n\nAgregados:\n{0}".format(files),
                            buttons=buttons,
                        )
                    else:
                        await bot.send_message(
                            chat_id,
                            "<b>Seleccione los archivo a subir:</b>\n\n--<i>Recuerde que el archivo debe ser menor a "
                            + os.getenv("PART_SIZE")
                            + "MB , de lo contrario comprimalo en el menu de Comprimir</i>\n\nAgregados:\n{0}".format(files),
                            buttons=buttons,
                        )
                    return
            buttons.append([Button.inline(" ↼Atras", "m0^0")])
            if "file_d" in letter:
                buttons[len(buttons) - 1] = [Button.inline("Borrar Todo", "m2^file_d_all")]
                buttons.append([Button.inline(" ↼Atras", "m0^0")])
                await bot.send_message(chat_id, f"<b>Seleccione el archivo borrar:</b>", buttons=buttons)
                return
            elif "rnm" in letter:
                await bot.send_message(
                    chat_id,
                    f"<b>Seleccione el archivo para renombrar:</b>",
                    buttons=buttons,
                )
                return
            elif "c_vid" in letter:
                await bot.send_message(chat_id, f"<b>Seleccione el video para cortar:</b>", buttons=buttons)
                return
            elif "copy_file" in letter:
                await bot.send_message(
                    chat_id,
                    f"<b>Seleccione el archivo para copiar:</b>",
                    buttons=buttons,
                )
            elif "share_file" in letter:
                await bot.send_message(
                    chat_id,
                    f"<b>Seleccione el archivo para obtener link:</b>",
                    buttons=buttons,
                )
                return
            elif "explorer" in letter:
                await bot.send_message(
                    chat_id,
                    "<b>Espacio usado: {}</b>".format(sizeof_fmt(get_dir_size(get_users_path(id)))),
                    buttons=buttons,
                )
                return
            elif "paste_file" in letter:
                await bot.send_message(chat_id, "<b>Elija la ubicacion para pegar: </b>", buttons=buttons)
                return
            elif "z" in letter:
                await bot.send_message(
                    chat_id,
                    f"<b>Seleccione el archivo a comprimir:</b>\n\n<b>Tamaño de loz zip:</b> {zip_size} MB\n\n--<i>Si desea cambiar el tamaño utilice el comando /zip</i>",
                    buttons=buttons,
                )

        else:
            buttons.append([Button.inline(" ↼Atras", "m0^0")])
            await bot.send_message(chat_id, "<b>No se encontraron archivos</b>", buttons=buttons)
    except:
        print(traceback.format_exc())
