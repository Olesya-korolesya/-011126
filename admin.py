from django.contrib import admin
from .models import Instructor, Category, Course, Student, Enrollment, Lesson, Review

class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 1
    fields = ('student', 'course', 'status', 'progress', 'grade')

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 3

class ReviewInline(admin.TabularInline):
    model = Review
    extra = 1

@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'email', 'specialization', 'rating', 'is_active')
    list_filter = ('is_active', 'specialization')
    search_fields = ('last_name', 'first_name', 'email', 'specialization')
    ordering = ['-rating', 'last_name']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'category', 'price', 'difficulty', 'status', 'display_average_rating', 'display_available_spots')
    list_filter = ('status', 'difficulty', 'category')
    search_fields = ('title', 'description')
    inlines = [EnrollmentInline, LessonInline, ReviewInline]

    def display_average_rating(self, obj):
        return obj.get_average_rating()
    display_average_rating.short_description = "Рейтинг курса"

    def display_available_spots(self, obj):
        return obj.get_available_spots()
    display_available_spots.short_description = "Свободные места"

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'email', 'registration_date')
    search_fields = ('last_name', 'first_name', 'email')
    inlines = [EnrollmentInline]

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    search_fields = ('title',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'rating', 'created_at')
    list_filter = ('rating', 'course')