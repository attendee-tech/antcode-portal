from django.contrib import admin
from .models import (User, Option, Report, Task, Project, StudentProfile, MentorProfile)

# Register your models here.
admin.site.register(User)
admin.site.register(Option)
admin.site.register(Report)
admin.site.register(Task)
admin.site.register(Project)
admin.site.register(StudentProfile)
admin.site.register(MentorProfile)
