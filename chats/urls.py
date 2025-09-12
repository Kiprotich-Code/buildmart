from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatViewSet, MessageViewSet, ProductQuestionViewSet, ProductAnswerViewSet

router = DefaultRouter()
router.register(r'chats', ChatViewSet, basename='chat')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'questions', ProductQuestionViewSet, basename='question')
router.register(r'answers', ProductAnswerViewSet, basename='answer')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
]
