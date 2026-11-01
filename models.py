from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Avg

class CourseQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status='published')

class CourseManager(models.Manager):
    def get_queryset(self):
        return CourseQuerySet(self.model, using=self._db)

    def get_new_courses(self, limit=5):
        return self.get_queryset().order_by('-created_at')[:limit]

    def get_popular_courses(self, limit=5):
        from django.db.models import Count
        return self.get_queryset().annotate(student_count=Count('students')).order_by('-student_count')[:limit]

class Instructor(models.Model):
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    email = models.EmailField(unique=True, verbose_name="Email")
    specialization = models.CharField(max_length=150, verbose_name="Специализация")
    rating = models.DecimalField(
        max_digits=3, decimal_places=1,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        default=0.0, verbose_name="Рейтинг"
    )
    start_date = models.DateField(verbose_name="Дата начала работы")
    bio = models.TextField(blank=True, verbose_name="Биография")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Преподаватель"
        verbose_name_plural = "Преподаватели"
        ordering = ['-rating', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.specialization})"

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slug (URL)")
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='subcategories', verbose_name="Родительская категория"
    )

    class Meta:
        verbose_name = "Категория курса"
        verbose_name_plural = "Категории курсов"

    def __str__(self):
        return self.name

class Course(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Начальный'),
        ('intermediate', 'Средний'),
        ('advanced', 'Продвинутый'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликован'),
    ]

    title = models.CharField(max_length=200, verbose_name="Название курса")
    instructor = models.ForeignKey(Instructor, on_delete=models.PROTECT, related_name='courses', verbose_name="Преподаватель")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='courses', verbose_name="Категория")
    description = models.TextField(verbose_name="Описание")
    duration_hours = models.PositiveIntegerField(verbose_name="Длительность (в часах)")
    difficulty = models.CharField(max_length=15, choices=DIFFICULTY_CHOICES, default='beginner', verbose_name="Уровень сложности")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft', verbose_name="Статус")
    max_students = models.PositiveIntegerField(null=True, blank=True, verbose_name="Макс. количество мест")

    objects = CourseManager()

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"

    def __str__(self):
        return self.title

    def get_available_spots(self):
        if self.max_students is None:
            return "Безлимитно"
        enrolled_count = self.students.count()
        available = self.max_students - enrolled_count
        return max(0, available)

    def get_average_rating(self):
        average = self.reviews.aggregate(Avg('rating'))['rating__avg']
        if average is None:
            return 0.0
        return round(average, 1)

class Student(models.Model):
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    email = models.EmailField(unique=True, verbose_name="Email")
    registration_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")
    courses = models.ManyToManyField(Course, through='Enrollment', related_name='students', verbose_name="Курсы")

    class Meta:
        verbose_name = "Студент"
        verbose_name_plural = "Студенты"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_completed_courses(self):
        return self.courses.filter(enrollment__status='completed')

class Enrollment(models.Model):
    PROGRESS_CHOICES = [
        ('in_progress', 'В процессе'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="Студент")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="Курс")
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата записи")
    status = models.CharField(max_length=15, choices=PROGRESS_CHOICES, default='in_progress', verbose_name="Статус")
    progress = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Прогресс (%)")
    grade = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="Оценка")

    class Meta:
        verbose_name = "Запись на курс"
        verbose_name_plural = "Записи на курсы"

    def __str__(self):
        return f"{self.student} -> {self.course} ({self.get_status_display()})"

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons', verbose_name="Курс")
    title = models.CharField(max_length=200, verbose_name="Название урока")
    content = models.TextField(verbose_name="Содержание урока")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядковый номер")

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        ordering = ['order', 'id']

    def __str__(self):
        return f"Урок {self.order}: {self.title} (Курс: {self.course.title})"


class Review(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews', verbose_name="Курс")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='reviews', verbose_name="Студент")
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Оценка от 1 до 5"
    )
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ['-created_at']

    def __str__(self):
        return f"Отзыв от {self.student} на курс {self.course} (Оценка: {self.rating})"