from queue import Full
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from .models import *
from .forms import LoginForm, RegisterForm, CustomerForm, ShippingAddressForm, CustumerUpdateForm, CourseForm
from django.contrib.auth import login, logout
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
import json
import datetime
import random
from django.core.mail import send_mail
import string
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from .utils import cookieCart, cartData
from django.db.models import Avg

def store(request):
    query = request.GET.get('q', '')

    course_types = CourseType.objects.all()  # Para los filtros de tipo de curso
    #city_list = Course.objects.values('city').distinct()  # Obtener lista de ciudades disponibles

    # Obtener filtros de la URL
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    course_type_id = request.GET.get('course_type', '')
    city = request.GET.get('city', '')
    sort_order = request.GET.get('sort_order', None)

    filters = {}
    filters_applied = ""

    if price_min:
        filters['price__gte'] = price_min
        filters_applied += f"Precio mínimo: {price_min}. "
    if price_max:
        filters['price__lte'] = price_max
        filters_applied += f"Precio máximo: {price_max}. "
    if course_type_id:
        course_type = course_types.get(id=course_type_id)
        filters['course_type__id'] = course_type_id
        filters_applied += f"Tipo de curso: {course_type.name}. "
    if city:
        filters['city__icontains'] = city
        filters_applied += f"Ciudad: {city}. "

    cart = cartData(request)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, status=Status.objects.get(name='No pagado'))
        items = order.orderitem_set.all()
        cartItems = order.get_cart_items
    else:
        customer = None
        items = []
        order = {'get_cart_total': 0, 'get_cart_items': 0}
        cartItems = order['get_cart_items']

    # Aplicar los filtros de ordenación
    courses = Course.objects.filter(name__icontains=query, **filters)

    if sort_order == 'name':
        courses = courses.order_by('name')
    elif sort_order == 'price':
        courses = courses.order_by('price')
    elif sort_order == 'city':
        courses = courses.order_by('city')
    city_list = set(
        city.strip().lower() for city in Course.objects.values_list('city', flat=True).distinct()
    )
    context = {
        'courses': courses,
        'customer': customer, 
        'query': query, 
        'course_types': course_types, 
        'city_list': city_list, 
        'course_type_id': course_type_id, 
        'city': city,
        'price_min': price_min,
        'price_max': price_max,
        'filters_applied': filters_applied,
        'cartItems': cart['cartItems'],
        'sort_order': sort_order,  # Pasa el valor de la opción seleccionada
    }
    return render(request, 'store/store.html', context)

def showcase(request):
    cart = cartData(request)
    courses_preview = Course.objects.order_by('-id')[:5]

    context = {
        'courses_preview': courses_preview,
        'cartItems': cart['cartItems'],
    }

    return render(request, 'store/preview.html', context)


def cart(request):
    cart = cartData(request)

    context = {'items': cart['items'], 'order': cart['order'], 'cartItems': cart['cartItems']}
    return render(request, 'store/cart.html', context)

def checkout(request):
    shippingData = None
    
    cart = cartData(request)
    
    if cart['cartItems'] <= 0:
            return redirect('store')
    if request.user.is_authenticated:
        try:
            shippingData = ShippingAddress.objects.get(customer=request.user.customer)
        except ShippingAddress.DoesNotExist:
            pass 
    context = {'items': cart['items'], 'order': cart['order'], 'cartItems': cart['cartItems'], 'shippingData':shippingData}
    return render(request, 'store/checkout.html', context)

def about(request):
    cart = cartData(request)
    
    context = {'cartItems': cart['cartItems']}
    return render(request, 'store/about.html', context)

def courseDetails(request, course_id):
    # Obtener datos del carrito
    cart = cartData(request)

    # Obtener el curso específico o devolver un 404 si no existe
    course = get_object_or_404(Course, pk=course_id)

    # Calcular la duración del curso en días
    duration = (course.end_date - course.start_date).days

    # Comprobar si el curso está disponible
    is_available = course.is_available

    return render(
        request, 
        'store/course.html', 
        {
            'course': course,
            'cartItems': cart['cartItems'], 
            'duration': duration,
            'is_available': is_available,
        }
    )

