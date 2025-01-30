from django.test import TestCase
from django.urls import reverse
from .models import Customer, Status, CourseType, Course, Order, OppositionUser
from datetime import date

class ListCustomersViewTest(TestCase):

    def setUp(self):
        self.status_no_realizado = Status.objects.create(name='No realizado')
        self.status_no_pagado = Status.objects.create(name='No pagado')  # Crear el estado requerido

        self.user_normal = OppositionUser.objects.create_user(email='normaluser@example.com', password='password')
        self.user_admin = OppositionUser.objects.create_user(email='adminuser@example.com', password='password', is_admin=True)

        self.customer_normal = Customer.objects.create(
            user=self.user_normal, 
            name='Normal User', 
            email='normaluser@example.com', 
            adress='123 St', 
            phone=123456789, 
            admin=False
        )

        self.customer_admin = Customer.objects.create(
            user=self.user_admin, 
            name='Admin User', 
            email='adminuser@example.com', 
            adress='456 St', 
            phone=987654321, 
            admin=True
        )

    def test_user_without_admin_access(self):
    
        self.client.login(email='normaluser@example.com', password='password')

        
        response = self.client.get(reverse('list_customers'))

        
        self.assertRedirects(response, reverse('store'))

    def test_user_with_admin_access(self):
        self.client.login(email='adminuser@example.com', password='password')

        response = self.client.get(reverse('list_customers'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'store/list_customers.html')
        self.assertIn('customers', response.context)
        customers = response.context['customers']
        self.assertEqual(customers.count(), 1)  
        self.assertEqual(customers.first().user.email, 'normaluser@example.com')
    
    def test_customers_exclude_current_user(self):
        self.client.login(email='adminuser@example.com', password='password')

        response = self.client.get(reverse('list_customers'))

        customers = response.context['customers']
        self.assertEqual(customers.count(), 1)  
        self.assertNotIn(self.customer_admin, customers) 

    def test_unauthenticated_user_redirect(self):
        response = self.client.get(reverse('list_customers'))

        self.assertRedirects(response, f'/login/?next={reverse("list_customers")}')

    def test_template_used(self):
        self.client.login(email='adminuser@example.com', password='password')

        response = self.client.get(reverse('list_customers'))

        self.assertTemplateUsed(response, 'store/list_customers.html')

class StoreViewTest(TestCase):

    def setUp(self):
        self.status_no_realizado = Status.objects.create(name='No realizado')
        self.status_no_pagado = Status.objects.create(name='No pagado')  

        self.course_type_1 = CourseType.objects.create(name='Mathematics')
        self.course_type_2 = CourseType.objects.create(name='Science')

        self.course_1 = Course.objects.create(
            name='Math 101', 
            price=100, 
            city='New York', 
            course_type=self.course_type_1, 
            start_date='2024-01-01', 
            end_date='2024-06-01',
            capacity=30  
        )
        self.course_2 = Course.objects.create(
            name='Science 101', 
            price=150, 
            city='Los Angeles', 
            course_type=self.course_type_2, 
            start_date='2024-01-01', 
            end_date='2024-06-01',
            capacity=25  
        )

        self.user_normal = OppositionUser.objects.create_user(email='normaluser@example.com', password='password')
        self.user_admin = OppositionUser.objects.create_user(email='adminuser@example.com', password='password', is_admin=True)
        
        self.customer_normal = Customer.objects.create(
            user=self.user_normal, 
            name='Normal User', 
            email='normaluser@example.com', 
            adress='123 St', 
            phone=123456789, 
            admin=False
        )
        self.customer_admin = Customer.objects.create(
            user=self.user_admin, 
            name='Admin User', 
            email='adminuser@example.com', 
            adress='456 St', 
            phone=987654321, 
            admin=True
        )
        self.order = Order.objects.create(customer=self.customer_normal, status=self.status_no_realizado)

    def test_store_page_loads(self):
        response = self.client.get(reverse('store'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'store/store.html')

    def test_search_courses_by_name(self):
        response = self.client.get(reverse('store') + '?q=Math')

        self.assertIn(self.course_1, response.context['courses'])
        self.assertNotIn(self.course_2, response.context['courses'])

    def test_filter_courses_by_price_min(self):
        response = self.client.get(reverse('store') + '?price_min=120')

        self.assertIn(self.course_2, response.context['courses'])
        self.assertNotIn(self.course_1, response.context['courses'])

    def test_filter_courses_by_course_type(self):
        response = self.client.get(reverse('store') + f'?course_type={self.course_type_1.id}')

        self.assertIn(self.course_1, response.context['courses'])
        self.assertNotIn(self.course_2, response.context['courses'])

    def test_filter_courses_by_city(self):
        response = self.client.get(reverse('store') + '?city=New York')

        self.assertIn(self.course_1, response.context['courses'])
        self.assertNotIn(self.course_2, response.context['courses'])

    def test_sort_courses_by_price(self):
        response = self.client.get(reverse('store') + '?sort_order=price')

        self.assertEqual(response.context['courses'][0], self.course_1)
        self.assertEqual(response.context['courses'][1], self.course_2)

    def test_sort_courses_by_name(self):
        response = self.client.get(reverse('store') + '?sort_order=name')

        self.assertEqual(response.context['courses'][0], self.course_1)
        self.assertEqual(response.context['courses'][1], self.course_2)

    def test_cart_is_visible_for_authenticated_users(self):
        self.client.login(email='normaluser@example.com', password='password')

        response = self.client.get(reverse('store'))

        self.assertIn('cartItems', response.context)
        self.assertEqual(response.context['cartItems'], 0) 

    def test_cart_is_not_visible_for_anonymous_users(self):
        response = self.client.get(reverse('store'))

        self.assertIn('cartItems', response.context)
        self.assertEqual(response.context['cartItems'], 0)

    def test_filters_applied_displayed(self):
        response = self.client.get(reverse('store') + '?price_min=100&course_type={}&city=New York'.format(self.course_type_1.id))

        self.assertIn('Precio mínimo: 100. Tipo de curso: Mathematics. Ciudad: New York. ', response.context['filters_applied'])

class CourseDetailsViewTest(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        # Crear estados necesarios
        cls.status_no_realizado = Status.objects.create(name='No realizado')
        cls.status_no_pagado = Status.objects.create(name='No pagado')  # Estado necesario

        # Crear usuario y cliente
        cls.user = OppositionUser.objects.create_user(
            email='testuser@example.com',  
            password='testpassword'        
        )

        cls.customer = Customer.objects.create(user=cls.user, phone='123456789')  

        # Crear tipo de curso y cursos
        course_type = CourseType.objects.create(name='Online')

        cls.course = Course.objects.create(
            name='Curso de Python', 
            start_date=date(2024, 1, 1),  
            end_date=date(2024, 1, 31),   
            price=100.00,  
            course_type=course_type,  
            city='Madrid', 
            is_available=True,
            capacity=25  
        )

    def test_course_details_authenticated_user(self):
        self.client.login(email='testuser@example.com', password='testpassword') 

        response = self.client.get(reverse('details', args=[self.course.id]))

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['course'].name, self.course.name)

    def test_course_details_anonymous_user(self):
        response = self.client.get(reverse('details', args=[self.course.id]))

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['course'].name, self.course.name)

        expected_duration = (self.course.end_date - self.course.start_date).days
        self.assertEqual(response.context['duration'], expected_duration)

    def test_course_availability(self):
        self.course.is_available00 = True
        self.course.save()

        response = self.client.get(reverse('details', args=[self.course.id]))

        self.assertEqual(response.context['course'].is_available, True)

    def test_course_details_for_nonexistent_course(self):
        response = self.client.get(reverse('details', args=[999]))  

        self.assertEqual(response.status_code, 404)

