from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import (
    CategoryViewSet,
    GenreViewSet,
    TitleViewSet,
    APIGetToken,
    APISignup
)

router_v1 = DefaultRouter()
router_v1.register(r'categories', CategoryViewSet, basename='categories')
router_v1.register(r'genres', GenreViewSet, basename='genres')
router_v1.register(r'titles', TitleViewSet, basename='titles')

auth_urls = ([
    path('signup/', APISignup.as_view(), name='signup'),
    path('token/', APIGetToken.as_view(), name='get_token'),
], 'auth')

urlpatterns = [
    path('v1/', include(router_v1.urls)),
    path('v1/auth/', include(auth_urls)),
]
