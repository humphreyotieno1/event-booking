from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.EventCategoryViewSet)
router.register(r'tags', views.EventTagViewSet)
router.register(r'events', views.EventViewSet)
router.register(r'reviews', views.ReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
]
