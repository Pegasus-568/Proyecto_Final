from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, username, password, rol):
        self.id = id
        self.username = username
        self.password = password
        self.rol = rol

    def get_id(self):
        return str(self.id)

    def is_admin(self):
        return self.rol == 'admin'