from ninja import Router
from ninja.errors import HttpError
from django.shortcuts import get_object_or_404
from django.db.models import Avg
from typing import List

from .models import Student, Course, Enrollment, Grade
from .schemas import *
from shared_auth.auth import bearer_auth

# -----------------------------------------------------
# 1. ADMIN ROUTER: CRUD для Студентів та Курсів
# -----------------------------------------------------
admin_router = Router(tags=["Admin: Students & Courses"], auth=bearer_auth)


@admin_router.post("/students/", response={201: StudentOut})
def create_student(request, payload: StudentIn):
    """
    Створює новий запис студента у системі.

    :param request: Об'єкт HttpRequest.
    :param payload: Дані нового студента (name, email, etc.).
    :type payload: StudentIn
    :status 201: Студента успішно створено.
    :return: Об'єкт створеного студента.
    :rtype: StudentOut
    """
    student = Student.objects.create(**payload.dict())
    return 201, student


@admin_router.get("/students/", response=List[StudentOut])
def list_students(request):
    """
    Повертає список усіх студентів, відсортований за прізвищем.

    :param request: Об'єкт HttpRequest.
    :return: Список об'єктів студентів.
    :rtype: List[StudentOut]
    """
    return Student.objects.all().order_by('last_name')


@admin_router.post("/courses/", response={201: CourseOut})
def create_course(request, payload: CourseIn):
    """
    Створює новий курс у каталозі.

    :param request: Об'єкт HttpRequest.
    :param payload: Дані нового курсу (name, code, credits).
    :type payload: CourseIn
    :status 201: Курс успішно створено.
    :return: Об'єкт створеного курсу.
    :rtype: CourseOut
    """
    course = Course.objects.create(**payload.dict())
    return 201, course


@admin_router.get("/courses/", response=List[CourseOut])
def list_courses(request):
    """
    Повертає список усіх курсів.

    Анотує кожен курс середнім балом (average_score), отриманим студентами
    на цьому курсі. Сортується за назвою.

    :param request: Об'єкт HttpRequest.
    :return: Список об'єктів курсів.
    :rtype: List[CourseOut]
    """
    courses = Course.objects.annotate(
        average_score=Avg('enrollments__grades__score')
    ).order_by('name')
    return courses


@admin_router.delete("/courses/{course_id}/", response={204: None})
def delete_course(request, course_id: int):
    """
    Видаляє курс. При видаленні курсу автоматично видаляються всі пов'язані
    реєстрації та оцінки (CASCADE).

    :param request: Об'єкт HttpRequest.
    :param course_id: ID курсу для видалення.
    :type course_id: int
    :raises Http404: Якщо курс не знайдено.
    :status 204: Успішне видалення (без вмісту).
    :return: None.
    """
    course = get_object_or_404(Course, id=course_id)
    course.delete()
    return 204, None


# -----------------------------------------------------
# 2. ENROLLMENT ROUTER: Реєстрація
# -----------------------------------------------------
enrollment_router = Router(tags=["Enrollment"], auth=bearer_auth)


@enrollment_router.post("/", response={201: EnrollmentOut})
def enroll_student(request, payload: EnrollmentIn):
    """
    Реєструє студента на обраний курс.

    Використовує `get_or_create` для запобігання дублюванню реєстрації.

    :param request: Об'єкт HttpRequest.
    :param payload: Дані реєстрації (student_id, course_id).
    :type payload: EnrollmentIn
    :raises Http404: Якщо студент або курс не знайдено.
    :raises HttpError 409: Якщо студент вже зареєстрований на цей курс.
    :status 201: Реєстрація успішно створена.
    :return: Об'єкт створеної реєстрації.
    :rtype: EnrollmentOut
    """
    student = get_object_or_404(Student, id=payload.student_id)
    course = get_object_or_404(Course, id=payload.course_id)

    enrollment, created = Enrollment.objects.get_or_create(
        student=student,
        course=course,
        defaults={'enrollment_date': datetime.now()}
    )
    if not created:
        raise HttpError(409, "Студент вже зареєстрований")

    return 201, enrollment


# -----------------------------------------------------
# 3. GRADING ROUTER: Оцінки та Метрики
# -----------------------------------------------------
grading_router = Router(tags=["Grading & Metrics"], auth=bearer_auth)


@grading_router.post("/{student_id}/{course_id}/", response={201: GradeOut})
def add_grade(request, student_id: int, course_id: int, payload: GradeIn):
    """
    Додає нову оцінку до реєстрації студента на курсі.

    :param request: Об'єкт HttpRequest (з автентифікованим користувачем, який виставляє оцінку).
    :param student_id: ID студента.
    :type student_id: int
    :param course_id: ID курсу.
    :type course_id: int
    :param payload: Дані оцінки (score, exam_name).
    :type payload: GradeIn
    :raises Http404: Якщо реєстрація для цієї пари (student, course) не знайдена.
    :status 201: Оцінка успішно додана.
    :return: Об'єкт створеної оцінки.
    :rtype: GradeOut
    """
    user = request.auth

    enrollment = get_object_or_404(
        Enrollment,
        student_id=student_id,
        course_id=course_id
    )

    grade = Grade.objects.create(
        enrollment=enrollment,
        score=payload.score,
        exam_name=payload.exam_name,
        graded_by=user
    )
    return 201, grade


@grading_router.get("/{student_id}/{course_id}/average/", response={'average_score': float})
def get_student_course_average(request, student_id: int, course_id: int):
    """
    Обчислює середню оцінку, отриману студентом за всі іспити в межах одного курсу.

    :param request: Об'єкт HttpRequest.
    :param student_id: ID студента.
    :type student_id: int
    :param course_id: ID курсу.
    :type course_id: int
    :raises Http404: Якщо реєстрація для цієї пари не знайдена.
    :return: Словник з ключем 'average_score' (float). Повертає 0.0, якщо оцінок немає.
    """
    enrollment = get_object_or_404(
        Enrollment,
        student_id=student_id,
        course_id=course_id
    )

    average = enrollment.grades.aggregate(Avg('score'))

    # Повертаємо 0.0, якщо оцінок немає
    return {'average_score': average['score__avg'] or 0.0}


@grading_router.get("/course/{course_id}/average/", response={'average_score': float})
def get_course_average(request, course_id: int):
    """
    Обчислює середню оцінку за весь курс (тобто середній бал усіх оцінок,
    виставлених усім студентам, зареєстрованим на цьому курсі).

    :param request: Об'єкт HttpRequest.
    :param course_id: ID курсу.
    :type course_id: int
    :raises Http404: Якщо курс не знайдено.
    :return: Словник з ключем 'average_score' (float). Повертає 0.0, якщо оцінок немає.
    """
    course = get_object_or_404(Course, id=course_id)

    # Обчислюємо середнє значення для всіх оцінок, пов'язаних з цим курсом
    average = Grade.objects.filter(
        enrollment__course=course
    ).aggregate(Avg('score'))

    return {'average_score': average['score__avg'] or 0.0}
