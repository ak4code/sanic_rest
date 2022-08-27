from sanic import Sanic
from .auth import register, activation
from .webhooks import payment_webhook, buy_product_webhook
from .views import (
    UsersView,
    UserDetailView,
    UserBillsView,
    UserTransactionView,
    ProductsView,
    ProductDetailView,
)


def init_routes(app: Sanic) -> None:
    app.add_route(UsersView.as_view(), '/users')
    app.add_route(UserDetailView.as_view(), '/users/<user_id:int>')
    app.add_route(UserBillsView.as_view(), '/users/<user_id:int>/bills')
    app.add_route(UserTransactionView.as_view(), '/users/<user_id:int>/transactions')
    app.add_route(ProductsView.as_view(), '/products')
    app.add_route(ProductDetailView.as_view(), '/products/<product_id:int>')
    app.add_route(register, '/auth/register', methods=["POST"])
    app.add_route(activation, '/auth/activation/<code:str>')
    app.add_route(buy_product_webhook, '/products/<product_id:int>/buy', methods=["POST"])
    app.add_route(payment_webhook, '/payment/webhook', methods=["POST"])
