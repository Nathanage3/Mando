from rest_framework import serializers
from django.conf import settings
from django.db import transaction
from .models import Collection, Promotion,  PaymentStatus, Description, Rating, Question, StudentAnswer, Option, Course, CourseProgress, \
  Review, Customer, InstructorEarnings, Lesson, Order, OrderItem, \
  Cart, CartItem, Certificate, CoreValue, WishList, WishListItem, Section, \
  Mission, CompanyOverview, CoreValue, FAQ, Vission, StaffMember, Testimonial
from courses.signals import order_created
from core.models import User


class PromotionSerializer(serializers.ModelSerializer):
    instructor = serializers.CharField(read_only=True)

    class Meta:
        model = Promotion
        fields = ['id', 'instructor', 'title', 'message', 'discount', 'start_date', 'end_date']
    
    def create(self, validated_data):
        validated_data['instructor'] = self.context['request'].user
        return super(PromotionSerializer, self).create(validated_data)


class CollectionSerializer(serializers.ModelSerializer):
    courses_count = serializers.IntegerField()
    class Meta:
        model = Collection
        fields = ['id', 'title', 'courses_count']


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['id', 'score']
        read_only_fields = ['course', 'user']

    def create(self, validated_data):
        request = self.context.get('request')
        view = self.context.get('view')

        if request and view and 'course_pk' in view.kwargs:
            course_id = view.kwargs['course_pk']
            try:
                course = Course.objects.get(pk=course_id)
                validated_data['user'] = request.user
                validated_data['course'] = course
            except Course.DoesNotExist:
                raise serializers.ValidationError("Course not found.")
        else:
            raise serializers.ValidationError("Course ID or user not found.")
        
        return super().create(validated_data)


class CourseSerializer(serializers.ModelSerializer):
    instructor = serializers.SerializerMethodField()
    numberOfStudents = serializers.SerializerMethodField()
    duration_in_hours = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'collection', 'title', 'courseFor', 'objectives', 'description', 'rating_count', 'average_rating',
                  'oldPrice', 'duration_in_hours', 'price', 'currency', 'instructor', 'level', 'syllabus', 'prerequisites',
                  'image', 'preview', 'numberOfStudents', 'promotions', 'last_update'
                  ]

    def get_instructor(self, course: Course):
        instructor = course.instructor
        return {'first_name': instructor.first_name, 'last_name': instructor.last_name}

    def get_numberOfStudents(self, obj):
        return OrderItem.objects.filter(course=obj).values('order__customer').distinct().count()

    def get_duration_in_hours(self, obj):
        return obj.duration_in_hours()

    def create(self, validated_data):
        promotions_data = validated_data.pop('promotions', [])
        course = Course.objects.create(**validated_data)
        for promotion_data in promotions_data:
            Promotion.objects.create(course=course, instructor=course.instructor, **promotion_data)
        return course

    def update(self, instance, validated_data):
        promotions_data = validated_data.pop('promotions', [])
        instance = super().update(instance, validated_data)
        for promotion_data in promotions_data:
            Promotion.objects.create(course=instance, instructor=instance.instructor, **promotion_data)
        return instance

    def get_average_rating(self, obj):
        return obj.get_average_rating()

    def get_rating_count(self, obj):
        return obj.get_rating_count()


class SimpleCourseSerializer(serializers.ModelSerializer):
    instructor = serializers.SerializerMethodField()
    class Meta:
        model = Course
        fields = ['id', 'title', 'instructor', 'price', 'description', 'objectives', 'total_duration']

    def get_instructor(self, course: Course):
        instructor = course.instructor
        return {'first_name': instructor.first_name,
                 'last_name': instructor.last_name
                 }

class LessonSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True)
    duration = serializers.IntegerField(read_only=True)

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'order', 'file', 'is_active', 'opened', 'duration']
        read_only_fields = ['order']
    
    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.file = validated_data.get('file', instance.file)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.save()
        return instance


class SectionSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    course = serializers.CharField(read_only=True)
    number_of_lessons = serializers.CharField(read_only=True)
    total_duration = serializers.DurationField(read_only=True) # Total duration field for section
    
    class Meta:
        model = Section
        fields = ['id', 'course', 'title', 'number_of_lessons', 'total_duration', 'lessons']


class OptionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    class Meta:
        model = Option
        fields = ['id', 'text', 'is_correct']

class QuestionSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ['id', 'text', 'options', 'section']

    def get_options(self, obj):
        # Check if the context has a flag to include `is_correct`
        show_correctness = self.context.get('show_correctness', False)
        if show_correctness:
            # Use the full OptionSerializer with `is_correct`
            return OptionSerializer(obj.options.all(), many=True).data
        else:
            # Exclude `is_correct` by using a simplified serializer
            return OptionSerializerWithoutCorrectness(obj.options.all(), many=True).data

    def create(self, validated_data):
        options_data = validated_data.pop('options', [])
        question = Question.objects.create(**validated_data)
        for option_data in options_data:
            Option.objects.create(question=question, **option_data)
        return question

    def update(self, instance, validated_data):
        options_data = validated_data.pop('options', [])
        instance.text = validated_data.get('text', instance.text)
        instance.section = validated_data.get('section', instance.section)
        instance.save()

        # Create a dictionary of existing options with their IDs
        existing_options = {option.id: option for option in instance.options.all()}

        # Update existing options and create new ones if necessary
        for option_data in options_data:
            option_id = option_data.get('id')
            if option_id in existing_options:
                option = existing_options[option_id]
                option.text = option_data.get('text', option.text)
                option.is_correct = option_data.get('is_correct', option.is_correct)
                option.save()
                del existing_options[option_id]  # Remove updated options from the dict
            else:
                Option.objects.create(question=instance, **option_data)

        # Delete any options that were not included in the update
        for option_id, option in existing_options.items():
            option.delete()

        return instance



