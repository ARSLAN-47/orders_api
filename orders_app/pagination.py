
import base64
import json
from rest_framework.pagination import BasePagination
from rest_framework.response import Response
from django.utils.dateparse import parse_datetime
from django.db import models

def _encode_cursor(ts, id_):
    payload = {"ts": ts, "id": str(id_)}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()

def _decode_cursor(cursor):
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        payload = json.loads(raw)
        return payload.get("ts"), payload.get("id")
    except Exception:
        return None, None

class KeysetPagination(BasePagination):
    page_size_query_param = 'limit'
    default_limit = 20
    max_limit = 100

    def paginate_queryset(self, queryset, request, view=None):
        limit = int(request.query_params.get('limit', self.default_limit))
        limit = min(limit, self.max_limit)
        cursor = request.query_params.get('cursor')
        tenant_id = getattr(request, "tenant_id", None)

        # enforce tenant scoping at view level; here assume queryset already filtered by tenant
        if cursor:
            ts_str, id_str = _decode_cursor(cursor)
            if ts_str and id_str:
                # parse ISO ts
                try:
                    ts = parse_datetime(ts_str)
                except Exception:
                    ts = None
                # apply keyset: since sorting is created_at DESC, id DESC
                if ts is not None:
                    queryset = queryset.filter(
                        # either created_at < ts OR (created_at == ts and id < id_str)
                        models.Q(created_at__lt=ts) |
                        (models.Q(created_at=ts) & models.Q(id__lt=id_str))
                    )
        # ordering must match keyset definition
        queryset = queryset.order_by('-created_at', '-id')[:limit + 1]
        items = list(queryset)
        self.has_more = len(items) > limit
        if self.has_more:
            self.items = items[:limit]
            last = self.items[-1]
            next_cursor = _encode_cursor(last.created_at.isoformat(), last.id)
        else:
            self.items = items
            next_cursor = None

        return self.items, next_cursor

    def get_paginated_response(self, data, next_cursor):
        return Response({"items": data, "nextCursor": next_cursor})
