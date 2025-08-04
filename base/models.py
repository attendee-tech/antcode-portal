from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class Option(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name=_("Option Name"))

    class Meta:
        verbose_name = _("Option")
        verbose_name_plural = _("Options")
        ordering = ["name"]  # Default ordering

    def __str__(self):
        return self.name


class User(AbstractUser):
    class UserType(models.TextChoices):
        STUDENT = "student", _("Student")
        MENTOR = "mentor", _("Mentor")

    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.STUDENT,
        verbose_name=_("User Type"),
    )
    phone = models.CharField(
        max_length=20, blank=True, default="670000000", verbose_name=_("Phone Number")
    )
    bio = models.TextField(max_length=1000, blank=True, verbose_name=_("Biography"))
    skills = models.CharField(max_length=500, blank=True, verbose_name=_("Skills"))
    profile_picture = models.ImageField(
        upload_to="user/profile_pictures/",
        blank=True,
        null=True,
        verbose_name=_("Profile Picture"),
    )

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        indexes = [
            models.Index(fields=["user_type"]),
            models.Index(fields=["last_name", "first_name"]),
        ]

    @property
    def name_abb(self):
        """Returns initials of the user's name."""
        if self.first_name and self.last_name:
            return f"{self.first_name[0].upper()}{self.last_name[0].upper()}"
        return self.username[0:2].upper()

    def clean(self):
        """Prevent user_type switch if profile exists."""
        if self.pk:
            orig = User.objects.get(pk=self.pk)
            if orig.user_type != self.user_type:
                if self.user_type == User.UserType.MENTOR and hasattr(
                    self, "student_profile"
                ):
                    raise ValidationError(
                        _("Cannot change user type to Mentor, student profile exists.")
                    )
                if self.user_type == User.UserType.STUDENT and hasattr(
                    self, "mentor_profile"
                ):
                    raise ValidationError(
                        _("Cannot change user type to Student, mentor profile exists.")
                    )
        super().clean()

    def __str__(self):
        return f"{self.get_full_name() or self.username}"


class MentorProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="mentor_profile",
        verbose_name=_("User"),
    )
    option = models.OneToOneField(
        Option,
        on_delete=models.CASCADE,
        unique=True,
        related_name="mentor",
        verbose_name=_("Option"),
    )
    expertise = models.CharField(
        max_length=255, blank=True, verbose_name=_("Expertise")
    )

    class Meta:
        verbose_name = _("Mentor Profile")
        verbose_name_plural = _("Mentor Profiles")

    def clean(self):
        """Validate that the user is actually a mentor."""
        if self.user.user_type != User.UserType.MENTOR:
            raise ValidationError(_("Assigned user is not a Mentor"))
        super().clean()

    def __str__(self):
        return _("Mentor: %(name)s (Option: %(option)s)") % {
            "name": self.user.get_full_name(),
            "option": self.option.name,
        }


class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile",
        limit_choices_to={"user_type": User.UserType.STUDENT},
        verbose_name=_("User"),
    )
    option = models.ForeignKey(
        Option,
        on_delete=models.CASCADE,
        related_name="students",
        verbose_name=_("Option"),
    )

    class Meta:
        verbose_name = _("Student Profile")
        verbose_name_plural = _("Student Profiles")
        unique_together = (
            "user",
            "option",
        )  # Prevent duplicate student-option assignments

    def clean(self):
        """Validate that the user is actually a student."""
        if self.user.user_type != User.UserType.STUDENT:
            raise ValidationError(_("Assigned user is not a Student"))
        super().clean()

    def __str__(self):
        return _("Student: %(name)s") % {"name": self.user.get_full_name()}


class Project(models.Model):
    name = models.CharField(max_length=50, verbose_name=_("Project Name"))
    option = models.ForeignKey(
        Option,
        on_delete=models.CASCADE,
        related_name="projects",
        verbose_name=_("Option"),
    )
    students = models.ManyToManyField(
        StudentProfile, related_name="projects", verbose_name=_("Students")
    )
    mentor = models.ForeignKey(
        MentorProfile,
        on_delete=models.CASCADE,
        related_name="projects",
        verbose_name=_("Mentor"),
    )
    content = models.TextField(max_length=2000, blank=True, verbose_name=_("Content"))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    due_date = models.DateTimeField(verbose_name=_("Due Date"))

    class Meta:
        verbose_name = _("Project")
        verbose_name_plural = _("Projects")
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["option"]),
            models.Index(fields=["due_date"]),
        ]

    def __str__(self):
        return self.name


