from argon2 import PasswordHasher
from sanic import Request
from sanic.views import HTTPMethodView
from sanic.response import json
from sanic_jwt import scoped, protected, inject_user
from tortoise.exceptions import DoesNotExist

from .exceptions import AuthorizationError, NotFoundError
from .models import User, Scope, Product, Bill, Transaction

password_hasher = PasswordHasher()


class UsersView(HTTPMethodView):
    decorators = [protected(), scoped('admin')]

    async def get(self, request: Request):
        users = await User.all()
        return json([await user.json() for user in users])

    async def post(self, request: Request):
        data = request.json
        try:
            scope = await Scope.filter(name='user').get()
        except DoesNotExist:
            scope = await Scope.create(name='user')
        user = await User.create(
            username=data.get('username'),
            password=password_hasher.hash(data.get('password')),
            active=True,
        )
        await user.scopes.add(scope)
        return json(await user.json(), status=201)


class UserDetailView(HTTPMethodView):
    decorators = [protected(), scoped('admin')]

    async def get(self, request: Request, user_id: int):
        try:
            user = await User.filter(id=user_id).get()
        except DoesNotExist:
            raise NotFoundError("User not found!")
        return json(await user.json())

    async def put(self, request: Request, user_id: int):
        data = request.json
        user = await User.filter(id=user_id).get()
        await user.update_from_dict(data)
        await user.save(update_fields=['username', 'active'])
        return json(await user.json())


class UserBillsView(HTTPMethodView):
    decorators = [protected(), scoped(['admin', 'user'], False)]

    @inject_user()
    async def get(self, request: Request, user_id: int, user: dict):
        if user_id == user['id'] or 'admin' in user['scopes']:
            bills = await Bill.filter(user_id=user_id)
            return json({
                "total_balance": sum([bill.balance for bill in bills]),
                "bills": [bill.json() for bill in bills]
            })
        raise AuthorizationError("You do not have access")


class UserTransactionView(UserBillsView):

    @inject_user()
    async def get(self, request: Request, user_id: int, user: dict):
        if user_id == user['id'] or 'admin' in user['scopes']:
            transactions = await Transaction.filter(bill__user_id=user_id)
            return json([transaction.json() for transaction in transactions])
        raise AuthorizationError("You do not have access")


class ProductsView(HTTPMethodView):
    decorators = [protected()]

    @scoped(['admin', 'user'], False)
    async def get(self, request: Request):
        products = await Product.all()
        return json([product.json() for product in products])

    @scoped('admin')
    async def post(self, request: Request):
        data = request.json
        product = await Product.create(
            name=data.get('name'),
            description=data.get('description'),
            price=data.get('price'),
        )
        return json(product.json())


class ProductDetailView(HTTPMethodView):
    decorators = [protected()]

    @scoped(['admin', 'user'], False)
    async def get(self, request: Request, product_id: int):
        try:
            product = await Product.filter(id=product_id).get()
        except DoesNotExist:
            raise NotFoundError("Product not found!")
        return json(product.json())

    @scoped('admin')
    async def put(self, request: Request, product_id: int):
        data = request.json
        product = await Product.filter(id=product_id).get()
        await product.update_from_dict(data)
        await product.save(update_fields=['name', 'description', 'price'])
        return json(product.json())

    @scoped('admin')
    async def delete(self, request: Request, product_id: int):
        await Product.filter(id=product_id).delete()
        return json({"message": "Product deleted"})
