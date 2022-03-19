from django.urls import path
from . import views

urlpatterns = [
    path('login_signup/', views.RequestLoginView.as_view(), name='login_signup'),
    path('verify_otp/', views.VerifyOtpView.as_view(), name='verify_otp'),
]