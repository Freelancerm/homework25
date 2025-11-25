from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Course(models.Model):
    """
    Модель, що представляє навчальний курс.
    """
    name = models.CharField(max_length=255, unique=True)
    """Назва курсу (унікальна)."""

    description = models.TextField(blank=True)
    """Детальний опис курсу (необов'язковий)."""

    instructor = models.CharField(max_length=100)
    """Ім'я викладача, який веде курс."""

    def __str__(self):
        """Повертає назву курсу."""
        return self.name


class Student(models.Model):
    """
    Модель, що представляє студента.
    """
    first_name = models.CharField(max_length=100)
    """Ім'я студента."""

    last_name = models.CharField(max_length=100)
    """Прізвище студента."""

    student_id_number = models.CharField(max_length=20, unique=True)
    """Унікальний ідентифікаційний номер студента."""

    email = models.EmailField(unique=True)
    """Унікальна електронна адреса студента."""

    def __str__(self):
        """Повертає повне ім'я студента."""
        return f"{self.first_name} {self.last_name}"


class Enrollment(models.Model):
    """
    Модель, що представляє реєстрацію студента на конкретний курс.
    Це модель, що зв'язує Student та Course (багато-до-багатьох).
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    """Студент, який зареєстрований."""

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    """Курс, на який зареєстрований студент."""

    enrollment_date = models.DateTimeField(auto_now_add=True)
    """Дата та час реєстрації (встановлюється автоматично)."""

    class Meta:
        """
        Обмеження унікальності: гарантує, що кожен студент
        може бути зареєстрований на одному курсі лише один раз.
        """
        unique_together = ('student', 'course')

    def __str__(self):
        """Повертає інформацію про реєстрацію."""
        return f"{self.student.last_name} enrolled in {self.course.name}"


class Grade(models.Model):
    """
    Модель, що зберігає оцінки (результати іспитів) для студента на курсі.
    """
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='grades')
    """Зв'язок з об'єктом Enrollment, до якого відноситься оцінка."""

    score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    """Числове значення оцінки (від 0 до 100)."""

    exam_name = models.CharField(max_length=100, default="Final Exam")
    """Назва іспиту або завдання, за яке виставлена оцінка."""

    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    """Користувач (викладач або адміністратор), який виставив оцінку (може бути NULL)."""

    date_recorded = models.DateTimeField(auto_now_add=True)
    """Дата та час запису оцінки (встановлюється автоматично)."""

    def __str__(self):
        """Повертає інформацію про оцінку, студента та курс."""
        return f"{self.enrollment.student.last_name} got {self.score} on {self.enrollment.course.name}"
