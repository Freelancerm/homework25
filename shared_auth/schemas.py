from ninja import Schema


# Роутер для аутентифікації
class LogIn(Schema):
    username: str
    password: str


class TokenOut(Schema):
    token: str
