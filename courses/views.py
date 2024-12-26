from django.db.utils import IntegrityError
from django.db import transaction
from django.db.models.aggregates import Count
from django.conf import settings
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework import viewsets, status, serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.permissions import IsAdminUser, IsAuthenticated, SAFE_METHODS, AllowAny
from .models import Course, Collection, Promotion, PaymentStatus, Customer, Description, Review, CourseProgress, Lesson, \
    Order, OrderItem, Option, StudentAnswer, StudentScore, Cart, CartItem, Rating, WishList, WishListItem, Section, Question, \
    CompanyOverview, Mission, Vission, Testimonial, FAQ
from .serializers import CourseSerializer, CourseDetailSerializer, CollectionSerializer, PromotionSerializer, \
    InstructorEarningsSerializer, RatingSerializer, DescriptionSerializer, ReviewSerializer, CourseProgressSerializer,CustomerSerializer, \
    InstructorEarnings, LessonSerializer, OrderSerializer, OrderItemSerializer, CartSerializer, CartItemSerializer, \
    WishListItemSerializer, WishListItemSerializer,  PaymentStatusSerializer, WishListSerializer, SectionSerializer, \
    QuestionSerializer, OptionSerializer, CoreValue, StudentAnswerSerializer, CompanyOverviewSerializer, \
    MissionSerializer, VissionSerializer, CoreValueSerializer, StaffMember, TestimonialSerializer, FAQSerializer, StaffMemberSerializer
from .permissions import IsAdminOrReadOnly, ViewCustomerHistoryPermission, IsInstructor, \
    IsStudentOrInstructor, IsInstructorOwner, IsInstructorOrReadOnly, IsStudentOrAdmin, IsInstructorOrAdmin, IsStudentAndPurchasedCourse, IsPreviousSectionCompleted
from .pagination import DefaultPagination
from uuid import uuid4
import logging
import os
import io



