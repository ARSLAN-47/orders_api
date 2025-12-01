
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from django.db.models import F
from .models import Order, Outbox
from .serializers import OrderSerializer, ConfirmSerializer
from .idempotency import idempotent_endpoint
from .pagination import KeysetPagination


class OrderCreateView(APIView):
    """
    POST /orders  (idempotent via decorator)
    """
    @idempotent_endpoint
    def post(self, request):
        tenant_id = request.tenant_id
       
        with transaction.atomic():
            order = Order.objects.create(tenant_id=tenant_id, status=Order.Status.DRAFT, version=1)
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderConfirmView(APIView):
    """
    PATCH /orders/{id}/confirm   (optimistic locking via If-Match header)
    """
    def patch(self, request, id):
        tenant_id = request.tenant_id
       
        ser = ConfirmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        total_cents = ser.validated_data['totalCents']

        if_match = request.headers.get("If-Match")
        if not if_match:
            return Response({"code":"missing_if_match","message":"If-Match header required"}, status=400)
        
        try:
            expected_version = int(if_match.strip().strip('"'))
        except Exception:
            return Response({"code":"invalid_if_match","message":"If-Match header must be an integer version"}, status=400)

        with transaction.atomic():
            updated = Order.objects.filter(id=id, tenant_id=tenant_id, version=expected_version, status=Order.Status.DRAFT).update(
                version=F('version') + 1,
                status=Order.Status.CONFIRMED,
                total_cents=total_cents,
                updated_at=timezone.now()
            )
            if updated == 0:
                try:
                    order = Order.objects.get(id=id, tenant_id=tenant_id)
                    if order.version != expected_version:
                        return Response({"code":"conflict","message":"stale version"}, status=409)
                    if order.status != Order.Status.DRAFT:
                        return Response({"code":"invalid_transition","message":"only draft -> confirmed allowed"}, status=400)
                except Order.DoesNotExist:
                    return Response({"code":"not_found","message":"order not found"}, status=404)
            order = Order.objects.get(id=id, tenant_id=tenant_id)
      
        out = {
            "id": str(order.id),
            "status": order.status,
            "version": order.version,
            "totalCents": order.total_cents
        }
        return Response(out, status=200)


class OrderCloseView(APIView):
    """
    POST /orders/{id}/close  (transactional close and write outbox)
    """
    def post(self, request, id):
        tenant_id = request.tenant_id

        if_match = request.headers.get("If-Match")
        if not if_match:
            return Response({"code":"missing_if_match","message":"If-Match header required"}, status=400)
        try:
            expected_version = int(if_match.strip().strip('"'))
        except Exception:
            return Response({"code":"invalid_if_match","message":"If-Match header must be an integer version"}, status=400)

        with transaction.atomic():
            qs = Order.objects.select_for_update().filter(id=id, tenant_id=tenant_id)
            try:
                order = qs.get()
            except Order.DoesNotExist:
                return Response({"code":"not_found","message":"order not found"}, status=404)

            if order.version != expected_version:
                return Response({"code":"conflict","message":"stale version"}, status=409)
            if order.status != Order.Status.CONFIRMED:
                return Response({"code":"invalid_transition","message":"order must be confirmed to be closed"}, status=400)

            order.status = Order.Status.CLOSED
            order.version = F('version') + 1
            order.save(update_fields=['status','version','updated_at'])

            order.refresh_from_db()

            payload = {
                "orderId": str(order.id),
                "tenantId": tenant_id,
                "totalCents": order.total_cents,
                "closedAt": timezone.now().isoformat()
            }
            Outbox.objects.create(event_type="orders.closed", order_id=order.id, tenant_id=tenant_id, payload=payload)

        return Response({"id": str(order.id), "status": order.status, "version": order.version}, status=200)



class OrderListView(APIView):
    
    def get(self, request):
        tenant_id = request.tenant_id
        qs = Order.objects.filter(tenant_id=tenant_id)
        paginator = KeysetPagination()
        items, next_cursor = paginator.paginate_queryset(qs, request)
        serializer = OrderSerializer(items, many=True)
        return paginator.get_paginated_response(serializer.data, next_cursor)
