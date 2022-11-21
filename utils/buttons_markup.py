from telethon import Button


def make_button(callback="m0^0"):
    return [Button.inline(" ↼Atras", callback)]


callback_dict = {
    "m0": {
        "0": [
            [
                [Button.inline("👤Perfil", "m0^3")],
                [Button.inline("👓Menu de Exploracion", "m0^5")],
                [Button.inline("🎛Menu de Subidas", "m0^2")],
                [Button.inline("💾Menu de Archivos", "m0^1")],
            ],
            "<b>Menu Principal</b>\n\nQue desea hacer?:",
        ],
        "1": [
            [
                [Button.inline("🔎Explorar", "m1^explorer")],
                [Button.inline("🗜Comprimir/Extraer", "m1^zip_menu")],
                [Button.inline("📝Rename", "m1^rename")],
                [Button.inline("✂️Cut Video", "m1^cut_video")],
                [Button.inline("🗑Borrar Archivos", "m1^f_delete")],
                make_button(),
            ],
            "<b>💾Menu de archivos descargados</b>\n\nQue desea hacer?:",
        ],
        "2": [
            [
                [Button.inline("📤Subir", "m2^fl^mark_list^u")],
                [Button.inline("🔗Obtener Link", "m1^share_file")],
                [Button.inline("🌁Establecer Miniatura", "m2^min_set_v1")],
                [Button.inline("📮Mega", "m1^mega_buttons")],
                make_button(),
            ],
            "<b>🎛Menu de subidas</b>\n\nQue desea hacer?:",
        ],
        "3": [
            [
                [Button.inline("▶️Deshabilitar descarga automatica (OFF)", "m0^3")],
                [Button.inline("🏞Menu de miniaturas", "m0^4")],
                make_button(),
            ],
            "<b>👤{}</b>\n\n➤Descargas automaticas habilitas : {}\n➤Tamaño de las partes 7z: {}",
        ],
        "4": [
            [
                [Button.inline("▷Crear Miniatura", "m1^min_create")],
                [Button.inline("▷Ver miniaturas", "m1^min_get")],
                [Button.inline("▷Eliminar miniatura", "m1^min_delete")],
                make_button("m0^3"),
            ],
            "<b>👤{}</b>\n\n➤Descargas automaticas habilitas : {}\n➤Tamaño de las partes 7z: {}",
        ],
        "5": [
            [
                [Button.inline("🎥Youtube Searcher", "m1^yutu_searcher")],
                make_button(),
            ],
            "<b>Menu de Exploracion:\n</b>",
        ],
    }
}


class Build_Markup:
    def __init__(self, menu_index, data_index):
        self.menu_index = menu_index
        self.data_index = data_index
        pass

    def build(self, username, db, id):
        if self.data_index in callback_dict[self.menu_index].keys():
            if self.data_index == "3" or self.data_index == "4":
                return callback_dict[self.menu_index][self.data_index][0], callback_dict[self.menu_index][self.data_index][1].format(
                    username, "<b>Si</b>", db.get_zips(id)
                )
            return callback_dict[self.menu_index][self.data_index][0], callback_dict[self.menu_index][self.data_index][1]
