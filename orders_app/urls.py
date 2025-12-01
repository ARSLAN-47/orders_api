"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from .views import OrderCreateView, OrderConfirmView, OrderCloseView, OrderListView



urlpatterns = [
    path('', OrderCreateView.as_view(), name='order-create'),
    path('<uuid:id>/confirm', OrderConfirmView.as_view(), name='order-confirm'),
    path('<uuid:id>/close', OrderCloseView.as_view(), name='order-close'),
    path('list', OrderListView.as_view(), name='order-list'),  # or reuse /orders with GET
]
