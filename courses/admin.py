from django.contrib import admin, messages
from django.db.models.aggregates import Count
from django.utils.html import format_html, urlencode
from django.urls import reverse
from django.utils.html import format_html
from . import models


class CourseImageInLine(admin.TabularInline):
    model = models.Course
    readonly_fields = ['thumbnail']

    def thumbnail(self, instance):
        if instance.image.name != '':
            return format_html(f'<img src="{instance.image.url}" class="thumbnail">')
        return ''


# Register Collection model
@admin.register(models.Collection)
class CollectionAdmin(admin.ModelAdmin):
    search_fields = ['title']  # Assuming the Collection model has a 'name' field
    list_display = ['title']  # Customize fields as per your model


############## CourseAdmin Begin ##############

# Inline for Lessons
class LessonInline(admin.StackedInline):
    model = models.Lesson
    extra = 1

# Customize Section Admin
@admin.register(models.Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'number_of_lessons', 'total_duration', 'locked', 'default')
    list_filter = ('course', 'locked', 'default')
    search_fields = ('title', 'course__title')
    inlines = [LessonInline]  # Inline for Lessons

    def course_title(self, obj):
        return obj.course.title
    course_title.admin_order_field = 'course'  # Allows column order sorting
    course_title.short_description = 'Course Title'

from django.contrib import admin

from . import models  # Adjust the import based on your project structure

@admin.register(models.Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'instructor', 'price', 'currency', 'average_rating_display', 
        'numberOfStudents', 'level', 'is_active', 'last_update'
    )
    list_filter = ('instructor', 'is_active', 'level')
    search_fields = ('title', 'instructor__user__email', 'description')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('-last_update', 'title')
    readonly_fields = ('average_rating', 'numberOfStudents', 'last_update')
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description', 'total_duration', 'price', 
                       'oldPrice', 'currency', 'is_active', 'level', 'collection', 
                       'promotions')
        }),
        ('Instructor Information', {
            'fields': ('instructor',)
        }),
        ('Media', {
            'fields': ('image', 'preview')
        }),
        ('Additional Info', {
            'fields': ('objectives', 'courseFor', 'syllabus', 'prerequisites')
        }),
        ('Ratings', {
            'fields': ('average_rating', 'rating_count', 'numberOfStudents')
        }),
    )
    date_hierarchy = 'last_update'
    autocomplete_fields = ['instructor', 'collection']

    def average_rating_display(self, obj):
        """Custom display for average rating."""
        return format_html(
            '<span style="color: green; font-weight: bold;">{}</span>',
            round(obj.average_rating, 2)
        )
    average_rating_display.short_description = "Average Rating"

    def get_queryset(self, request):
        """Customize queryset based on user permissions."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(instructor=request.user)

    def save_model(self, request, obj, form, change):
        """Set instructor for new courses automatically."""
        if not obj.pk:
            obj.instructor = request.user
        super().save_model(request, obj, form, change)

    class SectionInline(admin.StackedInline):
        """Inline admin for sections."""
        model = models.Section
        extra = 1

    inlines = [SectionInline]

############### CustomerAdmin Begin ############

@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'orders_count')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    ordering = ('user__first_name', 'user__last_name')

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            orders_count=Count('order')
        )
    
    def orders_count(self, obj):
        # Return the orders count for the customer
        return obj.orders_count
    orders_count.admin_order_field = 'orders_count'  # Enable ordering by this field
    orders_count.short_description = 'Orders Count'

############### CustomerAdmin End ##############


############## InstructorEarningAdmin Begin ###########

@admin.register(models.InstructorEarnings)
class InstructorEarningsAdmin(admin.ModelAdmin):
    list_display = ('instructor', 'total_earnings', 'last_payout', 'deduction_percentage')
    search_fields = ('instructor__username',) # Allows searching by instructor's username
    ordering = ('instructor',)
    readonly_fields = ('total_earnings',) # Make total_earnings read-only
    list_filter = ('deduction_percentage',) # Filter earnings by deduction percentage
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('instructor')
    
    def save_model(self, request, obj, form, change):
        # Update the total earnings whenever the model is saved
        obj.total_earnings = obj.calculate_earnings()
        super().save_model(request, obj, form, change)

############## InstructorEarningAddmin End ###########


@admin.register(models.Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'order', 'is_active')
    list_filter = ('section', 'is_active')
    search_fields = ('title', 'section__title')
    ordering = ('order',)

    def section_title(self, obj):
        return obj.section.title
    section_title.admin_order_field = 'section'  # Allows column order sorting
    section_title.short_description = 'Section Title'


class OrderItemInline(admin.TabularInline):
    autocomplete_fields = ['course']
    min_num = 1
    max_num = 10
    model = models.OrderItem
    extra = 0


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    autocomplete_fields = ['customer']
    inlines = [OrderItemInline]
    list_display = ['id', 'placed_at', 'payment_status', 'customer']
    list_editable = ['payment_status']
    list_filter = ['payment_status', 'placed_at', 'customer']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('customer')
    def customer_email(self, obj):
        return obj.customer.user.email
    customer_email.short_description = 'Customer Email'
    
    ordering = ['-placed_at']


@admin.register(models.Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'issue_date', 'certificate_file')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 'course__title')
    list_filter = ('issue_date', 'course')
    def generate_certificate(self, obj):
        return f"Generated on {obj.issue_date}"
    
    generate_certificate.short_description = 'Certificate Status'

@admin.register(models.CompanyOverview)
class CompanyOverviewAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)


@admin.register(models.Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)


@admin.register(models.Vission)
class VissionAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)


@admin.register(models.CoreValue)
class CoreValueAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)


@admin.register(models.StaffMember)
class StaffMember(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone')
    search_fields = ('first_name', 'email', 'phone')
   


@admin.register(models.Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'title')
    search_fields = ('full_name', 'title')


@admin.register(models.FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer')
    search_fields = ('question', 'answer')