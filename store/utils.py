import json
from . models import *

#He modificado course por product
def cookieCart(request):

    try:
        cart = json.loads(request.COOKIES['cart'])
    except:
        cart = {}
    items = []
    order = {'get_cart_total': 0, 'get_cart_items': 0}
    cartItems = order['get_cart_items']

    for i in cart:
        try:
            cartItems += int(cart[i]['quantity'])
            course = Course.objects.get(id=cart[i]['courseId'])
            total = (course.price * int(cart[i]['quantity']))
            order['get_cart_total'] += total
            order['get_cart_items'] += int(cart[i]['quantity'])

            item  = {}
            item['name'] = course.name
            item['img'] = course.image.url
            item['price'] = course.price
            item['id'] = course.id
            item['quantity'] = int(cart[i]['quantity'])
            item['get_total'] = item['quantity'] * course.price
            items.append(item)
        except:
            pass
    return {'cartItems': cartItems, 'order': order, 'items': items}

def cartData(request):
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer = customer, status=Status.objects.get(name='No pagado'))
        cartItems = order.get_cart_items
        items = order.orderitem_set.all()
    else:
        cookieData = cookieCart(request)
        cartItems = cookieData['cartItems']
        order = cookieData['order']
        items = cookieData['items']

    return {'cartItems': cartItems, 'order': order, 'items': items}