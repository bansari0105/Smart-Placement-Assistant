class User:
    def __init__(self, uid, email, name):
        self.uid = uid
        self.email = email
        self.name = name

    def to_dict(self):
        return {
            "uid": self.uid,
            "email": self.email,
            "name": self.name
        }
