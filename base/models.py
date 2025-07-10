from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class Options(models.Model):
    name=models.CharField(blank=False, max_length=50)
    
    def __str__(self):
        return self.name
    


class User(AbstractUser):
    first_name=models.CharField(blank=False, max_length=50)
    last_name=models.CharField(blank=False, max_length=50)
    email=models.EmailField(blank=False, max_length=254)
    phone=models.IntegerField(default=670000000)
    bio=models.TextField(max_length=1000, blank=True)
    skills=models.CharField(max_length=500, blank=True)
    profile_picture=models.ImageField(upload_to='user/',  max_length=None,)
    
    option=models.ForeignKey(Options,  on_delete=models.CASCADE)
    
    @property
    def name_abb(self):
        return self.first_name[0].upper() + self.last_name[0].upper()
    
    def __str__(self):
        return self.first_name + ' ' + self.last_name
    
class Reports(models.Model):
    title=models.CharField(blank=False, max_length=50)
    tags=models.CharField(blank=False, max_length=100)
    hourse_worked=models.FloatField(default=0.0)
    status=models.CharField(blank=False, max_length=50)
    content=models.TextField(max_length=2000, blank=True)
    student=models.ForeignKey(User, on_delete=models.CASCADE)
    option=models.ForeignKey(Options, on_delete=models.CASCADE)
    created=models.DateTimeField(auto_now_add=True)
    updated=models.DateTimeField(auto_now=True)
    
    @property
    def summary(self):
        return ' '.join(self.content.split()[:10])
    
    def __str__(self):
        return self.title + ' - ' + self.option.name    

class Projects(models.Model):
    name=models.CharField(blank=False, max_length=50)
    students=models.ManyToManyField(User)
    content=models.TextField(max_length=2000, blank=True)
    option=models.ForeignKey(Options, on_delete=models.CASCADE)
    created=models.DateTimeField(auto_now=False)
    
    def __str__(self):
        return self.name
    

class Tasks(models.Model):
    name=models.CharField(blank=False, max_length=50)
    student=models.ForeignKey(User, on_delete=models.CASCADE)
    content=models.TextField(max_length=2000, blank=True)
    option=models.ForeignKey(Options, on_delete=models.CASCADE)
    created=models.DateTimeField(auto_now=False)
    
    def __str__(self):
        return self.name
    