@login_required
def create_course(request):
    customer = Customer.objects.get(user=request.user)
    if customer.admin != True:
        return redirect('store')
    else:
        if request.method == 'POST':
            form = CourseForm(request.POST, request.FILES)  # Maneja también los archivos subidos (imagen)
            if form.is_valid():
                form.save()
                return redirect('store')  # Redirige a la página principal o donde desees
            else:
                form.add_error(None, form.errors)
                context = {'form': form}
                return render(request, 'store/create_course.html', context)
        else:
            form = CourseForm()
            context = {'form': form}
            return render(request, 'store/create_course.html', context)

def auth_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('store')
            else:
                form.add_error(None, 'Usuario o contraseña incorrectos')
                context = {'form': form}
                return render(request, 'store/login.html', context)
        else:
            form.add_error(None, form.errors)
            context = {'form': form}
            return render(request, 'store/login.html', context)
    else:
        form = LoginForm()
        context = {'form': form}
        return render(request, 'store/login.html', context)

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            customer, created = Customer.objects.get_or_create(
                email=user.email, 
                name=form.cleaned_data['name'], 
                adress=form.cleaned_data['adress'], 
                phone=form.cleaned_data['phone']
            )
            customer.user = user
            customer.save()
            login(request, user)
            return redirect('store')
        else:
            form.add_error(None, form.errors)
            context = {'form': form}
            return render(request, 'store/register.html', context)
    else:
        form = RegisterForm()
        context = {'form': form}
        return render(request, 'store/register.html', context)
    
def auth_logout(request):
    logout(request)
    return redirect('store')

@login_required
def profile(request, customer_id):
    cart = cartData(request)
    customer = Customer.objects.get(user=request.user)
    customer_id = customer.id
    shipping_address = ShippingAddress.objects.filter(customer=customer)
    return render(request, 'store/profile.html', {'customer': customer, 'shipping_address': shipping_address, 'customer_id': customer_id, 'cartItems': cart['cartItems']})

@login_required
def create_update_profile(request):
    cart = cartData(request)
    customer = request.user.customer
    shipping_address = customer.shippingaddress_set.last()
    form = CustumerUpdateForm(request.POST or None, instance=customer)
    if request.method == 'POST':
        if form.is_valid():
            new_profile = form.save(commit=False)
            new_profile.save()
            return redirect('store')
    return render(request, 'store/delivery_form.html', {'form': form, 'customer': customer, 'cartItems': cart['cartItems']})

def user_has_perm(user):
    if not user.is_staff:
        return False
    return True

@login_required
@user_passes_test(user_has_perm, redirect_field_name=None)
def customer_list(request):
    customers = Customer.objects.all()
    return render(request, 'store/customer_list.html', {'customers': customers})

@login_required
@user_passes_test(user_has_perm, redirect_field_name=None)
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'store/customer_form.html', {'form': form})

@login_required
@user_passes_test(user_has_perm, redirect_field_name=None)
def customer_update(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'store/customer_form.html', {'form': form})

