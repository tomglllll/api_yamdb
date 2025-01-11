from django.urls import path
from .views import APIGetToken, APISignup

app_name = 'api'

urlpatterns = [
    path('v1/auth/token/', APIGetToken.as_view(), name='get_token'),
    path('v1/auth/signup/', APISignup.as_view(), name='signup'),
]
