class Authorize:
    pass


class Deauthorize:
    pass


class SetAll:
    def __init__(self, files):
        self.files = files


class Change:
    def __init__(self, old_name, new_name):
        self.old_name = old_name
        self.new_name = new_name


class Forget:
    def __init__(self, file):
        self.file = file


class Error:
    def __init__(self, description):
        self.description = description


class Login:
    def __init__(self, username, password):
        self.username = username
        self.password = password


class Logout:
    pass


class Search:
    def __init__(self, pattern):
        self.pattern = pattern


class Rename:
    def __init__(self, old_name, new_name):
        self.old_name = old_name
        self.new_name = new_name


class Delete:
    def __init__(self, name):
        self.name = name
