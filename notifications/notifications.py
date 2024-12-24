from .models import Notification

def send_notification_to_instructor(instructor, course, customer):
  # Logic to create notification for the instructor
  Notification.objects.create(
    user=instructor,
    title="New Course Purchase",
    message=f"{customer.user.username} has purchased your course {course.title}",
    notification_type=Notification.ALERT
  )

def send_notification_to_customer(customer, course, instructor):
  # Logic to create notification for the customer
  Notification.objects.create(
    user=customer.user,
    title="Purchase Conformation",
    message=f"You have successfully purchased the course {course.title} by instructor {instructor.first_name}",
    notification_type=Notification.MESSAGE
  )

def send_promotional_notification(user, title, message):
  Notification.object.create(
    user=user,
    title=title,
    message=message,
    notification_type=Notification.PROMOTION
  )

def send_course_completion_notification(instructor, course, student):
  Notification.objects.create(
    user=instructor,
    title="Course Completed",
    message=f"{student.username} has completed the course {course.title}.",
    notification_type=Notification.ALERT
  )