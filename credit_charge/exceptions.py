import decimal

import credit_charge.models


class NegetavieBalanceError(Exception):
    def __init__(
        self,
        amount: decimal.Decimal,
        user: "credit_charge.models.User",
        user_balance: decimal.Decimal,
    ):
        self.amount = amount
        self.user = user
        self.user_balance = user_balance
        super().__init__(f"User {self.user} has insufficient balance: {self.user_balance}")


class UserBalanceCheckError(Exception):
    def __init__(self, user: "credit_charge.models.User", diff: decimal.Decimal):
        self.diff = diff
        self.user = user
        super().__init__(f"User {self.user} balance is not equal to total charge and expense: {self.diff}")
