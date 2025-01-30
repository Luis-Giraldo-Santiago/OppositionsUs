from django.core.exceptions import ValidationError
from django.test import TestCase
from .models import Customer, CourseType, Course,CourseReservation, Order, Status

class CustomerModelTest(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            name="John Doe",
            email="john.doe@example.com",
            adress="123 Main Street",
            phone=123456789,
            admin=False
        )

    def test_customer_str(self):
        self.assertEqual(str(self.customer), "John Doe") 

    def test_customer_phone_validation(self):
        self.customer.phone = 12345
        with self.assertRaises(ValidationError):
            self.customer.full_clean() 

class CourseModelTest(TestCase):
    def setUp(self):
        self.course_type = CourseType.objects.create(name="Programming")
        self.course = Course.objects.create(
            name="Python for Beginners",
            image="courses/python.jpg",
            price=100.00,
            details="Learn Python from scratch",
            city="Madrid",
            course_type=self.course_type,
            capacity=30,
            is_available=True,
            start_date="2024-01-01",
            end_date="2024-02-01"
        )

    def test_course_str(self):
        self.assertEqual(str(self.course), "Python for Beginners")  

    def test_price_validation(self):
        self.course.price = -10  
        with self.assertRaises(ValidationError):
            self.course.full_clean()  

    def test_capacity_validation(self):
        self.course.capacity = -5 
        with self.assertRaises(ValidationError):
            self.course.full_clean()

class CourseReservationModelTest(TestCase):
    def setUp(self):
        self.course_type = CourseType.objects.create(name="Programming")
        self.course = Course.objects.create(
            name="Python for Beginners",
            image="courses/python.jpg",
            price=100.00,
            details="Learn Python from scratch",
            city="Madrid",
            course_type=self.course_type,
            capacity=30,
            is_available=True,
            start_date="2024-01-01",
            end_date="2024-02-01"
        )
        self.customer = Customer.objects.create(
            name="Jane Doe",
            email="jane.doe@example.com",
            adress="456 Another Street",
            phone=987654321,
            admin=False
        )
        self.status = Status.objects.create(name="Pending")
        self.order = Order.objects.create(
            customer=self.customer,
            date_ordered="2024-01-14T12:00:00Z",
            status=self.status,
            tracking_id="TRACK123456",
            shipping_address=None  
        )
        
        self.reservation = CourseReservation.objects.create(
            order=self.order,
            customer=self.customer,
            reserved_on="2024-01-15T10:00:00Z",
            is_confirmed=False,
        )

    def test_reservation_str(self):

        self.assertEqual(
        str(self.reservation),
        f"Reservation {self.reservation.id} for {self.order.id} by {self.customer.id}"
    )
