from datetime import datetime, timedelta

from argon2 import PasswordHasher
from cryptography import fernet as fn
from sanic import Sanic, Request
from tortoise.exceptions import DoesNotExist

from .exceptions import ActivationCodeError
from .models import Scope, User
from Crypto.Hash import SHA1

password_hasher = PasswordHasher()


class ActivationCodeGenerator:
    FERNET_KEY = 'pvV6Qkb7YGCn-c_HBwCuXTaM8_VWE8owFj3S9yGkMs0='
    DATE_FORMAT = '%d.%m.%Y %H:%M:%S'
    EXPIRATION_DAYS = 3

    fernet = fn.Fernet(FERNET_KEY)

    def _get_time(self) -> str:
        return datetime.now().strftime(self.DATE_FORMAT)

    def _parse_time(self, d: str) -> datetime:
        return datetime.strptime(d, self.DATE_FORMAT)

    def generate_code(self, user_id: int) -> str:
        full_text = str(user_id) + '&' + self._get_time()
        code = self.fernet.encrypt(full_text.encode())
        return code.decode()

    def get_code_value(self, code: str) -> int | None:
        try:
            value = self.fernet.decrypt(code.encode())
            user_id, code_created = (value.decode().split('&'))
            if self._parse_time(code_created) + timedelta(self.EXPIRATION_DAYS) < datetime.now():
                raise ActivationCodeError("Activation code has expired!")
        except fn.InvalidToken:
            raise ActivationCodeError("Invalid activation code!")

        return int(user_id)


def create_admin_user(app: Sanic) -> None:
    @app.listener("before_server_start")
    async def generate(app, loop):
        try:
            scope = await Scope.filter(name='admin').get()
        except DoesNotExist:
            scope = await Scope.create(name='admin')
        try:
            user = await User.filter(username='admin').get()
            await user.fetch_related("scopes")
            if scope not in user.scopes:
                await user.scopes.add(scope)
        except DoesNotExist:
            user = await User.create(
                username="admin",
                email=app.config.ADMIN_USERNAME,
                password=password_hasher.hash(app.config.ADMIN_PASSWORD),
                active=True,
            )
            await user.scopes.add(scope)


async def scope_extender(user: dict, *args, **kwargs) -> list:
    return user['scopes']


async def retrieve_user(request: Request, payload: dict, *args, **kwargs) -> dict | None:
    if payload:
        id = payload.get('id', None)
        user = await User.filter(id=id).get()
        return await user.json()
    else:
        return None


def verify_signature(signature, **kwargs) -> bool:
    gen_sign = SHA1.new(
        f'{kwargs.get("private_key")}:{kwargs.get("transaction_id")}:'
        f'{kwargs.get("user_id")}:{kwargs.get("bill_id")}:'
        f'{kwargs.get("amount")}'.encode()
    ).hexdigest()
    return signature == gen_sign
