# orders_app/tests/test_orders_api.py
import json
from django.test import TestCase, Client
from django.urls import reverse
from orders_app.models import Order, Outbox

class OrdersApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.tenant_id = "shop-1"
        self.headers = {
            "HTTP_X_TENANT_ID": self.tenant_id,
        }

    # ------------------------
    # 1️⃣ Idempotency Tests
    # ------------------------
    def test_idempotency_replay_and_conflict(self):
        url = reverse("order-create")  # POST /orders
        key = "idem-123"

        # First request
        response1 = self.client.post(
            url,
            data="",
            content_type="application/json",
            **{"HTTP_IDEMPOTENCY_KEY": key, **self.headers},
        )
        self.assertEqual(response1.status_code, 200)
        data1 = response1.json()
        order_id = data1["id"]
        order_version = data1["version"]

        # Replay same key + same body → same ID
        response2 = self.client.post(
            url,
            data="",
            content_type="application/json",
            **{"HTTP_IDEMPOTENCY_KEY": key, **self.headers},
        )
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        self.assertEqual(data2["id"], order_id)

        # Same key + different body → 409 conflict
        response3 = self.client.post(
            url,
            data=json.dumps({"dummy": 1}),
            content_type="application/json",
            **{"HTTP_IDEMPOTENCY_KEY": key, **self.headers},
        )
        self.assertEqual(response3.status_code, 409)

    # ------------------------
    # 2️⃣ Optimistic Locking
    # ------------------------
    def test_confirm_order_versioning(self):
        # Create draft
        response = self.client.post(
            reverse("order-create"),
            data=json.dumps({}),
            content_type="application/json",
            **{"HTTP_IDEMPOTENCY_KEY": "draft-1", **self.headers},
        )
        order = response.json()
        order_id = order["id"]
        version = order["version"]

        # Confirm with correct version
        response_confirm = self.client.patch(
            reverse("order-confirm", args=[order_id]),
            data=json.dumps({"totalCents": 12345}),
            content_type="application/json",
            **{"HTTP_IF_MATCH": str(version), **self.headers},
        )
        self.assertEqual(response_confirm.status_code, 200)
        data = response_confirm.json()
        self.assertEqual(data["status"], "confirmed")
        self.assertEqual(data["version"], version + 1)

        # Confirm with stale If-Match → 409
        response_stale = self.client.patch(
            reverse("order-confirm", args=[order_id]),
            data=json.dumps({"totalCents": 555}),
            content_type="application/json",
            **{"HTTP_IF_MATCH": str(version), **self.headers},
        )
        self.assertEqual(response_stale.status_code, 409)

    # ------------------------
    # 3️⃣ Close + Outbox
    # ------------------------
    def test_close_order_creates_outbox(self):
        # Create + confirm
        response = self.client.post(
            reverse("order-create"),
            data=json.dumps({}),
            content_type="application/json",
            **{"HTTP_IDEMPOTENCY_KEY": "draft-2", **self.headers},
        )
        order = response.json()
        order_id = order["id"]
        version = order["version"]

        # Confirm order first
        response_confirm = self.client.patch(
            reverse("order-confirm", args=[order_id]),
            data=json.dumps({"totalCents": 200}),
            content_type="application/json",
            **{"HTTP_IF_MATCH": str(version), **self.headers},
        )
        self.assertEqual(response_confirm.status_code, 200)
        confirmed_order = response_confirm.json()
        new_version = confirmed_order["version"]

        # Close order with updated version
        response_close = self.client.post(
            reverse("order-close", args=[order_id]),
            content_type="application/json",
            **{"HTTP_IF_MATCH": str(new_version), **self.headers},
        )
        self.assertEqual(response_close.status_code, 200)

        # Verify order status
        order_obj = Order.objects.get(id=order_id)
        self.assertEqual(order_obj.status, "closed")

        # Verify exactly one outbox row
        outboxes = Outbox.objects.filter(order_id=order_id)
        self.assertEqual(outboxes.count(), 1)

    # ------------------------
    # 4️⃣ Pagination
    # ------------------------
    def test_pagination(self):
        # Create 15 orders
        for i in range(15):
            self.client.post(
                reverse("order-create"),
                data=json.dumps({}),
                content_type="application/json",
                **{"HTTP_IDEMPOTENCY_KEY": f"draft-{i}", **self.headers},
            )

        # First page: limit=10
        response1 = self.client.get(
            reverse("order-list") + "?limit=10",
            **self.headers,
        )
        self.assertEqual(response1.status_code, 200)
        data1 = response1.json()
        self.assertEqual(len(data1["items"]), 10)
        self.assertIsNotNone(data1["nextCursor"])

        # Second page using nextCursor
        cursor = data1["nextCursor"]
        response2 = self.client.get(
            reverse("order-list") + f"?limit=10&cursor={cursor}",
            **self.headers,
        )
        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        self.assertEqual(len(data2["items"]), 5)  # remaining items
        self.assertIsNone(data2.get("nextCursor"))

        # Ensure no duplicates between pages
        ids_page1 = {item["id"] for item in data1["items"]}
        ids_page2 = {item["id"] for item in data2["items"]}
        self.assertTrue(ids_page1.isdisjoint(ids_page2))
