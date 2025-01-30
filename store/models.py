from collections.abc import Iterable
from django.db import models
from django.contrib.auth.models import UserManager
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class OppositionUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user
    
    def create_user(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_admin", False)
        return self._create_user(email, password, **extra_fields)
    
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_admin", True)
        return self._create_user(email, password, **extra_fields)
    
class OppositionUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name='email', max_length=60, unique=True)
    date_joined = models.DateTimeField(verbose_name='date joined', auto_now_add=True)
    last_login = models.DateTimeField(verbose_name='last login', auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'email' 
    REQUIRED_FIELDS = [] 
    objects = OppositionUserManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    

class Customer(models.Model):
    user = models.OneToOneField(OppositionUser, null=True, blank=True, on_delete = models.CASCADE)
    name = models.CharField(max_length=200 , null=False, blank=False)
    email = models.EmailField(max_length=200 , null=True, blank=False)
    #NUEVOS CAMPOS PARA FORMULARIO
    adress = models.CharField(max_length=200 , null=False, blank=False)
    phone = models.IntegerField(null=False, blank=False, validators=[MaxValueValidator(999999999), MinValueValidator(100000000)])
    admin = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class CourseType(models.Model):
    name = models.CharField(max_length=50, unique=True, null=False, blank=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Course type'
        verbose_name_plural = 'Course types'
        ordering = ['name']


class Course(models.Model):
    name = models.CharField(max_length=200, null=False, blank=False)
    image = models.ImageField(upload_to='courses')
    price = models.DecimalField(max_digits=7, decimal_places=2, null=False, blank=False, validators=[MinValueValidator(0)])
    details = models.CharField(max_length=200, null=True, blank=True)
    city = models.CharField(max_length=200, null=False, blank=False)
    course_type = models.ForeignKey(CourseType, null=True, on_delete=models.SET_NULL)
    capacity = models.IntegerField(null=False, blank=False, validators=[MinValueValidator(0)])
    is_available = models.BooleanField(default=True)
    start_date = models.DateField(null=False, blank=False)  
    end_date = models.DateField(null=False, blank=False)  

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        ordering = ['name']
 
class Status(models.Model):
    name = models.CharField(max_length=200 , null=False, unique=True, blank=False)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Status'
        verbose_name_plural = 'Status'
        ordering = ['name']

class ShippingAddress(models.Model):
    customer = models.ForeignKey(Customer, null=True, on_delete = models.SET_NULL)
    address = models.CharField(max_length=200 , null=False, blank=False)
    city = models.CharField(max_length=200 , null=False, blank=False)
    state = models.CharField(max_length=200 , null=False, blank=False)
    zipcode = models.CharField(max_length=200 , null=False, blank=False)
    country = models.CharField(max_length=200 , null=False, blank=False)
    date_added = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.address

    class Meta:
        verbose_name = 'Shipping address'
        verbose_name_plural = 'Shipping addresses'
        ordering = ['-date_added']

class Order(models.Model):
    customer = models.ForeignKey(Customer, null=True, on_delete = models.SET_NULL)
    date_ordered = models.DateTimeField(auto_now_add=True)
    status = models.ForeignKey(Status, null=False, on_delete =models.CASCADE)
    tracking_id=models.CharField(max_length=200 , null=True, unique=True, blank=False)
    shipping_address = models.ForeignKey('ShippingAddress', null=True, on_delete = models.SET_NULL)

    def __str__(self):
        return str(self.id)
    
    @property
    def get_cart_items(self):
        orderitems = self.orderitem_set.all()
        return sum([item.quantity for item in orderitems])

    @property
    def get_cart_total(self):
        orderitems = self.orderitem_set.all()
        return sum([item.get_total for item in orderitems])
    
class OrderItem(models.Model):
    course = models.ForeignKey(Course, null=True, on_delete=models.SET_NULL)
    order = models.ForeignKey(Order, null=True, on_delete = models.SET_NULL)
    quantity = models.IntegerField(default=0, null=True, blank=True, validators=[MinValueValidator(0)])
    date_added = models.DateTimeField(auto_now_add=True)

    @property
    def get_total(self):
        return self.course.price * self.quantity

class Rating(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, null=True, on_delete=models.SET_NULL)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()

class Claim(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    description = models.TextField()
    date_submitted = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'order')

    def __str__(self):
        return f'Claim {self.id} by {self.customer.email}'

class CourseReservation(models.Model):
    order = models.ForeignKey(Order, null=True, on_delete=models.SET_NULL)
    customer = models.ForeignKey(Customer, null=True, on_delete=models.SET_NULL)
    reservation_date = models.DateTimeField(auto_now_add=True)
    reserved_on = models.DateTimeField(null=True)
    
    is_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f'Reservation {self.id} for {self.order.id} by {self.order.id}'

    class Meta:
        verbose_name = 'Course reservation'
        verbose_name_plural = 'Course reservations'
        ordering = ['-reservation_date']

