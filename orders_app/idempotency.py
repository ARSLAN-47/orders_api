# myapp/idempotency.py
from functools import wraps
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from .models import IdempotencyKey

IDEMPOTENCY_TTL = timedelta(hours=1)

def idempotent_endpoint(func):
    """
    Decorator for views implementing idempotent behavior using Idempotency-Key header.
    Stores response JSON into IdempotencyKey.response_json.
    """

    @wraps(func)
    def wrapper(view, request, *args, **kwargs):
        # Only for POST/PUT/DELETE where client provided Idempotency-Key
        key = request.headers.get("Idempotency-Key")
        if not key:
            return JsonResponse({"code":"missing_idempotency_key","message":"Idempotency-Key header required"}, status=400)

        tenant_id = getattr(request, "tenant_id", None)
        if not tenant_id:
            return JsonResponse({"code":"missing_tenant","message":"X-Tenant-Id header required"}, status=400)

        body_bytes = request.body or b""

        # Try to get or create the idempotency row
        with transaction.atomic():
            obj, created = IdempotencyKey.objects.select_for_update().get_or_create(
                tenant_id=tenant_id, key=key,
                defaults={"request_body": body_bytes}
            )

            if not created:
                # check age
                if obj.created_at + IDEMPOTENCY_TTL < timezone.now():
                    # treat as new request: allow reprocessing — we'll update request_body below
                    obj.request_body = body_bytes
                    obj.response_json = None
                    obj.created_at = timezone.now()
                    obj.save(update_fields=['request_body','response_json','created_at'])
                else:
                    # same key within ttl
                    # If response present -> replay if request_body matches
                    if obj.response_json is not None:
                        if obj.request_body == body_bytes:
                            return JsonResponse(obj.response_json, status=200, safe=False)
                        else:
                            return JsonResponse({"code":"conflict","message":"Idempotency key used with different request body"}, status=409)

            # If we reach here: either new row created, or old expired/reset, or no response yet.
            # Mark request_body (create case already set by defaults)
            obj.request_body = body_bytes
            obj.save(update_fields=['request_body'])
            # Proceed to view; we will save response after
        # run the view (outside the transaction above so view can open its own transactions)
        response = func(view, request, *args, **kwargs)

        # After view returns, if 2xx: store response JSON into idempotency row
        try:
            status_code = getattr(response, "status_code", 200)
            data = response.data if hasattr(response, "data") else None
            # convert DRF Response to JSONable (response.data) or raw HttpResponse
            if 200 <= status_code < 300 and data is not None:
                with transaction.atomic():
                    # reload with lock and set response_json
                    obj = IdempotencyKey.objects.select_for_update().get(tenant_id=tenant_id, key=key)
                    obj.response_json = data
                    obj.save(update_fields=['response_json'])
        except Exception:
            # do not hide original response on failure to persist idempotency record
            pass

        return response
    return wrapper
