"""
Level 2 - Intermediate: Mocking with unittest.mock
====================================================
Mocking lets you replace real dependencies (HTTP clients, databases,
email senders) with controlled fakes during testing.

Run:
    pip install pytest pytest-mock
    pytest 01_mocking.py -v
"""

from unittest.mock import MagicMock, patch, call
from typing import Protocol
import pytest


# ─── Domain model ─────────────────────────────────────────────────────────────

class EmailSender(Protocol):
    """Boundary interface for sending emails."""
    def send(self, to: str, subject: str, body: str) -> None: ...


class NotificationService:
    """Sends user-facing notifications via email."""

    def __init__(self, sender: EmailSender):
        self._sender = sender

    def welcome(self, user_email: str, user_name: str) -> None:
        self._sender.send(
            to=user_email,
            subject="Welcome!",
            body=f"Hello {user_name}, welcome to our platform.",
        )

    def password_reset(self, user_email: str, token: str) -> None:
        self._sender.send(
            to=user_email,
            subject="Password Reset",
            body=f"Use this token to reset your password: {token}",
        )


class OrderRepository(Protocol):
    def find_by_user(self, user_id: int) -> list[dict]: ...
    def save(self, order: dict) -> dict: ...


class OrderService:
    """Manages orders; depends on a repository and a notification sender."""

    def __init__(self, repo: OrderRepository, notifications: NotificationService):
        self._repo = repo
        self._notifications = notifications

    def place_order(self, user_id: int, user_email: str, items: list[str]) -> dict:
        if not items:
            raise ValueError("Order must contain at least one item")
        order = self._repo.save({"user_id": user_id, "items": items, "status": "placed"})
        self._notifications.welcome(user_email, f"User-{user_id}")
        return order


# ─── Tests using MagicMock ─────────────────────────────────────────────────────

class TestNotificationService:

    def test_welcome_sends_email_to_correct_address(self):
        # Arrange — create a mock that records calls
        mock_sender = MagicMock(spec=EmailSender)
        service = NotificationService(sender=mock_sender)

        # Act
        service.welcome("alice@example.com", "Alice")

        # Assert — verify the mock was called with the right arguments
        mock_sender.send.assert_called_once_with(
            to="alice@example.com",
            subject="Welcome!",
            body="Hello Alice, welcome to our platform.",
        )

    def test_password_reset_includes_token_in_body(self):
        mock_sender = MagicMock(spec=EmailSender)
        service = NotificationService(sender=mock_sender)

        service.password_reset("alice@example.com", token="abc123")

        args = mock_sender.send.call_args
        assert "abc123" in args.kwargs["body"]
        assert args.kwargs["to"] == "alice@example.com"

    def test_welcome_called_exactly_once(self):
        mock_sender = MagicMock(spec=EmailSender)
        service = NotificationService(sender=mock_sender)

        service.welcome("alice@example.com", "Alice")

        assert mock_sender.send.call_count == 1


class TestOrderService:

    def test_place_order_saves_order_and_sends_welcome(self):
        # Arrange
        mock_repo    = MagicMock(spec=OrderRepository)
        mock_sender  = MagicMock(spec=EmailSender)
        notifications = NotificationService(sender=mock_sender)

        # Configure the stub return value
        mock_repo.save.return_value = {
            "id": 42, "user_id": 1, "items": ["widget"], "status": "placed"
        }

        service = OrderService(repo=mock_repo, notifications=notifications)

        # Act
        order = service.place_order(
            user_id=1,
            user_email="alice@example.com",
            items=["widget"],
        )

        # Assert
        assert order["id"] == 42
        mock_repo.save.assert_called_once()
        mock_sender.send.assert_called_once()

    def test_place_order_empty_items_raises_error(self):
        mock_repo    = MagicMock(spec=OrderRepository)
        mock_sender  = MagicMock(spec=EmailSender)
        notifications = NotificationService(sender=mock_sender)
        service = OrderService(repo=mock_repo, notifications=notifications)

        with pytest.raises(ValueError, match="at least one item"):
            service.place_order(user_id=1, user_email="alice@example.com", items=[])

        # Confirm no side-effects occurred
        mock_repo.save.assert_not_called()
        mock_sender.send.assert_not_called()


# ─── Tests using @patch decorator ─────────────────────────────────────────────

class PaymentGateway:
    def charge(self, amount: float, card_token: str) -> str:
        raise NotImplementedError("Real gateway — do not call in tests!")


class PaymentService:
    def __init__(self, gateway: PaymentGateway):
        self._gateway = gateway

    def process(self, amount: float, card_token: str) -> dict:
        transaction_id = self._gateway.charge(amount, card_token)
        return {"status": "success", "transaction_id": transaction_id, "amount": amount}


class TestPaymentService:

    def test_process_returns_success_with_transaction_id(self):
        mock_gateway = MagicMock(spec=PaymentGateway)
        mock_gateway.charge.return_value = "txn_abc123"
        service = PaymentService(gateway=mock_gateway)

        result = service.process(49.99, "tok_test")

        assert result["status"] == "success"
        assert result["transaction_id"] == "txn_abc123"
        assert result["amount"] == 49.99

    def test_process_forwards_correct_arguments_to_gateway(self):
        mock_gateway = MagicMock(spec=PaymentGateway)
        mock_gateway.charge.return_value = "txn_xyz"
        service = PaymentService(gateway=mock_gateway)

        service.process(100.00, "tok_stripe")

        mock_gateway.charge.assert_called_once_with(100.00, "tok_stripe")
