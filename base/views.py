from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
from .models import User, Options, Projects, Tasks, Reports
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Create your views here.
def get_status_color(status):
    if status =='on-track':
        return '#10b981'        
    elif status=='at-risk':
        return '#f59e0b'
    elif status == 'blocked':
        return'#ef4444'
    elif status=='completed':
        return '#3b82f6'
    else:
        return '#6b7280'

@login_required(login_url='login')
def index(request):
    user=request.user
    reports=Reports.objects.filter(student=user)
    reports_fill=Reports.objects.filter(student=request.user, status='completed')
    tasks=Tasks.objects.filter(student=user)
    projects=Projects.objects.filter(students=user)   
    if reports.count()== 0:
        average_score=0
        skill_score=0
    
    else:  
        average_score=(reports_fill.count()/reports.count())*100
        skill_score=(reports.count()/7)*100
    
    
    context={
        'reports':reports,
        'tasks':tasks,
        'projects':projects,
        'reports_count':reports.count(),
        'tasks_count':tasks.count(),
        'projects_count':projects.count(),
        'average_score':round(average_score, 2),
        'skill_score':round(skill_score, 2)
        
    }
    return render(request, 'index.html', context)

def signup(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    
    try:
        options=Options.objects.all()
        if request.method == "POST":
            username=request.POST.get('username')
            first_name=request.POST.get('first-name')
            last_name=request.POST.get('last-name')
            email=request.POST.get('email')
            phone=request.POST.get('phone')
            option=request.POST.get('option')
            password=request.POST.get('password')
            
            
            
            try:
                if User.objects.filter(email=email, username=username, phone=phone).exists():
                    messages.error(request, 'Username or Email already in use')
                    return redirect('signup')
                else:
                    user=User.objects.create_user(username=username, password=password, email=email, phone=phone, first_name=first_name, last_name=last_name, option=Options.objects.filter(name=option)[:1].get())
                    login(request, user)
                    messages.success(request, 'Welcome')
                    return redirect('home')
            except Exception as e:
                messages.error(request, str(e))
                return redirect('signup')
        context={
            'options':options
        }
            
        return render(request, 'signup.html', context)
                
    except Exception as e:
        messages.error(request, str(e))
        return redirect('signup')
    
def login_user(request):
    if request.user.is_authenticated:
        return redirect('home')
    try:
        
        if request.method == "POST":
            username=request.POST.get('username')
            password=request.POST.get('password')

            try:
                User.objects.get(username=username)
            except Exception as e:
                messages.error(request, str(e))
                messages.error(request, 'User not found')
                return redirect('login')
            user=authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Invalid creditials')
                return redirect('login')
        
            
        return render(request, 'login.html')
                
    except Exception as e:
        messages.error(request, str(e))
        return redirect('login')
    
    
@login_required(login_url='login')
def logout_user(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def create_report(request):
    options=Options.objects.all()
    reports=Reports.objects.filter(student=request.user).order_by('-created')
    
    
    
    if request.method == 'POST':
        try:
            title=request.POST.get('title')
            tags=request.POST.get('tags')
            hourse_worked=float(str(request.POST.get('hours')).replace('(', '').replace(',', '').replace(')', ''))
            status=request.POST.get('status')
            content=request.POST.get('content')
            student=request.user
            option=Options.objects.get(name=request.user.option.name)
            
            report=Reports.objects.create(
            title=title,
            tags=tags,
            hourse_worked=hourse_worked,
            status=status,
            content=content,
            student=student,
            option=option
 
        )
            report.save()
            messages.success(request, 'report submitted')
            return redirect('reports')
        except Exception as e:
            messages.error(request, str(e))
            return redirect('reports')
        
    context={
            'options':options,
            'reports':reports,
            
        }      
        
    return render(request, 'create-report.html', context)

@login_required(login_url='login')
def edit_report(request, pk):
    
    options=Options.objects.all()
    reports=Reports.objects.filter(student=request.user).order_by('-created')
    report=Reports.objects.get(id=pk)
    
    
    
    
    if request.method == 'POST':
        try:
            title=request.POST.get('title')
            tags=request.POST.get('tags')
            hourse_worked=request.POST.get('hours')
            status=request.POST.get('status')
            content=request.POST.get('content')
            
            option=Options.objects.get(name=request.user.option.name)
            
            try:
                report.title=title
                report.tags=tags
                report.hourse_worked=hourse_worked
                report.status=status
                report.content=content
                
                report.option=option
            except ValueError as e:
                
                messages.error(request, str(e))
                return redirect('reports')
            
            
 
        
            report.save()
            messages.success(request, 'report submitted')
            
            return redirect('reports')
        except Exception as e:
            messages.error(request, str(e))
            return redirect('reports')
        
    context={
            'options':options,
            'reports':reports,
            'report':report,
            
        }      
        
    return render(request, 'create-report.html', context)

@login_required(login_url='login')
def delete_report(request, pk):
    report=Reports.objects.get(id=pk)
    if request.method == 'POST':
        report.delete()
        messages.success(request, 'report deleted')
        return redirect('reports')
    context={
        'obj':report
    }
    
    return render(request, 'create-report.html', context)
    
    
@login_required(login_url='login')
def user_profile(request):
    reports=Reports.objects.filter(student=request.user)
    
    projects=Projects.objects.filter(students=request.user)  
    user=User.objects.get(id=request.user.id)
    
    if request.method == "POST":
            username=request.POST.get('username')
            first_name=request.POST.get('first-name')
            last_name=request.POST.get('last-name')
            email=request.POST.get('email')
            phone=request.POST.get('phone')
            bio=request.POST.get('about')
            skills=request.POST.get('skills')
            
            
            
            
            
            user.username=username
            user.email=email
            user.phone=phone
            user.first_name=first_name
            user.last_name=last_name
            user.bio=bio
            user.skills=skills
            user.save()
                    
            messages.success(request, 'Profile Updated')
            return redirect('profile')
            
    context={
        'reports':reports,
        'reports_count':reports.count(),
        'projects':projects,
        'projects_count':projects.count()
        
    }
    
    return render(request, 'profile.html', context)

@login_required(login_url='login')
def report(request, pk):
    reports=Reports.objects.filter(student=request.user)
    report=Reports.objects.get(id=pk)
    context={
        'report':report,
        'reports':reports
    }
    return render(request, 'report.html', context)

def sample_report(request):
    return render(request, 'sample.html')

def all_users(request):
    users=User.objects.all()
    context={
        'users':users
    }
    return render(request, 'classmates.html', context)
    
