"""Notification navbar tests without writing notification records."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.template.loader import render_to_string
from django.test import SimpleTestCase, RequestFactory

from .context_processors import notification_badge, unread_notifications
from .notification_services import get_user_notification_center, _safe_internal_link


class NavbarNotificationTests(SimpleTestCase):
    def test_anonymous_does_not_query(self):
        with patch("accounts.notification_services.connection") as connection:
            self.assertEqual(get_user_notification_center(SimpleNamespace(is_authenticated=False)),
                             {"latest_notifications": [], "unread_notifications_count": 0})
            self.assertFalse(connection.mock_calls)

    def test_owner_filter_limit_order_count_and_safe_links(self):
        user = SimpleNamespace(is_authenticated=True, pk=17)
        collection = MagicMock()
        collection.find.return_value.sort.return_value.limit.return_value = [
            {"title": "Actual title", "message": "Actual message", "is_read": False, "link": "/notifications/"},
            {"title": "Unsafe", "is_read": True, "link": "https://example.com/"},
        ]
        collection.count_documents.return_value = 9
        with patch("accounts.notification_services.connection") as connection, patch("accounts.notification_services._notification_id_variants", return_value=[17, "17"]):
            connection.database.__getitem__.return_value = collection
            result = get_user_notification_center(user)
        self.assertEqual(collection.find.call_args.args[0], {"user_id": {"$in": [17, "17"]}})
        self.assertEqual(collection.find.return_value.sort.call_args.args[0], [("is_read", 1), ("created_at", -1), ("_id", -1)])
        collection.find.return_value.sort.return_value.limit.assert_called_once_with(5)
        collection.count_documents.assert_called_once_with({"user_id": {"$in": [17, "17"]}, "is_read": False})
        self.assertEqual(result["unread_notifications_count"], 9)
        self.assertEqual(result["latest_notifications"][0]["link"], "/notifications/")
        self.assertEqual(result["latest_notifications"][1]["link"], "")

    def test_two_processors_share_one_request_result_and_keep_permissions(self):
        request = RequestFactory().get("/dashboard/")
        request.user = SimpleNamespace(is_authenticated=True, is_superuser=True)
        data = {"latest_notifications": [], "unread_notifications_count": 3}
        with patch("accounts.notification_services.get_user_notification_center", return_value=data) as loader:
            self.assertEqual(notification_badge(request), data)
            context = unread_notifications(request)
            loader.assert_called_once_with(request.user)
        self.assertTrue(context["can_manage_configuration"])
        self.assertTrue(context["can_manage_fee_categories"])
        self.assertEqual(context["unread_notifications_count"], 3)

    def test_unsafe_and_mutating_links_are_not_followed(self):
        for link in ("https://example.com", "//example.com", "javascript:alert(1)", "/\\example.com", "/missing-route/", "/notifications/?mark_all_read=true"):
            with self.subTest(link=link):
                self.assertEqual(_safe_internal_link(link), "")
        self.assertEqual(_safe_internal_link("/notifications/settings/"), "/notifications/settings/")

    def test_template_empty_state_and_no_zero_badge(self):
        html = render_to_string("includes/navbar.html", {"latest_notifications": [], "unread_notifications_count": 0})
        self.assertIn("You're all caught up", html)
        self.assertIn('aria-expanded="false"', html)
        self.assertIn('aria-haspopup="dialog"', html)
        self.assertNotIn('class="edu-notification-count"', html)
        self.assertIn('href="/notifications/"', html)

    def test_unlinked_rows_and_html_are_safe(self):
        html = render_to_string("includes/navbar.html", {"unread_notifications_count": 1, "latest_notifications": [
            {"title": "<script>bad()</script>", "message": "<b>message</b>", "link": "", "is_read": False},
        ]})
        self.assertIn('<div class="edu-notification-item is-unread">', html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>bad()", html)
        self.assertIn("1 unread", html)
