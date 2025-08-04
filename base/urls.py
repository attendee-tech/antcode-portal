from django.urls import path
from . import views
from .views import (
    index, signup, logout_user, login_user, create_report, user_profile, 
    edit_report, delete_report, report_view, sample_report, all_users, 
    mentor_signup, mentor_dashboard, create_task, create_project, courses,
    view_notifications, react_course
)

urlpatterns = [
    path("home/", index, name="home"),
    path("signup/", signup, name="signup"),
    path("login/", login_user, name="login"),
    path("logout/", logout_user, name="logout"),
    path("daily-reports/", create_report, name="reports"),
    path("profile/", user_profile, name="profile"),
    path("edit-report/<int:pk>/", edit_report, name="edit"),
    path("delete-report/<int:pk>/", delete_report, name="delete"),
    path("view-report/<int:pk>/", report_view, name="report-view"),
    path("sample-report/", sample_report, name="sample"),
    path("classmates/", all_users, name="classmates"),

    # Mentor specific routes
    path("mentor/signup/", mentor_signup, name="mentor_signup"),
    path("mentor/dashboard/", mentor_dashboard, name="mentor_dashboard"),
    path("mentor/create-task/", create_task, name="create_task"),
    path("mentor/create-project/", create_project, name="create_project"),

    # Courses and reactions
    path("courses/", courses, name="courses"),
    path("courses/<int:course_id>/react/", react_course, name="react_course"),

    # Notifications
    path("notifications/", view_notifications, name="notifications"),
]
