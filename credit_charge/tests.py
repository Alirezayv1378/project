import decimal
import random

from django import test
from django.db import models

import credit_charge.consts
import credit_charge.models
import credit_charge.services


def check_user_balance(user: credit_charge.models.User) -> None:
    try:
        total_charge = credit_charge.models.Charge.objects.filter(user=user).aggregate(total=models.Sum("amount"))
        total_expense = credit_charge.models.UserTransaction.objects.filter(
            seller=user,
            status=credit_charge.consts.TransactionStatus.CONFIRMED,
        ).aggregate(
            total=models.Sum("amount"),
        )
        diff = total_charge["total"] - total_expense["total"]
        if diff < 0:
            raise credit_charge.exceptions.UserBalanceCheckError(user=user, diff=diff)
    except credit_charge.models.Charge.DoesNotExist:
        pass
    except credit_charge.models.UserTransaction.DoesNotExist:
        pass


class TestServices(test.TestCase):
    fixtures = ["data.json"]

    def setUp(self):
        self.seller_1 = credit_charge.models.User.objects.get(phone_number="+989097907343")
        self.seller_2 = credit_charge.models.User.objects.get(phone_number="+989203016403")

    def test_check_fixture_data(self):
        self.assertEqual(credit_charge.models.User.objects.count(), 100)
        self.assertEqual(credit_charge.models.User.objects.filter(is_seller=True).count(), 6)
        self.assertEqual(credit_charge.models.Charge.objects.count(), 14)
        self.assertEqual(credit_charge.models.UserTransaction.objects.count(), 0)

        self.assertEqual(self.seller_1.balance, decimal.Decimal("1_555_000"))
        self.assertEqual(self.seller_2.balance, decimal.Decimal("2_280_000"))

    def test_check_sellers_balance_case_no_transaction_created(self):
        seller_1_total_charge = credit_charge.models.Charge.objects.filter(
            user=self.seller_1,
            status=credit_charge.consts.TransactionStatus.CONFIRMED,
        ).aggregate(total=models.Sum("amount"))
        self.assertEqual(self.seller_1.balance, seller_1_total_charge["total"])

        seller_2_total_charge = credit_charge.models.Charge.objects.filter(
            user=self.seller_2,
            status=credit_charge.consts.TransactionStatus.CONFIRMED,
        ).aggregate(total=models.Sum("amount"))
        self.assertEqual(self.seller_2.balance, seller_2_total_charge["total"])

    def test_sellers_balance_case_with_transaction_created(self):
        seller_1_initial_balance = self.seller_1.balance
        seller_2_initial_balance = self.seller_2.balance

        customers = credit_charge.models.User.objects.filter(is_seller=False)
        seller_1_total_expense = decimal.Decimal("0")
        seller_2_total_expense = decimal.Decimal("0")

        for _ in range(1000):
            customer = random.choice(list(customers))  # noqa:S311
            seller = random.choice([self.seller_1, self.seller_2])  # noqa:S311
            amount = decimal.Decimal(random.randint(100, 1000))  # noqa:S311

            credit_charge.services.create_transaction(
                seller_phone_number=seller.phone_number,
                receiver_phone_number=customer.phone_number,
                amount=amount,
            )

            if seller == self.seller_1:
                seller_1_total_expense += amount
            else:
                seller_2_total_expense += amount

        self.seller_1.refresh_from_db()
        self.seller_2.refresh_from_db()

        check_user_balance(self.seller_1)
        check_user_balance(self.seller_2)
        self.assertEqual(self.seller_1.balance, seller_1_initial_balance - seller_1_total_expense)
        self.assertEqual(self.seller_2.balance, seller_2_initial_balance - seller_2_total_expense)
