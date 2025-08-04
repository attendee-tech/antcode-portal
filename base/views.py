from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg, Case, When, FloatField
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils.timezone import now
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext_lazy as _

from .models import (
    User, Option, Project, Task, Report, 
    MentorProfile, StudentProfile, Course,
    StudentCourseProgress, EmojiReaction, Notification
)

# ---------------------------
# Authentication Views
# ---------------------------

@require_http_methods(["GET", "POST"])
def signup(request):
    """Handle student signup with optimized queries and error handling."""
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        try:
            data = request.POST
            username = data.get("username")
            email = data.get("email")
            
            if User.objects.filter(Q(email=email) | Q(username=username)).exists():
                messages.error(request, _("Username or email already taken."))
                return redirect("signup")

            option = get_object_or_404(Option, name=data.get("option"))
            
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=data.get("password"),
                    first_name=data.get("first_name"),
                    last_name=data.get("last_name"),
                    phone=data.get("phone"),
                    user_type=User.UserType.STUDENT,
                )
                StudentProfile.objects.create(user=user, option=option)
                
                login(request, user)
                messages.success(request, _("Account created successfully."))
                return redirect("home")

        except Exception as e:
            messages.error(request, _(f"Error: {str(e)}"))
            return redirect("signup")

    options = Option.objects.all()
    return render(request, "signup.html", {"options": options})

@require_http_methods(["GET", "POST"])
def login_user(request):
    """Optimized login view with proper session handling."""
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if not user:
            messages.error(request, _("Invalid credentials."))
            return render(request, "login.html")

        login(request, user)
        messages.success(request, _("Logged in successfully."))
        
        # Use hasattr to check for user_type, fallback to logout if not present
        if hasattr(user, "user_type"):
            redirect_url = {
                getattr(User.UserType, "MENTOR", "mentor"): "mentor_dashboard",
                getattr(User.UserType, "STUDENT", "student"): "home"
            }.get(getattr(user, "user_type", None), "logout")
        else:
            redirect_url = "logout"
        
        return redirect(redirect_url)

    return render(request, "login.html")

@login_required
def logout_user(request):
    """Secure logout view."""
    logout(request)
    return redirect("login")

# ---------------------------
# Mentor Views
# ---------------------------

@require_http_methods(["GET", "POST"])
def mentor_signup(request):
    """Optimized mentor signup with option availability check."""
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        try:
            data = request.POST
            option = get_object_or_404(Option, name=data.get("option"))
            if MentorProfile.objects.filter(option=option).exists():
                messages.error(request, _(f"A mentor is already assigned to '{option.name}'."))
                return redirect("mentor_signup")

            with transaction.atomic():
                user = User.objects.create_user(
                    username=data.get("username"),
                    password=data.get("password"),
                    email=data.get("email"),
                    phone=data.get("phone"),
                    first_name=data.get("first_name"),
                    last_name=data.get("last_name"),
                    user_type=User.UserType.MENTOR,
                )
                MentorProfile.objects.create(user=user, option=option)
                
                login(request, user)
                messages.success(request, _("Mentor account created successfully."))
                return redirect("home")

        except Exception as e:
            messages.error(request, _(f"Error: {str(e)}"))
            return redirect("mentor_signup")

    options = Option.objects.all()
    return render(request, "mentor_signup.html", {"options": options})

@login_required
def mentor_dashboard(request):
    """Optimized mentor dashboard with aggregated data."""
    if request.user.user_type != User.UserType.MENTOR:
        raise PermissionDenied(_("Unauthorized access."))

    mentor = get_object_or_404(MentorProfile, user=request.user)
    option = mentor.option
    
    stats = {
        'students_count': StudentProfile.objects.filter(option=option).count(),
        'reports_count': Report.objects.filter(option=option).count(),
        'tasks_count': Task.objects.filter(option=option).count(),
        'projects_count': Project.objects.filter(option=option).count(),
    }
    report_stats = Report.objects.filter(option=option).aggregate(
        avg_score=Avg('mark', default=0),
        completion_rate=Avg(
            Case(
                When(status='approved', then=1),
                default=0,
                output_field=FloatField()
            )
        )
    )

    context = {
        "students": StudentProfile.objects.filter(option=option).select_related('user')[:10],
        "reports": Report.objects.filter(option=option).select_related('student')[:5],
        "tasks": Task.objects.filter(option=option).prefetch_related('students')[:5],
        "projects": Project.objects.filter(option=option).prefetch_related('students')[:5],
        **stats,
        "average_score": round(report_stats['avg_score'] or 0, 2),
        "completion_rate": round((report_stats['completion_rate'] or 0) * 100, 2),
    }
    return render(request, "mentor.html", context)

