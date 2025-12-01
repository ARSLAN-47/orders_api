
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

# class TenantMiddleware(MiddlewareMixin):
#     def process_request(self, request):
#         tenant = request.headers.get("X-Tenant-Id")
#         if not tenant:
#             return JsonResponse({"code":"missing_tenant","message":"X-Tenant-Id header required"}, status=400)
#         request.tenant_id = tenant



EXEMPT_PATHS = ["/schema/", "/docs/", "/redoc/"]

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if any(request.path.startswith(p) for p in EXEMPT_PATHS):
            return  # skip tenant check
        tenant = request.headers.get("X-Tenant-Id")
        if not tenant:
            return JsonResponse(
                {"code":"missing_tenant","message":"X-Tenant-Id header required"}, 
                status=400
            )
        request.tenant_id = tenant
