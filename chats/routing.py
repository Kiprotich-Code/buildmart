from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<chat_id>[0-9a-f-]+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/dispute/(?P<dispute_id>[0-9a-f-]+)/$', consumers.DisputeConsumer.as_asgi()),
    re_path(r'ws/user/(?P<user_id>[0-9]+)/$', consumers.UserConsumer.as_asgi()),
]
