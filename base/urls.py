from django.urls import path
from . import views
from .views import (index, signup, logout_user, login_user, create_report, user_profile, edit_report, delete_report, report, sample_report, all_users)

urlpatterns = [
    path("home/", index, name="home"),
    path("signup/", signup, name="signup"),
    path("login/", login_user, name="login"),
    path("logout/", logout_user, name="logout"),
    path("daily-reports/", create_report, name="reports"),
    path("profile/", user_profile, name="profile"),
    path('edit-report/<int:pk>/', edit_report, name='edit'),
    path("delete-report/<int:pk>", delete_report, name="delete"),
    path("report/<int:pk>/", report, name="report"),
    path("sample-report/", sample_report, name="sample"),
    path("classmates/", all_users, name="classmates")
    
]
