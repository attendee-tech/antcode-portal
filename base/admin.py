from django.contrib import admin
from .models import (User, Options, Reports, Tasks, Projects)

# Register your models here.
admin.site.register(User)
admin.site.register(Options)
admin.site.register(Reports)
admin.site.register(Tasks)
admin.site.register(Projects)
