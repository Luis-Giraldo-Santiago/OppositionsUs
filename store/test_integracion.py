from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model  
from store.models import Course, CourseType, Customer
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image
from decimal import Decimal

def create_test_image():
    image = Image.new('RGB', (100, 100), color=(255, 0, 0))  
    image_file = BytesIO()
    image.save(image_file, format='JPEG')  
    image_file.name = 'test_image.jpg'  
    image_file.seek(0)  
    return SimpleUploadedFile('test_image.jpg', image_file.read(), content_type='image/jpeg')


class CourseIntegrationTests(TestCase):
    def setUp(self):
        self.course_type = CourseType.objects.create(name='Test Course Type')

        self.image = create_test_image()

        self.user_admin = get_user_model().objects.create_user(
            email='admin@test.com',  
            password='adminpassword',
        )
        self.customer_admin = Customer.objects.create(user=self.user_admin, name='Admin User', email='admin@test.com', adress='123 Admin St', phone='123456789', admin=True)
    
    def test_create_course_as_admin(self):
        form_data = {
            'name': 'Test Course',
            'price': Decimal('100.00'),  
            'city': 'Test City',
            'course_type': self.course_type.id,
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'image': self.image,
            'capacity': Decimal('20.00'),  
        }

        self.client.login(email='admin@test.com', password='adminpassword')

        response = self.client.post(reverse('createCourse'), form_data)

        self.assertEqual(response.status_code, 302)  
        self.assertTrue(Course.objects.filter(name='Test Course').exists())
        course = Course.objects.get(name='Test Course')
        self.assertEqual(course.capacity, Decimal('20.00'))  

        def test_create_course_as_non_admin(self):
            user_non_admin = get_user_model().objects.create_user(
                email='nonadmin@test.com',
                password='nonadminpassword',
            )
            customer_non_admin = Customer.objects.create(user=user_non_admin, name='Non Admin', email='nonadmin@test.com', adress='123 Non Admin St', phone='987654321', admin=False)

            form_data = {
                'name': 'Test Course',
                'price': 100.00,
                'city': 'Test City',
                'course_type': self.course_type.id, 
                'start_date': '2024-01-01',
                'end_date': '2024-12-31',
                'image': self.image,
                'capacity': 20,  
            }
            self.client.login(email='nonadmin@test.com', password='nonadminpassword')

            response = self.client.post(reverse('createCourse'), form_data)

            self.assertEqual(response.status_code, 302)
            self.assertFalse(Course.objects.filter(name='Test Course').exists())

class EditCourseIntegrationTests(TestCase):
    def setUp(self):
        self.course_type = CourseType.objects.create(name='Test Course Type')

        self.image = create_test_image()

        self.user_admin = get_user_model().objects.create_user(
            email='admin@test.com', 
            password='adminpassword',
        )
        self.customer_admin = Customer.objects.create(user=self.user_admin, name='Admin User', email='admin@test.com', adress='123 Admin St', phone='123456789', admin=True)

        self.course = Course.objects.create(
            name='Original Course',
            price=100.00,
            city='Original City',
            course_type=self.course_type,
            start_date='2024-01-01',
            end_date='2024-12-31',
            image=self.image,
            capacity=20,  
        )

    def test_edit_course_as_admin(self):
        course = Course.objects.create(
            name='Initial Course',
            price=Decimal('100.00'),
            city='Test City',
            course_type=self.course_type,
            start_date='2024-01-01',
            end_date='2024-12-31',
            image=self.image,
            capacity=Decimal('20.00'),
        )

        form_data = {
            'name': 'Updated Course Name',
            'price': Decimal('150.00'),
            'city': 'Updated City',
            'course_type': self.course_type.id,
            'start_date': '2024-02-01',
            'end_date': '2024-11-30',
            'capacity': Decimal('50.00'),  
        }

        self.client.login(email='admin@test.com', password='adminpassword')

        files = {
            'image': self.image,   
        }


        response = self.client.post(reverse('edit_course', args=[course.id]), form_data, FILES=files)

        self.assertEqual(response.status_code, 302) 


        course.refresh_from_db()
        self.assertEqual(course.name, 'Updated Course Name')
        self.assertEqual(course.city, 'Updated City')
        self.assertEqual(course.price, Decimal('150.00'))  
        self.assertEqual(course.capacity, Decimal('50.00'))  

    def test_edit_course_as_non_admin(self):
        user_non_admin = get_user_model().objects.create_user(
            email='nonadmin@test.com', 
            password='nonadminpassword',
        )
        customer_non_admin = Customer.objects.create(user=user_non_admin, name='Non Admin', email='nonadmin@test.com', adress='123 Non Admin St', phone='987654321', admin=False)

        form_data = {
            'name': 'Updated Course Name',
            'price': 150.00,
            'city': 'Updated City',
            'course_type': self.course_type.id,  
            'start_date': '2024-02-01',
            'end_date': '2024-11-30',
            'capacity': 50,  
        }

        self.client.login(email='nonadmin@test.com', password='nonadminpassword')

        response = self.client.post(reverse('edit_course', args=[self.course.id]), form_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('store'))  
        self.course.refresh_from_db()
        self.assertEqual(self.course.name, 'Original Course')
        self.assertEqual(self.course.city, 'Original City')
        self.assertEqual(self.course.price, 100.00)
        self.assertEqual(self.course.capacity, 20)  

class DeleteCourseIntegrationTests(TestCase):
    def setUp(self):
        self.course_type = CourseType.objects.create(name='Test Course Type')

        self.user_admin = get_user_model().objects.create_user(
            email='admin@test.com',  
            password='adminpassword',
        )
        self.customer_admin = Customer.objects.create(user=self.user_admin, name='Admin User', email='admin@test.com', adress='123 Admin St', phone='123456789', admin=True)

        self.user_non_admin = get_user_model().objects.create_user(
            email='nonadmin@test.com', 
            password='nonadminpassword',
        )
        self.customer_non_admin = Customer.objects.create(user=self.user_non_admin, name='Non Admin', email='nonadmin@test.com', adress='123 Non Admin St', phone='987654321', admin=False)

        self.course = Course.objects.create(
            name='Course to Delete',
            price=100.00,
            city='City to Delete',
            course_type=self.course_type,
            start_date='2024-01-01',
            end_date='2024-12-31',
            capacity=20,  
        )

    def test_delete_course_as_admin(self):
        self.client.login(email='admin@test.com', password='adminpassword')

        response = self.client.post(reverse('delete_course', args=[self.course.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('store')) 

        with self.assertRaises(Course.DoesNotExist):
            self.course.refresh_from_db()

    def test_delete_course_as_non_admin(self):
        self.client.login(email='nonadmin@test.com', password='nonadminpassword')

        response = self.client.post(reverse('delete_course', args=[self.course.id]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('store')) 

        self.course.refresh_from_db()
        self.assertEqual(self.course.name, 'Course to Delete')