class Task(models.Model):
    name = models.CharField(max_length=50, verbose_name=_("Task Name"))
    option = models.ForeignKey(
        Option, on_delete=models.CASCADE, related_name="tasks", verbose_name=_("Option")
    )
    students = models.ManyToManyField(
        StudentProfile, related_name="tasks", verbose_name=_("Students")
    )
    mentor = models.ForeignKey(
        MentorProfile,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name=_("Mentor"),
    )
    content = models.TextField(max_length=2000, blank=True, verbose_name=_("Content"))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    due_date = models.DateTimeField(verbose_name=_("Due Date"))

    class Meta:
        verbose_name = _("Task")
        verbose_name_plural = _("Tasks")
        ordering = ["due_date"]
        indexes = [
            models.Index(fields=["option"]),
            models.Index(fields=["due_date"]),
        ]

    def __str__(self):
        return self.name


class Report(models.Model):
    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("submitted", _("Submitted")),
        ("reviewed", _("Reviewed")),
        ("approved", _("Approved")),
    ]

    title = models.CharField(max_length=50, verbose_name=_("Title"))
    tags = models.CharField(max_length=100, verbose_name=_("Tags"))
    hours_worked = models.FloatField(default=0.0, verbose_name=_("Hours Worked"))
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default="draft", verbose_name=_("Status")
    )
    content = models.TextField(max_length=2000, blank=True, verbose_name=_("Content"))
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reports",
        limit_choices_to={"user_type": User.UserType.STUDENT},
        verbose_name=_("Student"),
    )
    option = models.ForeignKey(
        Option,
        on_delete=models.CASCADE,
        related_name="reports",
        verbose_name=_("Option"),
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    mark = models.IntegerField(default=0, verbose_name=_("Mark"))

    class Meta:
        verbose_name = _("Report")
        verbose_name_plural = _("Reports")
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["option"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created"]),
        ]

    @property
    def summary(self):
        """Returns first 10 words of content as summary."""
        return " ".join(self.content.split()[:10])

    def __str__(self):
        return f"{self.title} - {self.option.name}"


class Course(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    description = models.TextField(verbose_name=_("Description"))
    category = models.CharField(max_length=100, verbose_name=_("Category"))
    tech_field = models.CharField(max_length=100, verbose_name=_("Tech Field"))
    thumbnail = models.URLField(verbose_name=_("Thumbnail URL"))
    video_id = models.CharField(max_length=100, verbose_name=_("Video ID"))
    duration = models.CharField(max_length=20, verbose_name=_("Duration"))
    views = models.CharField(max_length=50, verbose_name=_("Views"))
    date = models.CharField(max_length=50, verbose_name=_("Date"))
    instructor = models.CharField(max_length=255, verbose_name=_("Instructor"))
    option = models.ForeignKey(
        Option,
        on_delete=models.CASCADE,
        related_name="courses",
        verbose_name=_("Option"),
    )
    order = models.PositiveIntegerField(verbose_name=_("Order"))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        verbose_name = _("Course")
        verbose_name_plural = _("Courses")
        ordering = ["order"]
        indexes = [
            models.Index(fields=["option"]),
            models.Index(fields=["tech_field"]),
            models.Index(fields=["order"]),
        ]

    def __str__(self):
        return f"{self.title} (Order {self.order})"


class StudentCourseProgress(models.Model):
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="course_progress",
        verbose_name=_("Student"),
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="student_progress",
        verbose_name=_("Course"),
    )
    completed = models.BooleanField(default=False, verbose_name=_("Completed"))
    reacted = models.BooleanField(default=False, verbose_name=_("Reacted"))
    assigned_date = models.DateTimeField(verbose_name=_("Assigned Date"))

    class Meta:
        verbose_name = _("Student Course Progress")
        verbose_name_plural = _("Student Course Progress")
        unique_together = ("student", "course")  # Prevent duplicate progress records
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["course"]),
            models.Index(fields=["completed"]),
        ]

    def __str__(self):
        return f"{self.student.user.username} - {self.course.title}"


class EmojiReaction(models.Model):
    EMOJIS = [
        ("👍", _("Like")),
        ("❤️", _("Love")),
        ("🔥", _("Fire")),
        ("😮", _("Surprised")),
        ("💡", _("Insightful")),
    ]

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="emoji_reactions",
        verbose_name=_("Student"),
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="emoji_reactions",
        verbose_name=_("Course"),
    )
    emoji = models.CharField(max_length=5, choices=EMOJIS, verbose_name=_("Emoji"))
    reacted_on = models.DateTimeField(auto_now_add=True, verbose_name=_("Reacted On"))

    class Meta:
        verbose_name = _("Emoji Reaction")
        verbose_name_plural = _("Emoji Reactions")
        unique_together = ("student", "course")  # One reaction per student per course
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["course"]),
        ]

    def __str__(self):
        return f"{self.student.user.username} reacted to {self.course.title}"


class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("User"),
    )
    message = models.TextField(verbose_name=_("Message"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    is_read = models.BooleanField(default=False, verbose_name=_("Is Read"))

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["is_read"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.message[:30]}"