@login_required
@user_passes_test(user_has_perm, redirect_field_name=None)
def customer_delete(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    customer.delete()
    return redirect('customer_list')


@csrf_exempt
def updateItem(request):
    data = json.loads(request.body)
    action = data['action']
    courseId = data['courseId']

    cart = cartData(request)
    course = Course.objects.get(id=courseId)
    
    if request.user.is_authenticated:
        order = cart['order']  
        orderItem, created = OrderItem.objects.get_or_create(order=order, course=course)
        if action == 'add':
            try:
                quantity = int(data['quantity'])
            except:
                return JsonResponse({'error': 'Cantidad inválida'}, safe=False)
            if course.capacity - (quantity + orderItem.quantity) < 0:
                return JsonResponse({'error': 'Cantidad superior a stock actual: '+ str(course.capacity)}, safe=False)
            
            orderItem.quantity = orderItem.quantity + quantity
            orderItem.save()
            return JsonResponse({"success": "Se ha añadido el producto a la cesta"}, safe=False)
        elif action == 'remove':
            orderItem.quantity = orderItem.quantity - 1
            orderItem.save()
            if orderItem.quantity <= 0:
                orderItem.delete()
            return JsonResponse({}, safe=False)
    else:
        if action == 'add':
            try:
                quantity = int(data['quantity'])
            except:
                return JsonResponse({'error': 'Cantidad inválida'}, safe=False)
            if course.capacity - quantity < 0:
                return JsonResponse({'error': 'Cantidad superior a stock actual: '+ str(course.capacity)}, safe=False)
            return JsonResponse({"success": "Se ha añadido el producto a la cesta"}, safe=False)
        return JsonResponse({}, safe=False)

@transaction.atomic
def processOrder(request):
    body = json.loads(request.body)
    timestamp = datetime.datetime.now().strftime("%d%m%Y")
    tracking_id = timestamp + ''.join(random.choices(string.ascii_uppercase + string.digits, k=14))
    while Order.objects.filter(tracking_id=tracking_id).exists():
        tracking_id = timestamp + ''.join(random.choices(string.ascii_uppercase + string.digits, k=14))
    contrareembolso = body['contrareembolso']

    cart = cartData(request)
    
    if request.user.is_authenticated:
        order = cart['order']
    else:
        customer, created = Customer.objects.get_or_create(email=body['form']['email'], name=body['form']['name'], phone=body['form']['phone'])
        if contrareembolso:
            order = Order.objects.create(customer=customer, status=Status.objects.get(name='No pagado'))
        else:
            order = Order.objects.create(customer=customer, status=Status.objects.get(name='En trámite'))
        items = cart['items']
        for item in items:
            course = Course.objects.get(name=item['name'])
            orderItem = OrderItem.objects.create(order=order, course=course, quantity=item['quantity'])
            orderItem.save()

    order.date_ordered = datetime.datetime.now()
    if contrareembolso:
        order.status = Status.objects.get(name='No pagado')
    else:
        order.status = Status.objects.get(name='En trámite')
    order.tracking_id = tracking_id
    shipping_address = ShippingAddress.objects.create()
    shipping_address.customer = None
    shipping_address.address = body['shipping']['address']
    shipping_address.city = body['shipping']['city']
    shipping_address.state = body['shipping']['state']
    shipping_address.zipcode = body['shipping']['zipcode']
    shipping_address.country = body['shipping']['country']

    # check all products in cart are available
    order_items = order.orderitem_set.all()
    for order_item in order_items:
        if order_item.course.capacity - order_item.quantity < 0:
            return JsonResponse({'error': 'No hay suficiente espacio en el curso: ' + str(order_item.course.name)}, safe=False)

    # reduce stock of products in cart
    for order_item in order_items:
        order_item.course.capacity = order_item.course.capacity - order_item.quantity
        try:
            order_item.course.save()
        except:
            return JsonResponse({'error': 'No hay suficiente espacio en el curso: ' + str(order_item.course.name)}, safe=False)

    shipping_address.save()
    order.shipping_address = shipping_address
    order.save()

    order_items = order.orderitem_set.all()
    course_info_list = []

    for order_item in order_items:
        course_name = order_item.course.name
        quantity = order_item.quantity
        price = order_item.course.price 
        course_info = f"Producto: {course_name}, Cantidad: {quantity}, Precio: {price}"
        course_info_list.append(course_info)

    full_course_info = "\n".join(course_info_list)
    if request.user.is_authenticated:
        user = request.user
        customer = user.customer

        customer_name = customer.name
        customer_email = customer.email
    else:
        customer_name = body['form']['name']
        customer_email = body['form']['email']
        
    CourseReservation.objects.create(
        order=order,
        customer=order.customer,
        reservation_date=datetime.datetime.now(),
        reserved_on=None,  # Esto lo hace NULL en la base de datos
        is_confirmed=False  # Ajusta según sea necesario
    )

    enviar_correo(customer_email, customer_name, full_course_info, order.tracking_id, order.date_ordered, order.shipping_address)

    return JsonResponse({'tracking': tracking_id}, safe=False)

def enviar_correo(email_destino, username, resume_order, id_pedido, fecha, direccion):
    asunto = ' ¡Gracias por tu compra en OppositionUS!'
    mensaje = f'Estimado/a {username},' '\n' \
              f'En nombre de todo el equipo de OppositionUS, queremos expresar nuestro más sincero agradecimiento por tu reciente compra en nuestra tienda en línea.' '\n' '\n' \
              f'Nos emociona saber que has elegido OppositionUS para adquirir tus clase de oposiciones, y estamos comprometidos a brindarte la mejor experiencia posible. Valoramos tu confianza en nuestros servicios.' '\n' '\n' \
              f'Detalles de tu pedido:' '\n' \
              f'Número de seguimiento: {id_pedido}\n' \
              f'Fecha de compra: {fecha}\n' \
              f'Dirección de envío: {direccion}\n' \
              f'Resumen de su pedido: {resume_order}\n' '\n'\
              f'Si tienes alguna pregunta sobre tu pedido o necesitas asistencia adicional, no dudes en ponerte en contacto con nuestro equipo de atención al cliente. Estamos aquí para ayudarte en cualquier momento.\n' \
              f'Esperamos que disfrutes al máximo tus nuevas clases. ¡Gracias por formar parte de la comunidad de OppositionUS!'

    remitente = 'oppositionusoficial@gmail.com'
    destinatarios = [email_destino]

    send_mail(asunto, mensaje, remitente, destinatarios)
    return HttpResponse('Correo enviado exitosamente.')

def track_orders(request):
    cart = cartData(request)
    if request.method == 'POST':
        tracking_id = request.POST.get('tracking_id')
        if tracking_id:
            tracking = Order.objects.exclude(status=Status.objects.get(name='No realizado')).filter(tracking_id=tracking_id)
            if tracking:
                return HttpResponseRedirect("/tracking/" + tracking_id)
            else:
                return render(request, 'store/track_order.html', {'cartItems': cart['cartItems']})
        else:
            return render(request, 'store/track_order.html', {'error_message': 'Por favor, proporciona un ID de seguimiento.', 'cartItems': cart['cartItems']})
    return render(request, 'store/track_order.html', {'cartItems': cart['cartItems']})

def track_order(request, tracking_id):
    cart = cartData(request)
    try:
        order = get_object_or_404(Order, tracking_id=tracking_id)
        order_items = OrderItem.objects.filter(order=order)
        order_courses = [item.course.id for item in order_items]
        claimed_courses = Claim.objects.filter(order=order).values_list('course_id', flat=True)
        if request.user.is_authenticated:
            user_ratings = Rating.objects.filter(customer=request.user.customer , course_id__in=order_courses).values_list('course_id', flat=True)
        else:
            user_ratings = Rating.objects.filter(customer=order.customer , course_id__in=order_courses).values_list('course_id', flat=True)

        total_cost = order.get_cart_total

        context = {'order': order, 'order_items': order_items, 'total_cost': total_cost, 'cartItems': cart['cartItems'],'user_ratings': user_ratings, 'claimed_courses': claimed_courses}
    except Order.DoesNotExist:
        return render(request, 'store/track_order.html', {'error_message': f'No existe un pedido con ID de seguimiento {tracking_id}.'})

    return render(request, 'store/track_order_status.html', context)

@login_required
def view_orders(request):
    cart = cartData(request)
    # orders with status distinct from 'No realizado'
    user_orders = Order.objects.filter(customer=request.user.customer).exclude(status=Status.objects.get(name='No realizado')).order_by('-date_ordered')
    context = {'user_orders': user_orders, 'cartItems': cart['cartItems']}
    return render(request, 'store/view_orders.html', context)

@login_required
def review_order(request, course_id):
    cart = cartData(request)
    course = get_object_or_404(Course, id=course_id)
    error_message = None
    if request.method == 'POST':
        rating_value = request.POST.get('rating')
        comment = request.POST.get('comment')
        if not rating_value:
            error_message = 'Debes proporcionar una valoración.'
        else:
            rating = Rating.objects.create(
                course=course,
                customer=request.user.customer,
                rating=rating_value,
                comment=comment
            )
            rating.save()
            messages.success(request, 'Tu valoración ha sido enviada.')
            return redirect('view_orders')

    context = {'course':course, 'cartItems': cart['cartItems'],'error_message': error_message}
    return render(request, 'store/review_order.html', context)


def claim_product(request, course_id,order_id):
    cart = cartData(request)
    course = get_object_or_404(Course, id=course_id)
    order = get_object_or_404(Order, id=order_id)
    error_message = None
    if request.method == 'POST':
        description = request.POST.get('claimDescription')
        if not description:
            error_message = 'Debes proporcionar una descripción.'
        else:
            claim = Claim.objects.create(
                order=order,
                course=course,
                customer=order.customer,
                description=description
            )
            claim.save()
            messages.success(request, 'Tu reclamación ha sido enviada.')
            return HttpResponseRedirect("/tracking/" + order.tracking_id)

    context = {'course':course,'order': order,  'cartItems': cart['cartItems'], 'error_message': error_message}
    return render(request, 'store/claim_product.html', context)

#carrito#########################################################################################################################################

@csrf_exempt
def add_to_cart(request, course_id):
    # Comprobar si el método de la solicitud es POST
    if request.method == 'POST':
        try:
            # Obtener el curso correspondiente
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return JsonResponse({'error': 'Curso no encontrado'}, status=404)

        # Obtener el carrito de la sesión (usando cartData)
        cart = cartData(request)
        order = cart['order']  # Obtener el pedido asociado al carrito

        # Crear o obtener el item en el carrito
        orderItem, created = OrderItem.objects.get_or_create(order=order, course=course)

        # Si el curso no está en el carrito, se agrega
        if created:
            return JsonResponse({"success": "Curso añadido al carrito"}, status=200)
        else:
            # Si ya estaba en el carrito, solo actualizamos la cantidad si es necesario
            orderItem.quantity += 1
            orderItem.save()
            return JsonResponse({"success": "Curso añadido al carrito"}, status=200)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def add_course_to_cart(request, course_id):
    # Obtener el carrito del usuario (puedes personalizar esta lógica)
    cart, created = cart.objects.get_or_create(user=request.user, completed=False)

    # Obtener el curso
    course = get_object_or_404(Course, id=course_id)

    # Verificar si ya está en el carrito
    cart_item, created = CartItem.objects.get_or_create(cart=cart, course=course)
    if not created:
        cart_item.quantity += 1  # Incrementar la cantidad
    cart_item.save()

    return JsonResponse({'message': 'Curso añadido al carrito'}, status=200)


@login_required
def create_course(request):
    customer = Customer.objects.get(user=request.user)
    if customer.admin != True:
        return redirect('store')
    else:
        if request.method == 'POST':
            form = CourseForm(request.POST, request.FILES)  # Maneja también los archivos subidos (imagen)
            if form.is_valid():
                form.save()
                return redirect('store')  # Redirige a la página principal o donde desees
            else:
                form.add_error(None, form.errors)
                context = {'form': form}
                return render(request, 'store/create_course.html', context)
        else:
            form = CourseForm()
            context = {'form': form}
            return render(request, 'store/create_course.html', context)
        

@login_required
def edit_course(request, course_id):
    customer = Customer.objects.get(user=request.user)
    if not customer.admin:
        return redirect('store')
    
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return redirect('store')

    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            return redirect('store')
        else:
            form.add_error(None, form.errors) 
            context = {'form': form, 'course': course}
            return render(request, 'store/edit_course.html', context)
    else:
        form = CourseForm(instance=course)
        context = {'form': form, 'course': course}
        return render(request, 'store/edit_course.html', context)
    

@login_required
def delete_course(request, course_id):
    customer = Customer.objects.get(user=request.user)
    if not customer.admin:
        return redirect('store')

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        messages.error(request, 'El curso no existe.')
        return redirect('store')

    if request.method == 'POST':
        course.delete()
        messages.success(request, f'El curso "{course.name}" fue eliminado exitosamente.')
        return redirect('store')

    context = {'course': course}
    return render(request, 'store/delete_course.html', context)


@login_required
def list_customers(request):
    customer = Customer.objects.get(user=request.user)
    if not customer.admin:
        return redirect('store')

    customers = Customer.objects.exclude(user=request.user)

    context = {'customers': customers}
    return render(request, 'store/list_customers.html', context)


@login_required
def delete_customer(request, customer_id):
    customer = Customer.objects.get(user=request.user)
    if not customer.admin:
        return redirect('store')

    try:
        customerDelete = Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        messages.error(request, 'El cliente no existe.')
        return redirect('list_customers')

    if request.method == 'POST':
        customerDelete.delete()
        messages.success(request, f'El cliente "{customerDelete.name}" fue eliminado exitosamente.')
        return redirect('list_customers')

    context = {'customers': customerDelete}
    return render(request, 'store/delete_customer.html', context)


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import CourseReservation
from django.contrib import messages

@login_required
def list_reservations(request):
    customer = Customer.objects.get(user=request.user)
    
    if not customer.admin:
        return redirect('store')

    reservations = CourseReservation.objects.all()

    context = {
        'reservations': reservations
        
    }

    return render(request, 'store/list_reservations.html', context)


@login_required
def confirmar_reserva(request, reservation_id):
    customer = Customer.objects.get(user=request.user)
    if not customer.admin:
        return redirect('store')

    reservation = get_object_or_404(CourseReservation, id=reservation_id)

    if request.method == 'POST':
        reservation.is_confirmed = True
        reservation.reserved_on = datetime.datetime.now()
        reservation.save()
        order = reservation.order
        if order:  # Asegúrate de que la orden existe
            order.status = Status.objects.get(name='Aceptada')
            order.save()  # Guarda los cambios en el modelo Order

            messages.success(request, f'La reserva para {reservation.order.tracking_id} ha sido aceptada.')
        else:
            messages.error(request, 'La reserva no ha podido se aceptada.')
        return redirect('list_reservations')

    return redirect('list_reservations')

@login_required
def denegar_reserva(request, reservation_id):
    customer = Customer.objects.get(user=request.user)
    if not customer.admin:
        return redirect('store')

    reservation = get_object_or_404(CourseReservation, id=reservation_id)

    if request.method == 'POST':
        reservation.is_confirmed = False
        reservation.reserved_on = datetime.datetime.now()
        reservation.save()
        order = reservation.order
        if order:  # Asegúrate de que la orden existe
            order.status = Status.objects.get(name='Denegada')
            order.save()  # Guarda los cambios en el modelo Order

            messages.success(request, f'La reserva para {reservation.order.tracking_id} ha sido denegada.')
        else:
            messages.error(request, 'La reserva no se ha podido denegar.')

        return redirect('list_reservations')

    return redirect('list_reservations')

@login_required
def confirmar_pago(request, reservation_id):
    customer = Customer.objects.get(user=request.user)
    if not customer.admin:
        return redirect('store')

    reservation = get_object_or_404(CourseReservation, id=reservation_id)

    if request.method == 'POST':
        # Cambiar el estado de la orden asociada
        order = reservation.order
        if order:  # Asegúrate de que la orden existe
            order.status = Status.objects.get(name='En trámite')
            order.save()  # Guarda los cambios en el modelo Order

            messages.success(request, f'La reserva para {reservation.order.tracking_id} ha sido pagada.')
        else:
            messages.error(request, 'No se ha podido realizar el pago de la reserva.')

        return redirect('list_reservations')

    return redirect('list_reservations')