logger = logging.getLogger(__name__)

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=True, permission_classes=[ViewCustomerHistoryPermission])
    def history(self, request, pk):
        return Response('Ok')

    @action(detail=False, methods=['GET', 'PUT'], permission_classes=[IsAuthenticated])
    def me(self, request):
        (customer, created) = Customer.objects.get_or_create(user_id=request.user.id)
        if request.method == 'GET':
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        
        elif request.method == 'PUT':
            serializer = CustomerSerializer(customer, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        
    @action(detail=False, methods=['PUT'], permission_classes=[IsAuthenticated])
    def update_profile_picture(self, request):
        try:
            customer = Customer.objects.get(user=request.user)
            user = request.user
            if 'profile_picture' in request.FILES:
                profile_picture = request.FILES['profile_picture']
            
                # Update profile picture for Customer
                customer.profile_picture = profile_picture
                customer.save()
            
                # Update profile picture for User
                user.profile_picture = profile_picture
                user.save()
            
                return Response({'status': 'Profile picture updated'}, status=200)
            return Response({'error': 'No profile picture uploaded'}, status=400)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=404)


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.select_related('instructor', 'collection').all().order_by('id')
    serializer_class = CourseSerializer
    pagination_class = DefaultPagination
    search_fields = ['title']
    ordering_fields = ['price', 'last_update', 'id']
    http_method_names = ['get', 'post', 'delete', 'put', 'patch'] # CRUD

    def get_serializer_context(self):
        return {'request': self.request}

    def destroy(self, request, *args, **kwargs):
        if OrderItem.objects.filter(course_id=kwargs['pk']).exists():
            return Response({'error': 'course cannot be deleted because it is associated with an order item.'}, 
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        ordering = self.request.query_params.get('ordering', None)      
        
        if self.request.user.is_authenticated:
            if self.request.user.role == "instructor":
                return queryset.filter(instructor=self.request.user)
        # For anonymous user, all active courses
        queryset = queryset.filter(is_active=True)
    
        if ordering:
            try:
                queryset = queryset.order_by(ordering)
            except TypeError as e:
                print(f"TypeError: {e}")
                # Handle the error or provide a default ordering
                queryset = queryset.order_by('id')
        return queryset


    @action(detail=True, methods=['get'], permission_classes=[IsInstructorOrAdmin])
    def statistics(self, request, pk=None):
        # Custom action to retrieve the ratingCount and numberOfStudent for specific course
        course = self.get_object()
        data = {
            "rating_count": course.rating_count,
            "numberOfStudents": course.numberOfStudents,
            
        }
        return Response(data)


    def get_permissions(self):
        if self.action == 'destroy':
            self.permission_classes = [IsInstructorOrAdmin]
        elif self.action == 'retrieve' or self.action  == 'list':
            self.permission_classes = [AllowAny]
        elif self.action == 'create':
            self.permission_classes = [IsInstructorOrReadOnly]
        elif self.action == 'update':
            self.permission_classes = [IsInstructor]
        else:
            self.permission_classes = []
        return super().get_permissions()


class FullCourseViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        purchased_course_ids = OrderItem.objects.filter(
            order__customer=user.customer_profile,
            order__payment_status='C'
        ).values_list('course_id', flat=True)
        return Course.objects.filter(id__in=purchased_course_ids).distinct()

    @action(detail=True, methods=['get'], url_path='rating')
    def get_rating(self, request, pk=None):
        course = self.get_object()
        return Response({
            'average_rating': course.get_average_ratings(),
            'rating_count': course.get_rating_count()
        })


class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.annotate(courses_count=Count('courses')).all()
    serializer_class = CollectionSerializer
    permission_classes = [IsAdminOrReadOnly]


class SectionViewSet(viewsets.ModelViewSet):
    serializer_class = SectionSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [IsAuthenticated, IsStudentAndPurchasedCourse | IsInstructorOwner, IsPreviousSectionCompleted]
        elif self.action in ['create', 'update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsInstructorOwner]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def get_queryset(self):
        course_id = self.kwargs['course_pk']
        user = self.request.user

        logger.debug(f"User {user.id} is requesting sections for course {course_id}")

        # Check if the user is an instructor for the course
        if Course.objects.filter(id=course_id, instructor=user).exists():
            logger.debug(f"User {user.id} is the instructor for course {course_id} (Instructor Check)")
            return Section.objects.filter(course_id=course_id)

        # Check if the user is a student who purchased the course
        if self.request.method in SAFE_METHODS:
            logger.debug(f"Checking purchase for course_id: {course_id}, user: {user.id}")
            if OrderItem.objects.filter(
                course_id=course_id,
                order__customer=user.customer_profile,
                order__payment_status='C'
            ).exists():
                logger.debug(f"User {user.id} has purchased course {course_id} (Student Check)")
                return Section.objects.filter(course_id=course_id)
            logger.warning(f"User {user.id} does not have permission to access purchased sections of course {course_id}")
            raise PermissionDenied("You do not have permission to access this course's sections.")

        logger.warning(f"User {user.id} does not have permission to access course {course_id} (No Match)")
        raise PermissionDenied("You do not have permission to access this course's sections.")
    
  
    def complete_section(self, request, pk=None):
        section = self.get_object()
        student = request.user

        # Check if all sections in the course are completed
        total_sections = section.course.section_set.count()
        completed_sections = StudentScore.objects.filter(
            student=student,
            section__course=section.course,
            completed=True
        ).count()
        
        if completed_sections == total_sections:
            # All sections are completed, issue certificate
            return Response({'status': 'Section completed'})
    

    def perform_create(self, serializer):
        course_id = self.kwargs['course_pk']
        course = get_object_or_404(Course, id=course_id)
        serializer.save(course=course)


class BaseLessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer

    def create(self, request, *args, **kwargs):
        print("Creating Lesson:", request.data)  # Print incoming data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context
    
    def update_course_progress(self, request, lesson):
        user = request.user
        # Get or create the CourseProgress instance and ensure it is saved
        course_progress, created = CourseProgress.objects.get_or_create(
        student=user,
        course=lesson.section.course
        )

        # Save the instance to ensure it has an ID before accessing many-to-many relationships
        if created:
            course_progress.save()

        if lesson.opened:
            # Add the lesson to completed_lessons if not already added
            if not course_progress.completed_lessons.filter(id=lesson.id).exists():
                course_progress.completed_lessons.add(lesson)
        else:
            # Remove the lesson from completed_lessons if it exists
            if course_progress.completed_lessons.filter(id=lesson.id).exists():
                course_progress.completed_lessons.remove(lesson)

        # Update and save progress
        course_progress.save()

    
    def get_queryset(self):
        section_id = self.kwargs['section_pk']
        return Lesson.objects.filter(section_id=section_id)
    
    def perform_create(self, serializer):
        section_id = self.kwargs['section_pk']
        section = Section.objects.get(id=section_id)
        order = Lesson.objects.filter(section=section).count() + 1
        lesson = serializer.save(section=section, order=order)

        # Check if the file is a vido and update the duration
        if lesson.file and lesson.file.name.split('.')[-1].lower() in Lesson.VIDEO_EXTENTIONS:
            lesson.save() # Triggers the save method with duration calculate if it's a video

        # Update the number_of_lessons for the section
        section.number_of_lessons += 1
        section.update_total_duration() # Ensure section duration is updated after adding a lesson 
        section.save() # Save the updated section

    def perform_destroy(self, instance):
        section = instance.section
        super().perform_destroy(instance)
        section.number_of_lessons -= 1
        section.update_total_duration() # Update section and course duration after deleting lesson 
        section.save() # Save the updated section


class LessonViewSet(BaseLessonViewSet):
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [IsAuthenticated, IsStudentAndPurchasedCourse | IsInstructorOwner]
        elif self.action in ['mark_as_finished', 'mark_as_unfinished']:
            self.permission_classes = [IsAuthenticated, IsStudentAndPurchasedCourse]
        elif self.action in ['create', 'update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsInstructorOwner]  # Restricted actions for instructors only
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def is_student_with_purchase(self, user, course_id):
        """Check if the user is a student and has purchased the course."""
        has_purchased = OrderItem.objects.filter(
            order__customer=user.customer_profile,
            course_id=course_id,
            order__payment_status='C'
        ).exists()
        logger.debug(f"[Permission Check] Purchase status for user {user.id} and course_id {course_id}: {has_purchased}")
        return has_purchased

    @action(detail=True, methods=['get', 'put'], url_path='mark_as_finished')
    def mark_as_finished(self, request, *args, **kwargs):
        lesson = self.get_object()
        course_id = lesson.section.course.id

        # Debug: Check purchase status
        if not self.is_student_with_purchase(request.user, course_id):
            logger.debug(f"[Forbidden] User {request.user.id} does not have access to course_id {course_id}")
            return Response({'detail': 'You do not have permission to perform this action.'}, status=403)

        # Mark lesson as finished
        lesson.opened = True
        lesson.save()
        self.update_course_progress(request, lesson)
        return Response(LessonSerializer(lesson, context={'request': request}).data)

    @action(detail=True, methods=['get', 'put'], url_path='mark_as_unfinished')
    def mark_as_unfinished(self, request, *args, **kwargs):
        lesson = self.get_object()
        course_id = lesson.section.course.id

        # Debug: Check purchase status
        if not self.is_student_with_purchase(request.user, course_id):
            logger.debug(f"[Forbidden] User {request.user.id} does not have access to course_id {course_id}")
            return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)

        # Mark lesson as unfinished
        lesson.opened = False
        lesson.save()
        self.update_course_progress(request, lesson)
        return Response(LessonSerializer(lesson, context={'request': request}).data)

# from django.urls import reverse
# from django.http import HttpResponseRedirect

# class QuestionViewSet(viewsets.ModelViewSet):
#     serializer_class = QuestionSerializer

#     def get_permissions(self):
#         if self.action in ['list', 'retrieve']:
#             self.permission_classes = [IsAuthenticated, IsStudentAndPurchasedCourse | IsInstructorOwner]
#         elif self.action in ['create', 'update', 'destroy']:
#             self.permission_classes = [IsAuthenticated, IsInstructorOwner]
#         else:
#             self.permission_classes = [IsAuthenticated]
#         return super().get_permissions()

#     def get_queryset(self):
#          section_id = self.kwargs.get('section_pk')
#          if not section_id:
#              raise PermissionDenied("Section ID is missing in the request.")

#          user = self.request.user

#          # Instructor access
#          if Section.objects.filter(id=section_id, course__instructor=user).exists():
#              return Question.objects.filter(section_id=section_id)

#          # Student access
#          if OrderItem.objects.filter(
#              course_id=Section.objects.get(id=section_id).course_id,
#              order__customer=user.customer_profile,
#              order__payment_status='C'
#             ).exists():
#              return Question.objects.filter(section_id=section_id)

#          # No access
#          raise PermissionDenied("You do not have permission to access this section's questions.")

#     @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated], url_path='answer')
#     def question_answer(self, request, course_pk=None, section_pk=None, pk=None):
#          question = self.get_object()
#          option_id = request.data.get('option_id')
#          student = request.user

#          if not option_id:
#              return Response({'error': 'Option ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

#          try:
#              option = Option.objects.get(id=option_id, question=question)
#          except Option.DoesNotExist:
#              return Response({'error': 'Invalid option'}, status=status.HTTP_400_BAD_REQUEST)

#          # Save student answer
#          student_answer = StudentAnswer.objects.create(
#              student=student,
#              question=question,
#              selected_option=option
#          )

#          # Update the Student Score
#          student_score, created = StudentScore.objects.get_or_create(
#              student=student,
#              section=question.section
#          )
#          student_score.calculate_progress()
#          passed = student_score.score >= 70.0

#          return Response({
#              'student_answer': StudentAnswerSerializer(student_answer).data,
#              'passed': passed,
#              'score': student_score.score
#          })

#     @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated], url_path='retake')
#     def retake_exam(self, request, course_pk=None, section_pk=None, pk=None):
#          logger.debug("Retake exam triggered for question ID: %s", pk)
#          question = self.get_object()
#          student = request.user
#          section = question.section

#          try:
#              student_score = StudentScore.objects.get(student=student, section=section)
#              student_score.reset_score()
#              logger.debug("Score reset for student ID: %s, section ID: %s", student.id, section.id)
#          except StudentScore.DoesNotExist:
#              logger.warning("StudentScore not found for student ID: %s, section ID: %s", student.id, section.id)
#              return Response({'error': 'No score exists to reset for this section'}, status=status.HTTP_404_NOT_FOUND)

#          # Redirect to the list of questions for the section
#          questions_url = reverse('questions-list', kwargs={'course_pk': course_pk, 'section_pk': section_pk})
#          return HttpResponseRedirect(questions_url)


from django.urls import reverse
from django.http import HttpResponseRedirect
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import PermissionDenied
from .models import Question, Option, StudentAnswer, StudentScore, Section, OrderItem
from .serializers import QuestionSerializer, StudentAnswerSerializer
import logging

logger = logging.getLogger(__name__)

class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [IsAuthenticated, IsStudentAndPurchasedCourse | IsInstructorOwner]
        elif self.action in ['create', 'update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsInstructorOwner]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def get_queryset(self):
         section_id = self.kwargs.get('section_pk')
         if not section_id:
             raise PermissionDenied("Section ID is missing in the request.")

         user = self.request.user

         # Instructor access
         if Section.objects.filter(id=section_id, course__instructor=user).exists():
             return Question.objects.filter(section_id=section_id)

         # Student access
         if OrderItem.objects.filter(
             course_id=Section.objects.get(id=section_id).course_id,
             order__customer=user.customer_profile,
             order__payment_status='C'
            ).exists():
             return Question.objects.filter(section_id=section_id)

         # No access
         raise PermissionDenied("You do not have permission to access this section's questions.")

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated], url_path='answer')
    def question_answer(self, request, course_pk=None, section_pk=None, pk=None):
         question = self.get_object()
         option_id = request.data.get('option_id')
         student = request.user

         if not option_id:
             return Response({'error': 'Option ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

         try:
             option = Option.objects.get(id=option_id, question=question)
         except Option.DoesNotExist:
             return Response({'error': 'Invalid option'}, status=status.HTTP_400_BAD_REQUEST)

         # Save student answer
         student_answer = StudentAnswer.objects.create(
             student=student,
             question=question,
             selected_option=option
         )

         # Update the Student Score
         student_score, created = StudentScore.objects.get_or_create(
             student=student,
             section=question.section
         )
         student_score.calculate_progress()
         passed = student_score.score >= 70.0

         return Response({
             'student_answer': StudentAnswerSerializer(student_answer).data,
             'passed': passed,
             'score': student_score.score
         })

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='retake')
    def retake_exam(self, request, course_pk=None, section_pk=None):
         logger.debug("Retake exam triggered for section ID: %s", section_pk)
         section = get_object_or_404(Section, pk=section_pk)
         student = request.user

         try:
             student_scores = StudentScore.objects.filter(student=student, section=section)
             for student_score in student_scores:
                 student_score.reset_score()
             logger.debug("Scores reset for student ID: %s, section ID: %s", student.id, section.id)
         except StudentScore.DoesNotExist:
             logger.warning("StudentScores not found for student ID: %s, section ID: %s", student.id, section.id)
             return Response({'error': 'No scores exist to reset for this section'}, status=status.HTTP_404_NOT_FOUND)

         # Redirect to the list of questions for the section
         questions_url = reverse('questions-list', kwargs={'course_pk': course_pk, 'section_pk': section_pk})
         return HttpResponseRedirect(questions_url)


    
class PromotionViewSet(viewsets.ModelViewSet):
    serializer_class = PromotionSerializer
    permission_classes = [IsInstructorOrReadOnly]

    def get_queryset(self):
        course_id = self.kwargs['course_pk']
        user = self.request.user

        if not Course.objects.filter(id=course_id, instructor=user).exists():
            raise PermissionDenied("You do not have permission to access this course's promotions.")
        return Promotion.objects.filter(course_id=course_id)

    def perform_create(self, serializer):
        course_id = self.kwargs['course_pk']
        course = Course.objects.get(id=course_id)
        if course.instructor != self.request.user:
            raise PermissionDenied("You do not have permissions to create a promotion for this course.")
        serializer.save(instructor=self.request.user, course=course)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    def get_serializer_context(self):
        return {'course_id': self.kwargs['course_pk']}

    def get_queryset(self):
        return Review.objects.filter(course_id=self.kwargs['course_pk'])


class CourseProgressViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CourseProgressSerializer
    permission_classes = [IsStudentOrInstructor]

    def get_queryset(self):
        queryset = CourseProgress.objects.prefetch_related('student').select_related('course')
        if self.request.user.is_staff:
            logger.info(f"Admin user accessing CourseProgress")
            return queryset.all()

        # Get the customer instance linked to the current user
        customer = Customer.objects.get(user=self.request.user)

        # Check if the user has completed the payment for the course
        purchased_courses = OrderItem.objects.filter(
            order__customer=customer,
            order__payment_status='C'
        ).values_list('course_id', flat=True)

        logger.info(f"Purchased courses: {purchased_courses}")
        
        #filtered_queryset = queryset.filter(student=self.request.user, course_id__in=purchased_courses)
        filtered_queryset = queryset.filter(course_id__in=purchased_courses).filter(student_id=self.request.user.id)

        logger.info(f"Filtered CourseProgress: {filtered_queryset}")
        return filtered_queryset


class InstructorEarningsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InstructorEarningsSerializer
    permission_classes = [IsInstructor]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsInstructor()]
        return [IsAdminUser()]

    def get_queryset(self):
        queryset = InstructorEarnings.objects.select_related('instructor')
        if self.request.user.is_staff:
            return queryset.all()
        return queryset.filter(instructor=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.calculate_earnings()  # Update total_earnings
        total_students = instance.total_students_enrolled()  # Get total students enrolled

        # Serialize and include total_students_enrolled in response
        serializer = self.get_serializer(instance)
        data = serializer.data
        data['total_students_enrolled'] = total_students
        return Response(data)

    def perform_create(self, serializer):
        instance = serializer.save(instructor=self.request.user)
        instance.calculate_earnings()  # Automatically update earnings on creation


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsStudentOrAdmin]

    def get_queryset(self):
        customer = self.request.user.customer_profile
        return Order.objects.filter(customer=customer)

    def get_cart(self, request):
        try:
            return request.user.customer_profile.cart
        except Customer.DoesNotExist:
            logger.error('Customer profile not found')
            return Response({'detail': 'Customer profile not found'}, status=status.HTTP_400_BAD_REQUEST)
        except Cart.DoesNotExist:
            return Response({'detail': 'Your cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='checkout')
    @transaction.atomic
    def checkout(self, request):
        customer = request.user.customer_profile
        cart = self.get_cart(request)

        if isinstance(cart, Response):
            return cart  # Return the error response from get_cart

        if not cart.items.exists():
            logger.error('Cart is empty')
            return Response({'detail': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        
        purchased_courses = OrderItem.objects.filter(order__customer=customer).values_list('course_id', flat=True)
        cart_courses = cart.items.values_list('course_id', flat=True)
        duplicate_courses = set(cart_courses).intersection(set(purchased_courses))
        
        if duplicate_courses:
            logger.info(f"Customer {customer.id} has already purchased course: {duplicate_courses}")
            return Response({'detail': f"You have already purchased course: {list(duplicate_courses)}"}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"Creating order for customer: {customer.id}")
        order = Order.objects.create(customer=customer, payment_status='C')
        logger.info(f"Order created: {order.id}")

        for item in cart.items.all():
            order_item = OrderItem.objects.create(
                order=order,
                course=item.course,
                price=item.course.price,
                customer=customer,
                instructor=item.course.instructor
            )
            logger.info(f"OrderItem created: {order_item.id} for course: {item.course.id}")

            progress, created = CourseProgress.objects.get_or_create(student=request.user, course=item.course)
            if created:
                logger.info(f"CourseProgress created: {progress}")
            else:
                logger.info(f"CourseProgress already exists for student: {request.user}, course: {item.course}")
            
            item.course.update_student_count()
            logger.info(f"Updated number of students for course: {item.course.id}")

        cart.items.all().delete()
        cart.delete()

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = OrderItemSerializer
    queryset = OrderItem.objects.all()
    permission_classes = [IsStudentOrAdmin]


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsStudentOrAdmin]

    def get_queryset(self):
        customer = self.request.user.customer_profile
        logger.debug(f"Fetching cart for customer: {customer.id}")
        return Cart.objects.filter(customer=customer)

    def get_cart(self, request):
        """Get or Create cart associated with the current user"""
        customer = request.user.customer_profile
        cart, created = Cart.objects.get_or_create(customer=customer)
        logger.debug(f"{'Created' if created else 'Fetched'} cart for customer: {customer.id}")
        return cart

    @action(detail=False, methods=['post'], url_path='add-item')
    def add_item(self, request):
        logger.debug(f"Received add-item request with method: {request.method}")
        cart = self.get_cart(request)
        course_id = request.data.get('course_id')
        if not course_id:
            logger.error("course_id is required")
            return Response({'detail': 'course_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            course = Course.objects.get(id=course_id)
            logger.debug(f"Course found: {course.id}")
        except Course.DoesNotExist:
            logger.error(f"Invalid course_id: {course_id}")
            return Response({'detail': 'Invalid course_id'}, status=status.HTTP_404_NOT_FOUND)
        if CartItem.objects.filter(cart=cart, course=course).exists():
            logger.warning(f"Item already in the cart: {course.id}")
            return Response({'detail': 'Item already in the cart'}, status=status.HTTP_400_BAD_REQUEST)
        CartItem.objects.create(cart=cart, course=course)
        logger.info(f"Added course {course.id} to cart for customer {cart.customer.id}")
        return Response(CartSerializer(cart, context={'request': request}).data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        customer = self.request.user.customer_profile
        existing_cart = Cart.objects.filter(customer=customer).first()
        if existing_cart:
            logger.error("Cart already exists for this customer.")
            raise serializers.ValidationError({"detail": "Cart already exists for this customer."})
        serializer.save(customer=customer)


class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):

        if self.action == 'remove':
            self.permission_classes = [IsStudentOrAdmin]

        elif self.request.method == 'POST':
            self.permission_classes = [IsAdminUser]  # Changed to ensure POST is only for admin
        else:
            self.permission_classes = [IsStudentOrAdmin]
        return super(CartItemViewSet, self).get_permissions()

    def get_cart(self, request):
        """Get the cart associated with the current user"""
        customer = request.user.customer_profile
        cart, created = Cart.objects.get_or_create(customer=customer)
        logger.debug(f"{'Created' if created else 'Fetched'} cart for customer: {customer.id}")
        return cart
    
    def get_queryset(self):
        cart = self.get_cart(self.request)
        logger.debug(f"Fetching cart items for cart: {cart.id}")
        return CartItem.objects.filter(cart=cart)
    
    def create(self, request, *args, **kwargs):
        cart = self.get_cart(request)
        course_id = request.data.get('course_id')
        
        if not course_id:
            logger.error("course_id is required")
            return Response({'detail': 'course_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            course = Course.objects.get(id=course_id)
            logger.debug(f"Course found: {course.id}")
        except Course.DoesNotExist:
            logger.error(f"Invalid course_id: {course_id}")
            return Response({'detail': 'Invalid course_id'}, status=status.HTTP_404_NOT_FOUND)
        
        cart_item, created = CartItem.objects.get_or_create(cart=cart, course=course)
        if not created:
            logger.warning(f"Item already in the cart: {course.id}")
            return Response({'detail': 'Item Already in cart'}, status=status.HTTP_200_OK)
        
        logger.info(f"Added course {course.id} to cart item: {cart_item.id}")
        return Response(CartItemSerializer(cart_item).data, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, pk=None):
        cart_item = self.get_object()
        logger.info(f"Removing item {cart_item.id} from cart")
        cart_item.delete()
        return Response({'detail': 'Item removed from the cart'}, status=status.HTTP_204_NO_CONTENT)

    def list(self, request, cart_pk=None):
        cart = self.get_cart(request)
        cart_items = cart.items.all()
        logger.debug(f"Listing items for cart: {cart.id}")
        serializer = CartItemSerializer(cart_items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get', 'delete'], url_path='remove')
    def remove(self, request, pk=None):
        """Custom endpoint to remove a specific item from the cart"""
        try:
            cart_item = CartItem.objects.get(pk=pk, cart=self.get_cart(request))
            logger.info(f"Removing item {cart_item.id} from cart for custom remove endpoint")
            cart_item.delete()
            return Response({'detail': 'Item removed from the cart'}, status=status.HTTP_204_NO_CONTENT)

        except CartItem.DoesNotExist:
            logger.error(f"Cart item id {pk} not found in cart")
            return Response({'detail': 'Item not found in cart'}, status=status.HTTP_404_NOT_FOUND)


class WishListViewSet(viewsets.ModelViewSet):
    serializer_class = WishListSerializer
    permission_classes = [IsStudentOrAdmin]

    def get_queryset(self):
        return WishList.objects.filter(customer=self.request.user.customer_profile)


class WishListItemViewSet(viewsets.ModelViewSet):
    serializer_class = WishListItemSerializer
    permission_classes = [IsStudentOrAdmin]

    def get_queryset(self):
        wishlist = WishList.objects.get(pk=self.kwargs['wishlist_pk'])
        return WishListItem.objects.filter(wishlist=wishlist)


class RatingViewSet(viewsets.ModelViewSet):
    serializer_class = RatingSerializer
    permission_classes = [IsStudentAndPurchasedCourse]

    def get_queryset(self):
        user = self.request.user
        course_id = self.kwargs['course_pk']
        logger.debug(f"Fetching ratings for course {course_id}")
        return Rating.objects.filter(course_id=course_id, user=user)

    def create(self, request, course_pk=None):
        course = get_object_or_404(Course, pk=course_pk)
        logger.debug(f"Creating rating for course {course_pk}")

        purchased = OrderItem.objects.filter(order__customer=request.user.customer_profile, course=course, order__payment_status='C').exists()
        if not purchased:
            logger.debug(f"User {request.user.id} has not purchased course {course_pk}")
            return Response({'detail': 'You can only rate courses you have purchased.'}, status=status.HTTP_400_BAD_REQUEST)

        if Rating.objects.filter(user=request.user, course=course).exists():
            logger.debug(f"User {request.user.id} has already rated course {course_pk}")
            return Response({'detail': 'You have already rated this course.'}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data['user'] = request.user.id
        data['course'] = course.id

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            rating = serializer.save()
            logger.debug(f"Rating created for course {course_pk} by user {request.user.id}")
            course.update_rating_metrics()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.debug(f"Failed to create rating for course {course_pk}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, course_pk=None, pk=None):
        course = get_object_or_404(Course, pk=course_pk)
        rating = get_object_or_404(self.get_queryset(), pk=pk, user=request.user)

        logger.debug(f"Updating rating {pk} for course {course_pk}")
        serializer = self.get_serializer(rating, data=request.data, partial=True)
        if serializer.is_valid():
            rating = serializer.save()
            logger.debug(f"Rating {pk} updated for course {course_pk}")
            course.update_rating_metrics()
            return Response(serializer.data)
        logger.debug(f"Failed to update rating {pk} for course {course_pk}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, course_pk=None, pk=None):
        course = get_object_or_404(Course, pk=course_pk)
        rating = get_object_or_404(self.get_queryset(), pk=pk, user=request.user)

        logger.debug(f"Deleting rating {pk} for course {course_pk}")
        rating.delete()
        course.update_rating_metrics()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CompanyOverviewViewSet(viewsets.ModelViewSet):
    queryset = CompanyOverview.objects.all()
    serializer_class = CompanyOverviewSerializer
    permission_classes = [IsAdminOrReadOnly]


class MissionViewSet(viewsets.ModelViewSet):
    queryset = Mission.objects.all()
    serializer_class = MissionSerializer
    permission_classes = [IsAdminOrReadOnly]


class VisionViewSet(viewsets.ModelViewSet):
    queryset = Vission.objects.all()
    serializer_class = VissionSerializer
    permission_classes = [IsAdminOrReadOnly]


class CoreValueViewSet(viewsets.ModelViewSet):
    queryset = CoreValue.objects.all()
    serializer_class = CoreValueSerializer
    permission_classes = [IsAdminOrReadOnly]



class StaffMemberViewSet(viewsets.ModelViewSet):
    queryset = StaffMember.objects.all()
    serializer_class = StaffMemberSerializer
    permission_classes = [IsAdminOrReadOnly]

    @action(detail=True, methods=['get'], url_path='fb')
    def get_fb(self, request, pk=None):
        staff_member = self.get_object()
        return Response({'fb': staff_member.fb})

    @action(detail=True, methods=['get'], url_path='linkedin')
    def get_linkedin(self, request, pk=None):
        staff_member = self.get_object()
        return Response({'linkedin': staff_member.linkedin})

    @action(detail=True, methods=['get'], url_path='twitter')
    def get_twitter(self, request, pk=None):
        staff_member = self.get_object()
        return Response({'twitter': staff_member.twitter})

    @action(detail=True, methods=['get'], url_path='tiktok')
    def get_tiktok(self, request, pk=None):
        staff_member = self.get_object()
        return Response({'tiktok': staff_member.tiktok})

    @action(detail=True, methods=['get'], url_path='telegram_channel')
    def get_telegram_channel(self, request, pk=None):
        staff_member = self.get_object()
        return Response({'telegram_channel': staff_member.telegram_channel})


class TestimonialViewSet(viewsets.ModelViewSet):
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer
    permission_classes = [IsAuthenticated]


class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    permission_classes = [IsAdminOrReadOnly]


class DescriptionViewSet(viewsets.ModelViewSet):
    queryset = Description.objects.all()
    serializer_class = DescriptionSerializer
    permission_classes = [IsAdminOrReadOnly]


class PaymentStatusViewSet(viewsets.ModelViewSet):
    queryset = PaymentStatus.objects.all()
    serializer_class = PaymentStatusSerializer
    permission_class = [IsAdminUser]

from rest_framework.views import APIView
logger = logging.getLogger(__name__)

class SetEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        logger.info(f"Request headers: {request.headers}")
        logger.info(f"Request data: {request.data}")
        # Your existing logic

# def register_user(request):
#     if request.method == 'POST':
#         # Create a new user
#         user = User.objects.create_user(
#             email=request.POST['email'],
#             password=request.POST['password']
#         )
        
#         # Generate a token
#         token = generate_token_for_user(user)

#         # Send activation email
#         send_activation_email(user, token)

#         return JsonResponse({'message': 'User registered. Activation email sent.'})


def home(request):
    return HttpResponse("Welcome to the home page!")


# import boto3
# from botocore.exceptions import NoCredentialsError
# from django.http import JsonResponse
# import os

# # Initialize the S3 client using AWS credentials
# s3_client = boto3.client('s3', 
#     aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),  # Get credentials from environment variables or settings
#     aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
#     region_name='eu-north-1'  # Replace with your specific AWS region, e.g., 'eu-north-1'
# )

# # Your S3 bucket name
# BUCKET_NAME = 'mando-ecommerce'

# def generate_presigned_url(request):
#     try:
#         # Get file name and type from the request parameters
#         file_name = request.GET.get('file_name')
#         file_type = request.GET.get('file_type')

#         if not file_name or not file_type:
#             return JsonResponse({'error': 'Missing file_name or file_type parameters'}, status=400)

#         # Generate a presigned URL for uploading the file to S3
#         presigned_url = s3_client.generate_presigned_url('put_object',
#             Params={'Bucket': BUCKET_NAME, 'Key': file_name, 'ContentType': file_type},
#             ExpiresIn=3600)  # The URL will expire in 1 hour

#         return JsonResponse({'url': presigned_url})
    
#     except NoCredentialsError:
#         return JsonResponse({'error': 'AWS credentials not available'}, status=400)
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)
