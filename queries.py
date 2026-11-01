from django.db.models import Count, Avg, Q, F
from blog.models import Course, Instructor, Enrollment, Category, Student

def get_published_courses():
    return Course.objects.filter(status='published')

def get_courses_by_level(level):
    return Course.objects.filter(difficulty=level)

def get_instructor_courses(instructor_id):
    return Course.objects.filter(instructor_id=instructor_id)

def get_popular_courses(min_students):
    return Course.objects.annotate(num_students=Count('students')).filter(num_students__gte=min_students)

def get_student_active_courses(student_id):
    return Course.objects.filter(
        enrollment__student_id=student_id,
        enrollment__status='in_progress'
    )

def get_category_with_subcategories(category_id):

    return Category.objects.filter(Q(id=category_id) | Q(parent_id=category_id))

def get_expensive_courses(min_price):
    return Course.objects.filter(price__gt=min_price)

def get_instructors_by_rating(min_rating):
    return Instructor.objects.filter(rating__gt=min_rating)

def get_courses_with_available_spots():
    return Course.objects.annotate(num_students=Count('students')).filter(
        Q(max_students__isnull=True) | Q(num_students__lt=F('max_students'))
    )

def update_enrollment_progress(enrollment_id, progress):
    Enrollment.objects.filter(id=enrollment_id).update(progress=progress)

def complete_enrollment(enrollment_id, grade):
    Enrollment.objects.filter(id=enrollment_id).update(
        status='completed',
        progress=100,
        grade=grade
    )

def get_student_statistics(student_id):
    stats = Enrollment.objects.filter(student_id=student_id).aggregate(
        total_courses=Count('id'),
        completed_courses=Count('id', filter=Q(status='completed')),
        average_grade=Avg('grade', filter=Q(status='completed'))
    )

    return {
        'total_courses': stats['total_courses'] or 0,
        'completed_courses': stats['completed_courses'] or 0,
        'average_grade': round(stats['average_grade'], 1) if stats['average_grade'] else 0.0
    }

def get_instructor_statistics(instructor_id):

    stats = Course.objects.filter(instructor_id=instructor_id).aggregate(
        total_courses=Count('id', distinct=True),
        total_students=Count('students', distinct=True),
        average_course_grade=Avg('enrollment__grade', filter=Q(enrollment__status='completed'))
    )
    return {
        'total_courses': stats['total_courses'] or 0,
        'total_students': stats['total_students'] or 0,
        'average_course_grade': round(stats['average_course_grade'], 1) if stats['average_course_grade'] else 0.0
    }