import uuid
from django.db import models
from django.utils import timezone
class Order(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft"
        CONFIRMED = "confirmed"
        CLOSED = "closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=255, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    version = models.IntegerField(default=1)
    total_cents = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['tenant_id', '-created_at', '-id'], name='orders_tenant_created_id_idx'),
           
        ]

    def __str__(self):
        return f"Order({self.id}, tenant={self.tenant_id}, status={self.status}, v={self.version})"


class Outbox(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=255)
    order_id = models.UUIDField()
    tenant_id = models.CharField(max_length=255)
    payload = models.JSONField()
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['tenant_id', 'created_at']),
        ]


class IdempotencyKey(models.Model):
    tenant_id = models.CharField(max_length=255)
    key = models.CharField(max_length=255)
    request_body = models.BinaryField(null=True)  
    response_json = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = (('tenant_id', 'key'),)
        indexes = [
            models.Index(fields=['tenant_id', 'key']),
        ]
