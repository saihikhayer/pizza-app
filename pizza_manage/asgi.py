"""
ASGI config for pizza_manage project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from pizza_app.consumers import ChefOrderConsumer
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pizza_manage.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/orders/", ChefOrderConsumer.as_asgi()),
        ])
    ),
})
