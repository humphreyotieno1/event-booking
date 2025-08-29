from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'external-events', views.ExternalEventViewSet, basename='external-event')

urlpatterns = [
    path('', include(router.urls)),
]