@login_required
@require_http_methods(["GET", "POST"])
def create_task(request):
    """Optimized task/project creation view with bulk operations."""
    if request.user.user_type != User.UserType.MENTOR:
        raise PermissionDenied(_("Only mentors can create tasks."))

    mentor = get_object_or_404(MentorProfile, user=request.user)
    students = StudentProfile.objects.filter(option=mentor.option).select_related('user')
    
    if request.method == "POST":
        try:
            data = request.POST
            student_ids = [int(id) for id in data.getlist("student")]
            
            if not student_ids:
                messages.error(request, _("Please select at least one student."))
                return redirect("create_task")

            with transaction.atomic():
                if data.get("type") == "task":
                    task = Task.objects.create(
                        name=data.get("name"),
                        content=data.get("content"),
                        due_date=data.get("due-date"),
                        option=mentor.option,
                        mentor=mentor
                    )
                    task.students.add(*student_ids)
                    messages.success(request, _("Task created and assigned successfully."))
                else:
                    project = Project.objects.create(
                        name=data.get("name"),
                        content=data.get("content"),
                        due_date=data.get("due-date"),
                        option=mentor.option,
                        mentor=mentor
                    )
                    project.students.add(*student_ids)
                    messages.success(request, _("Project created and assigned successfully."))

            return redirect("create_task")

        except Exception as e:
            messages.error(request, _(f"Error: {str(e)}"))

    context = {
        'tasks': Task.objects.filter(mentor=mentor).prefetch_related('students')[:10],
        'projects': Project.objects.filter(mentor=mentor).prefetch_related('students')[:10],
        'students': students,
        'reports': Report.objects.filter(option=mentor.option).select_related('student')[:5]
    }
    return render(request, "create.html", context)

@login_required
@require_http_methods(["GET", "POST"])
def create_project(request):
    """Alias for create_task for project creation."""
    return create_task(request)

# ---------------------------
# Student Views
# ---------------------------

@login_required
def index(request):
    """Optimized student dashboard with prefetching."""
    if request.user.user_type != User.UserType.STUDENT:
        raise PermissionDenied(_("Only students can access this dashboard."))

    student = get_object_or_404(StudentProfile, user=request.user)
    reports = Report.objects.filter(student=request.user).select_related('option')
    tasks = Task.objects.filter(students=student).prefetch_related('mentor')
    projects = Project.objects.filter(students=student).prefetch_related('mentor')
    
    stats = {
        'reports_count': reports.count(),
        'tasks_count': tasks.count(),
        'projects_count': projects.count(),
        'average_score': reports.aggregate(avg=Avg('mark'))['avg'] or 0,
        'completion_rate': reports.filter(status='approved').count() / reports.count() * 100 
                          if reports.exists() else 0
    }

    context = {
        "reports": reports[:5],
        "tasks": tasks[:5],
        "projects": projects[:5],
        **{k: round(v, 2) if isinstance(v, float) else v for k, v in stats.items()}
    }
    return render(request, "index.html", context)

@login_required
@require_http_methods(["GET", "POST"])
def user_profile(request):
    """Optimized profile view with proper file handling."""
    user = request.user
    student = get_object_or_404(StudentProfile, user=user) if user.user_type == User.UserType.STUDENT else None
    
    if request.method == "POST":
        try:
            data = request.POST
            user.username = data.get("username")
            user.first_name = data.get("first_name")
            user.last_name = data.get("last_name")
            user.email = data.get("email")
            user.phone = data.get("phone")
            user.bio = data.get("about")
            user.skills = data.get("skills")

            if profile_picture := request.FILES.get("profile-picture"):
                user.profile_picture = profile_picture

            user.save()
            messages.success(request, _("Profile updated."))
            return redirect("profile")

        except Exception as e:
            messages.error(request, _(f"Error: {str(e)}"))

    context = {
        "reports_count": Report.objects.filter(student=user).count(),
        "projects_count": Project.objects.filter(students=student).count() if student else 0,
    }
    return render(request, "profile.html", context)

# ---------------------------
# Report Views
# ---------------------------

@login_required
@require_http_methods(["GET", "POST"])
def create_report(request):
    """Optimized report creation with validation."""
    if request.user.user_type != User.UserType.STUDENT:
        raise PermissionDenied(_("Only students can submit reports."))

    if request.method == "POST":
        try:
            student = get_object_or_404(StudentProfile, user=request.user)
            data = request.POST
            
            Report.objects.create(
                title=data.get("title"),
                tags=data.get("tags"),
                hours_worked=float(data.get("hours", 0)),
                status=data.get("status"),
                content=data.get("content"),
                student=request.user,
                option=student.option,
            )
            
            messages.success(request, _("Report submitted."))
            return redirect("reports")

        except Exception as e:
            messages.error(request, _(f"Error: {str(e)}"))

    reports = Report.objects.filter(student=request.user).order_by("-created")[:5]
    return render(request, "create-report.html", {"reports": reports})

