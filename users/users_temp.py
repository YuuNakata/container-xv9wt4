import os

users_list = []
path = os.getcwd() + "/UsersData/{0}/"


class User_Temp:
    def __init__(self, id, select_list, path, copy_list, yutu_list, callback_class):
        self.id = id
        self.select_list = select_list
        self.path = path
        self.copy_list = copy_list
        self.yutu_list = yutu_list
        self.callback_class = callback_class
        pass


def check_id(id) -> User_Temp:
    for user in users_list:
        user: User_Temp
        if str(id) in str(user.id):
            return user
    return False


def set_users_callback(id, callback):
    user = check_id(id)
    if user:
        user.callback_class = callback
    else:
        users_list.append(User_Temp(id, [], path, None, [], callback))


def get_users_callback(id):
    user = check_id(id)
    if user:
        return user.callback_class
    return False


def set_users_path(id, path):
    user = check_id(id)
    if user:
        user.path = path
    else:
        users_list.append(User_Temp(id, [], path, None, [], None))


def get_users_path(id):
    user = check_id(id)
    if user:
        return user.path
    return path.format(id)


def set_users_path(id, path):
    user = check_id(id)
    if user:
        user.path = path
    else:
        users_list.append(User_Temp(id, [], path, None, [], None))


def get_users_path(id):
    user = check_id(id)
    if user:
        return user.path
    return path.format(id)


def set_users_copy(id, copy):
    user = check_id(id)
    if user:
        user.copy_list = copy
    else:
        users_list.append(User_Temp(id, [], get_users_path(id), copy, [], None))


def get_users_copy(id):
    user = check_id(id)
    if user:
        return user.copy_list
    return None


def set_users_yutulist(id, yutulist):
    user = check_id(id)
    if user:
        user.yutu_list = yutulist
    else:
        users_list.append(User_Temp(id, [], get_users_path(id), None, yutulist, None))


def get_users_yutulist(id):
    user = check_id(id)
    if user:
        return user.yutu_list
    return None


def set_users_selected(id, elements):
    user = check_id(id)
    if user:
        user.select_list = elements
    else:
        users_list.append(User_Temp(id, elements, get_users_path(id), None, [], None))


def get_users_selected(id):
    user = check_id(id)
    if user:
        return user.select_list
    return []


def clear_users_selected(id):
    user = check_id(id)
    if user:
        user.select_list = []
