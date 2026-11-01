from django.shortcuts import render, get_object_or_404
from .models import Course

def home_page_view(request):
    courses = Course.objects.all()
    return render(request, 'blog/home.html', {'courses': courses})

def course_page_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'blog/course_page.html', {'course': course})