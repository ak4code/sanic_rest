from sanic import Request
from sanic.response import json
from sanic_jwt import inject_user, protected
from tortoise.exceptions import DoesNotExist

from .exceptions import InvalidSignature
from .helpers import verify_signature
from .models import Product, Bill, Transaction


async def payment_webhook(request: Request):
    signature = request.json.get('signature', None)
    transaction_id = request.json.get('transaction_id', None)
    user_id = request.json.get('user_id', None)
    bill_id = request.json.get('bill_id', None)
    amount = request.json.get('amount', None)
    valid_sign = verify_signature(
        signature,
        private_key=request.app.config.PRIVATE_KEY,
        transaction_id=transaction_id,
        user_id=user_id,
        bill_id=bill_id,
        amount=amount,
    )
    if valid_sign:
        try:
            bill = await Bill.filter(id=bill_id, user_id=user_id).get()
        except DoesNotExist:
            bill = await Bill.create(id=bill_id, user_id=user_id)
        transaction = await Transaction.create(id=transaction_id, bill_id=bill.id, amount=amount)
        bill.balance += amount
        await bill.save(update_fields=['balance'])
        return json({
            "message": "Payment successful",
            "bill": bill.json(),
            "transaction": transaction.json()
        })

    raise InvalidSignature


@protected()
@inject_user()
async def buy_product_webhook(request: Request, product_id: int, user: dict):
    product = await Product.filter(id=product_id).get()
    try:
        bill = await Bill.filter(balance__gte=product.price, user_id=user.get('id')).first()
        bill.balance -= product.price
        await bill.save(update_fields=['balance'])
        return json({
            "message": f"You buy {product.name} at {product.price}$",
            "product": product.json(),
            "bill": bill.json()
        })
    except DoesNotExist:
        return json({"message": "Insufficient funds."})


