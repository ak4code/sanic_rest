import base64

from argon2.exceptions import VerifyMismatchError
from sanic import Request
from sanic.response import json
from argon2 import PasswordHasher
from tortoise.exceptions import DoesNotExist

from .exceptions import CredentialsError, AuthorizationError
from .models import User, Scope
from .helpers import ActivationCodeGenerator

acg = ActivationCodeGenerator()
password_hasher = PasswordHasher()


async def register(request: Request):
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    if not username or not password:
        return json({"error": "Missing username or password."}, status=400)

    try:
        scope = await Scope.filter(name="user").get()
    except DoesNotExist:
        scope = await Scope.create(
            name="user"
        )

    user = await User.create(
        username=username,
        password=password_hasher.hash(password),
        active=False,
    )

    await user.scopes.add(scope)

    code = acg.generate_code(user_id=user.id)
    url = request.app.url_for('activation', code=code, _external=True)

    return json({"activation_link": url})


async def activation(request: Request, code: str):
    user_id = acg.get_code_value(code)
    user = await User.get(id=user_id)
    if not user.active:
        await user.activate()
        return json({"message": "User has been activated. Please login."})
    return json({"message": "User is already activated. Please login."})


async def authenticate(request: Request):
    if request.headers.get("Authorization"):
        authorization_type, credentials = request.headers.get("Authorization").split()
        if authorization_type == "Basic":
            username, password = (
                base64.b64decode(credentials).decode().split(":")
            )
        else:
            raise CredentialsError("Invalid authorization type.")
    else:
        if request.json:
            username = request.json.get("username", None)
            password = request.json.get("password", None)
            if not username or not password:
                raise CredentialsError("Credentials not provided.")
        else:
            raise CredentialsError("Credentials not provided.")

    user = await User.get(username=username)

    if not user.active:
        raise AuthorizationError('User is not activated!')

    try:
        password_hasher.verify(user.password, password)
        if password_hasher.check_needs_rehash(user.password):
            user.password = password_hasher.hash(password)
            await user.save(update_fields=["password"])
        return await user.json()
    except VerifyMismatchError:
        raise CredentialsError("Incorrect password.", 401)
