from ninja import Schema
from typing import Optional
from datetime import datetime
from decimal import Decimal


# --- Студенти ---
class StudentIn(Schema):
    """
    Схема вхідних даних для створення нового студента.
    """
    first_name: str
    """Ім'я студента (обов'язкове поле)."""

    last_name: str
    """Прізвище студента (обов'язкове поле)."""

    student_id_number: str
    """Унікальний ідентифікаційний номер студента (обов'язкове поле)."""

    email: str
    """Унікальна електронна адреса студента (обов'язкове поле)."""


class StudentOut(Schema):
    """
    Схема вихідних даних для представлення об'єкта Student.
    """
    id: int
    """Унікальний ідентифікатор студента."""

    first_name: str
    """Ім'я студента."""

    last_name: str
    """Прізвище студента."""

    student_id_number: str
    """Ідентифікаційний номер студента."""

    email: str
    """Електронна адреса студента."""


# --- Курси ---
class CourseIn(Schema):
    """
    Схема вхідних даних для створення нового курсу.
    """
    name: str
    """Назва курсу (обов'язкове поле)."""

    description: Optional[str] = None
    """Опис курсу (опціонально)."""

    instructor: str
    """Ім'я викладача (обов'язкове поле)."""


class CourseOut(Schema):
    """
    Схема вихідних даних для представлення об'єкта Course.
    """
    id: int
    """Унікальний ідентифікатор курсу."""

    name: str
    """Назва курсу."""

    instructor: str
    """Ім'я викладача."""

    average_score: Optional[Decimal] = None
    """
    Середня оцінка, отримана студентами на цьому курсі. 
    Поле може бути обчислене анотацією у Django QuerySet (Optional).
    """


# --- Реєстрація ---
class EnrollmentIn(Schema):
    """
    Схема вхідних даних для реєстрації студента на курс.
    """
    student_id: int
    """ID студента для реєстрації."""

    course_id: int
    """ID курсу для реєстрації."""


class EnrollmentOut(Schema):
    """
    Схема вихідних даних для представлення об'єкта Enrollment.
    """
    id: int
    """Унікальний ідентифікатор реєстрації."""

    student_name: str
    """Повне ім'я зареєстрованого студента (вирішується через метод resolve_student_name)."""

    course_name: str
    """Назва курсу (вирішується через метод resolve_course_name)."""

    enrollment_date: datetime
    """Дата та час реєстрації."""

    @staticmethod
    def resolve_student_name(obj):
        """Отримує повне ім'я студента з пов'язаного об'єкта Student."""
        return f"{obj.student.first_name} {obj.student.last_name}"

    @staticmethod
    def resolve_course_name(obj):
        """Отримує назву курсу з пов'язаного об'єкта Course."""
        return obj.course.name


# --- Оцінки ---
class GradeIn(Schema):
    """
    Схема вхідних даних для додавання нової оцінки.
    """
    score: int
    """Числове значення оцінки (від 0 до 100)."""

    exam_name: Optional[str] = "Final Exam"
    """Назва іспиту або завдання (за замовчуванням "Final Exam")."""


class GradeOut(Schema):
    """
    Схема вихідних даних для представлення об'єкта Grade.
    """
    id: int
    """Унікальний ідентифікатор оцінки."""

    student_name: str
    """Прізвище студента, який отримав оцінку (вирішується через метод resolve_student_name)."""

    course_name: str
    """Назва курсу, до якого відноситься оцінка (вирішується через метод resolve_course_name)."""

    score: int
    """Числове значення оцінки."""

    exam_name: str
    """Назва іспиту."""

    @staticmethod
    def resolve_student_name(obj):
        """Отримує прізвище студента через об'єкт Enrollment."""
        return f"{obj.enrollment.student.last_name}"

    @staticmethod
    def resolve_course_name(obj):
        """Отримує назву курсу через об'єкт Enrollment."""
        return obj.enrollment.course.name
