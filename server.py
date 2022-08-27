from sanic_jwt import Initialize
from tortoise.contrib.sanic import register_tortoise
from sanic import Sanic
from api.auth import authenticate
from api.helpers import create_admin_user, scope_extender, retrieve_user
from api.routing import init_routes

app = Sanic("test_server")
app.config.PRIVATE_KEY = 'secret'
app.config.SERVER_NAME = 'localhost:8000'
app.config.ADMIN_USERNAME = 'admin'
app.config.ADMIN_PASSWORD = 'hackme'

init_routes(app)

Initialize(
    app,
    authenticate=authenticate,
    retrieve_user=retrieve_user,
    user_id='id',
    add_scopes_to_payload=scope_extender,
    path_to_authenticate='/login',
)

register_tortoise(
    app,
    db_url="asyncpg://sanic:hackme@db:5432/sanic_db",
    modules={"models": ["api.models"]},
    generate_schemas=True,
)
create_admin_user(app)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, dev=True)
