from django.db.models.signals import post_save, post_delete
from django.conf import settings
from django.dispatch import receiver
from courses.models import Lesson, SectionAttempt, Course, Customer, CourseProgress, Rating, OrderItem, Order, InstructorEarnings
from notifications.notifications import send_notification_to_instructor, send_notification_to_customer


@receiver(post_save, sender=Lesson)
def update_course_progress(sender, instance, **kwargs):
    # Get all CourseProgress instances where this lesson is marked as completed
    course_progresses = CourseProgress.objects.filter(completed_lessons=instance)
    
    for course_progress in course_progresses:
        course_progress.calculate_progress()
        course_progress.save()


@receiver(post_save, sender=Order)
def create_course_progress(sender, instance, created, **kwargs):
    if instance.payment_status == Order.PAYMENT_STATUS_COMPLETE:
        for item in instance.items.all():
            CourseProgress.objects.get_or_create(student=instance.customer, course=item.course)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_customer_for_new_user(sender, instance, created,  **kwargs):
    if created:
        Customer.objects.create(user=instance)


@receiver(post_save, sender=OrderItem)
def update_order_item(sender, instance, created, **kwargs):
    if created:
        # Custom logic to handle post creation of OrderItem
        course = instance.course
        customer = instance.customer
        instructor = instance.instructor

        # Example: Send a notification to the instructor and customer
        send_notification_to_instructor(instructor, course, customer)
        send_notification_to_customer(customer, course, instructor)

@receiver(post_save, sender=OrderItem)
def update_instructor_earnings(sender, instance, created, **kwargs):
    if created:
        instructor = instance.course.instructor
        earnings, created = InstructorEarnings.objects.get_or_create(instructor=instructor)


@receiver(post_save, sender=Rating)
@receiver(post_delete, sender=Rating)
def update_course_rating_count(sender, instance, created, **kwargs):
  instance.course.update_rating_metrics()


@receiver(post_save, sender=Lesson)
def update_section_duration_on_save(sender, instance, **kwargs):
    section = instance.section
    section.update_total_duration()

@receiver(post_delete, sender=Lesson)
def update_section_duration_on_delete(sender, instance, **kwargs):
    section = instance.section
    section.update_total_duration()
