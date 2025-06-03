import decimal
import uuid

import factory
import factory.django
import faker

import credit_charge.consts
import credit_charge.models

FAKE = faker.Faker()  # for Persian (Farsi) fake data


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = credit_charge.models.User

    phone_number = factory.LazyAttribute(lambda _: f"+98{FAKE.unique.random_int(9000000000, 9999999999)}")
    balance = decimal.Decimal("0")
    is_seller = factory.LazyAttribute(lambda _: FAKE.boolean())


class ChargeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = credit_charge.models.Charge

    user = factory.SubFactory(UserFactory)
    status = credit_charge.consts.TransactionStatus.WAITING
    amount = factory.LazyAttribute(lambda _: decimal.Decimal(FAKE.random_int(min=1000, max=500_000)))
    transaction_id = factory.LazyFunction(uuid.uuid4)


class UserTransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = credit_charge.models.UserTransaction

    seller = factory.SubFactory(UserFactory, is_seller=True)
    receiver_user = factory.SubFactory(UserFactory, is_seller=False)
    amount = factory.LazyAttribute(lambda _: decimal.Decimal(FAKE.random_int(min=1000, max=500_000)))
    transaction_id = factory.LazyFunction(uuid.uuid4)
    status = credit_charge.consts.TransactionStatus.WAITING
    description = None
