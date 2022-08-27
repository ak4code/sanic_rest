from tortoise.models import Model
from tortoise import fields


class BaseModel(Model):
    id: int = fields.IntField(pk=True)

    class Meta:
        abstract = True


class User(BaseModel):
    username: str = fields.CharField(unique=True, max_length=255)
    password: str = fields.CharField(max_length=255)
    active: bool = fields.BooleanField(default=False)
    scopes: fields.ManyToManyRelation["Scope"] = fields.ManyToManyField('models.Scope', through='user_scope')

    async def activate(self):
        self.active = True
        await self.save(update_fields=["active"])

    async def deactivate(self):
        self.active = False
        await self.save(update_fields=["active"])

    async def json(self) -> dict:
        await self.fetch_related('scopes')
        return {
            "id": self.id,
            "username": self.username,
            "active": self.active,
            "scopes": [scope.name for scope in self.scopes]
        }


class Product(BaseModel):
    name: str = fields.CharField(max_length=255)
    description: str = fields.TextField()
    price: int = fields.IntField()

    def json(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price
        }


class Bill(Model):
    id: int = fields.IntField(pk=True, generated=False)
    balance: int = fields.IntField(default=0)
    user: fields.ForeignKeyRelation['User'] = fields.ForeignKeyField('models.User', related_name='bills')

    def json(self) -> dict:
        return {
            "id": self.id,
            "balance": self.balance
        }


class Transaction(Model):
    id: int = fields.IntField(pk=True, generated=False)
    amount: int = fields.IntField()
    bill: fields.ForeignKeyRelation['Bill'] = fields.ForeignKeyField('models.Bill', related_name='transactions')

    def json(self) -> dict:
        return {
            "id": self.id,
            "amount": self.amount
        }


class Scope(BaseModel):
    name: str = fields.CharField(max_length=255)

    def __str__(self):
        return self.name
