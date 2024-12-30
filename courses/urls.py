from django.urls import path, include
from rest_framework_nested import routers
from courses import views


# Main router for Course-related viewsets
router = routers.DefaultRouter()
router.register(r'courses', views.CourseViewSet, basename='courses')
router.register('collections', views.CollectionViewSet, basename='collections')
router.register('customers', views.CustomerViewSet, basename='customers')
router.register('course-progress', views.CourseProgressViewSet, basename='course-progress')
router.register('instructor-earnings', views.InstructorEarningsViewSet, basename='instructor-earnings')
router.register('orders', views.OrderViewSet, basename='orders')
router.register('order-items', views.OrderItemViewSet, basename='order-items')
router.register('carts', views.CartViewSet, basename='carts')
router.register('cart-items', views.CartItemViewSet, basename='cart-items')
router.register('company_overview', views.CompanyOverviewViewSet)
router.register('mission', views.MissionViewSet)
router.register('vission', views.VisionViewSet)
router.register('core_values', views.CoreValueViewSet)
router.register('staff_members', views.StaffMemberViewSet)
router.register('testimonials', views.TestimonialViewSet)
router.register('faqs', views.FAQViewSet)
router.register('purchased_course', views.FullCourseViewSet, basename='purchased-courses')
router.register('payment_description', views.DescriptionViewSet)
router.register('payment_snapshot', views.PaymentStatusViewSet)

# Nested routers for Course-related models
course_router = routers.NestedDefaultRouter(router, r'courses', lookup='course')
course_router.register('reviews', views.ReviewViewSet, basename='course-reviews')
course_router.register('progress', views.CourseProgressViewSet, basename='course-progress')
course_router.register('promotions', views.PromotionViewSet, basename='promotions')
course_router.register('sections', views.SectionViewSet, basename='sections')
course_router.register(r'questions', views.QuestionViewSet, basename='course-questions')

# Nested router for lessons under sections
section_router = routers.NestedDefaultRouter(course_router, r'sections', lookup='section')
section_router.register(r'lessons', views.LessonViewSet, basename='lessons')
section_router.register(r'questions', views.QuestionViewSet, basename='questions')


# Separate nested routers for purchased courses for students
purchased_course_router = routers.NestedDefaultRouter(router, 'purchased_course', lookup='course')
purchased_course_router.register(r'sections', views.SectionViewSet, basename='purchased-sections')
purchased_course_router.register(r'ratings', views.RatingViewSet, basename="ratings")

# Nested router for lessons under purchased sections
purchased_section_router = routers.NestedDefaultRouter(purchased_course_router, 'sections', lookup='section')
purchased_section_router.register('lessons', views.LessonViewSet, basename='purchased-lessons')
purchased_course_router.register('questions', views.QuestionViewSet, basename='questions')


urlpatterns = [
    path('', include(router.urls)),
    path('', views.home, name='home'),
    path('', include(course_router.urls)),
    path('', include(section_router.urls)),
    path('', include(purchased_course_router.urls)),
    path('', include(purchased_section_router.urls)),
    # path('get-upload-url/', views.get_upload_url, name='get_upload_url'),
    # path('get-image-url/<str:file_name>/', views.get_image_url, name='get_image_url'),
    path('instructors/<int:instructor_pk>/earnings/', views.InstructorEarningsViewSet.as_view({'get': 'list'})),
    path('courses/<int:course_pk>/sections/<int:section_pk>/questions/<int:pk>/answer/', views.QuestionViewSet.as_view({'post': 'question_answer'}), name='question-answer'),
]