class OptionSerializerWithoutCorrectness(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'text']


class StudentAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAnswer
        fields = '__all__'

class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = '__all__'


class CourseDetailSerializer(serializers.ModelSerializer):
    sections = SectionSerializer(many=True, read_only=True)
    instructor = serializers.SerializerMethodField()
    rating = RatingSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'instructor', 'description', 'rating', 'price', 'currency', 'sections']

    def get_instructor(self, course: Course):
        instructor = course.instructor
        return {
            'first_name': instructor.first_name,
            'last_name': instructor.last_name
        }


class CourseProgressSerializer(serializers.ModelSerializer):
    completed_lessons = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = CourseProgress
        fields = ['student', 'course', 'completed_lessons', 'completed', 'progress', 'last_accessed']
        read_only_fields = ['student', 'course', 'completed_lessons']


class ReviewSerializer(serializers.ModelSerializer):
    course = serializers.StringRelatedField()

    class Meta:
        model = Review
        fields = ['id', 'name', 'course', 'rating', 'comment', 'created_at']

    def create(self, validated_data):
        course_id = self.context['course_id']
        return Review.objects.create(course_id=course_id, **validated_data)


class CustomerSerializer(serializers.ModelSerializer):
    pass


class InstructorEarningsSerializer(serializers.ModelSerializer):
    earnings_after_deduction = serializers.SerializerMethodField()
    class Meta:
        model = InstructorEarnings
        fields = ['id', 'earnings_after_deduction', 'last_payout']

    def validate_instructor_id(self, value):
        if not User.objects.filter(id=value, role='instructor').exists():
            raise serializers.ValidationError("Instructor does not exist.")
        return value

    def get_earnings_after_deduction(self, obj):
        return obj.calculate_earnings()


class OrderItemSerializer(serializers.ModelSerializer):
    course = SimpleCourseSerializer()
    customer = serializers.CharField(read_only=True)
    instructor = serializers.CharField(read_only=True)
    price = serializers.IntegerField(read_only=True)
    class Meta:
        model = OrderItem
        fields = ['id', 'course', 'customer', 'instructor', 'price', 'purchase_at']


class OrderSerializer(serializers.ModelSerializer):
    items  = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    # I removed the payment_status intentinally 
    class Meta:
        model = Order
        fields = ['id', 'placed_at', 'items', 'total_price']

    def get_total_price(self, cart: Cart):
        return sum([item.course.price for item in cart.items.all()])


class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()

    def validate_cart_id(self, id):
        if not Cart.objects.filter(pk=id).exists():
            raise serializers.ValidationError('Invalid cart id')
        elif not CartItem.objects.filter(cart_id=id).exists():
            raise serializers.ValidationError('Empty cart')
        return id

    def save(self, **kwargs):
        with transaction.atomic():
            cart_id = self.validated_data['cart_id']
            customer, created = Customer.objects.get_or_create(user_id=self.context['user_id'])
            order = Order.objects.create(customer=customer)
            cart_items = CartItem.objects.select_related('course').filter(cart_id=cart_id)
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    course=item.course,
                    price=item.course.price,
                )
            Cart.objects.filter(pk=cart_id).delete()
            order_created.send_robust(sender=self.__class__, order=order)
            return order


class UpdateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['payment_status']


class CartItemSerializer(serializers.ModelSerializer):
    course = SimpleCourseSerializer()
   
    class Meta:
        model = CartItem
        fields = ['id', 'course']


class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    customer_id = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'created_at', 'customer_id', 'items']

    def get_customer_id(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, "user"):
            customer = Customer.objects.get(user=request.user)
            return customer.id
        return None
    
class WishListItemSerializer(serializers.ModelSerializer):
    course = SimpleCourseSerializer()
    
    class Meta:
        model = WishListItem
        fields = ['id', 'course']


class WishListSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    items = WishListItemSerializer(many=True, read_only=True)
    class Meta:
        model = WishList
        fields = ['id', 'created_at', 'items']


class CompanyOverviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyOverview
        fields = '__all__'


class MissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mission
        fields = '__all__'

class VissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vission
        fields = '__all__'


class CoreValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoreValue
        fields = '__all__'

class StaffMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffMember
        exclude = ['is_admin']  # Exclude sensitive admin details
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.is_admin:
            # Remove sensitive fields for admin staff members
            representation.pop('phone')
            representation.pop('email')
        return representation


class SocialMediaLinksSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffMember
        fields = ['fb', 'linkedin', 'twitter', 'tiktok', 'telegram_channel']

class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = '__all__'


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'

class DescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Description
        fields = '__all__'

class PaymentStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentStatus
        fields = '__all__'