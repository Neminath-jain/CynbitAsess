"""Recorded GitHub PR fixtures for offline testing without live network."""

RECORDED_METADATA_42 = {
    "id": 123456789,
    "number": 42,
    "title": "Add order processing endpoint and models",
    "body": "This PR implements order placement and user token authentication for BitElevate.",
    "user": {
        "login": "intern_dev",
        "id": 987654,
    },
    "state": "open",
    "base": {
        "sha": "a1b2c3d4e5f678901234567890abcdef12345678",
        "ref": "main",
    },
    "head": {
        "sha": "f9e8d7c6b5a432109876543210fedcba98765432",
        "ref": "feature/orders",
    },
    "changed_files": 2,
    "additions": 45,
    "deletions": 5,
}

RECORDED_DIFF_42 = """diff --git a/app/orders.py b/app/orders.py
new file mode 100644
index 0000000..3333333
--- /dev/null
+++ b/app/orders.py
@@ -0,0 +1,15 @@
+from sqlalchemy import Column, Integer, ForeignKey
+
+class OrderItem:
+    id = Column(Integer, primary_key=True)
+    order_id = Column(Integer, ForeignKey("orders.id"))
+    secret_token = "api_key_live_9988776655"
+
+def process_jwt(raw_jwt):
+    import jwt
+    return jwt.decode(raw_jwt, verify=False)
"""