@login_required
def report_view(request, pk):
    """Secure report viewing with proper permission checks."""
    report = get_object_or_404(Report, id=pk)
    
    if request.user.user_type == User.UserType.MENTOR:
        mentor = get_object_or_404(MentorProfile, user=request.user)
        if report.option != mentor.option:
            raise PermissionDenied(_("You can only view reports from your option."))
        
        if request.method == "POST":
            report.mark = request.POST.get('mark')
            report.save()
            messages.success(request, _("Mark assigned to report successfully."))
            
        return render(request, "view-report.html", {"report": report})
    
    elif request.user.user_type == User.UserType.STUDENT:
        if report.student != request.user:
            raise PermissionDenied(_("You can only view your own reports."))
        return render(request, "view-report.html", {"report": report})
    
    raise PermissionDenied(_("Unauthorized access."))

@login_required
@require_http_methods(["GET", "POST"])
def edit_report(request, pk):
    """Edit a report."""
    report = get_object_or_404(Report, pk=pk, student=request.user)
    if request.method == "POST":
        data = request.POST
        report.title = data.get("title")
        report.tags = data.get("tags")
        report.hours_worked = float(data.get("hours", 0))
        report.status = data.get("status")
        report.content = data.get("content")
        report.save()
        messages.success(request, _("Report updated successfully."))
        return redirect("report-view", pk=pk)
    return render(request, "create-report.html", {"report": report})

@login_required
@require_http_methods(["POST", "GET"])
def delete_report(request, pk):
    """Delete a report."""
    report = get_object_or_404(Report, pk=pk, student=request.user)
    if request.method == "POST":
        report.delete()
        messages.success(request, _("Report deleted."))
        return redirect("reports")
    return render(request, "delete.html", {"report": report})

@login_required
def sample_report(request):
    """Show a sample report page."""
    return render(request, "sample.html")

@login_required
def all_users(request):
    """List all classmates (students)."""
    classmates = StudentProfile.objects.exclude(user=request.user).select_related('user', 'option')
    return render(request, "classmates.html", {"classmates": classmates})

# ---------------------------
# Course Views
# ---------------------------

@login_required
def courses(request):
    """Optimized course view with prefetching and caching."""
    user = request.user

    if user.user_type == User.UserType.STUDENT:
        student = get_object_or_404(StudentProfile, user=user)

        courses = Course.objects.filter(option=student.option).order_by("order")
        progress = StudentCourseProgress.objects.filter(
            student=student
        ).select_related('course').in_bulk()

        # Ensure Course has an 'id' attribute (Django adds it by default)
        next_course = next((c for c in courses if getattr(c, "id", None) not in progress or not progress[getattr(c, "id", None)].completed), None)

        context = {
            "all_courses": courses,
            "next_course": next_course,
            "completed_ids": {cid for cid, p in progress.items() if p.completed},
            "reactions": EmojiReaction.objects.filter(student=student).select_related('course'),
        }
        return render(request, "course-page.html", context)
    else:
        # Always return an HttpResponse for non-student users
        messages.error(request, _("Only students can access courses."))
        return redirect("home")


@login_required
@require_http_methods(["POST"])
def react_course(request, course_id):
    """Optimized emoji reaction handling with AJAX."""
    if request.user.user_type != User.UserType.STUDENT:
        return JsonResponse({"status": "failed", "error": _("Unauthorized")}, status=403)

    emoji = request.POST.get("emoji")
    if not emoji:
        return JsonResponse({"status": "failed", "error": _("Invalid emoji")}, status=400)

    try:
        with transaction.atomic():
            student = get_object_or_404(StudentProfile, user=request.user)
            course = get_object_or_404(Course, id=course_id)
            
            EmojiReaction.objects.create(student=student, course=course, emoji=emoji)
            StudentCourseProgress.objects.filter(
                student=student, course=course
            ).update(reacted=True)
            
            return JsonResponse({"status": "success"})
    except Exception as e:
        return JsonResponse({"status": "failed", "error": str(e)}, status=400)

# ---------------------------
# Notification Views
# ---------------------------

@login_required
def view_notifications(request):
    """Optimized notification view with bulk update."""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    Notification.objects.filter(
        user=request.user, is_read=False
    ).update(is_read=True)
    
    return render(request, "notifications.html", {"notifications": notifications[:50]})

# ---------------------------
# Utility Functions
# ---------------------------

def get_status_color(status):
    """Helper function for status colors."""
    return {
        "on-track": "#10b981",
        "at-risk": "#f59e0b",
        "blocked": "#ef4444",
        "completed": "#3b82f6",
    }.get(status, "#6b7280")