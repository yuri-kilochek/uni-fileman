# тут описаны сообщения, которыми обмениваются клиент и сервер

# сообщения от сервера к клиенту

# авторизовать
class Authorize:
    pass


# деавторизовать
class Deauthorize:
    pass


# установить список файлов
class SetAll:
    def __init__(self, files):
        self.files = files


# изменить файл
class Change:
    def __init__(self, old_name, new_name):
        self.old_name = old_name
        self.new_name = new_name


# убрать файл из списка
class Forget:
    def __init__(self, file):
        self.file = file


# ошибка
class Error:
    def __init__(self, description):
        self.description = description


# сообщения от клиента к серверу

# войти
class Login:
    def __init__(self, username, password):
        self.username = username
        self.password = password


# выйти
class Logout:
    pass


# найти
class Search:
    def __init__(self, pattern):
        self.pattern = pattern


# переименовать
class Rename:
    def __init__(self, old_name, new_name):
        self.old_name = old_name
        self.new_name = new_name


# удалить
class Delete:
    def __init__(self, name):
        self.name = name


# собираюсь отключаться
class AboutToDisconnect:
    pass