//He cambiado productId por courseId para el carrito
var updateBtns = document.getElementsByClassName('update-cart')
for (var i = 0; i < updateBtns.length; i++) {
    updateBtns[i].addEventListener('click', function () {
        // Capturar valores desde los atributos data-*
        var courseId = this.dataset.course;
        var action = this.dataset.action;
        var quantity = this.dataset.quantity
        
        if (user == 'AnonymousUser') {
            addCookieItem(courseId, action, quantity);
        } else {
            updateUserOrder(courseId, action, quantity).then((data) => {
                    if (data.error) {
                        alert(data.error);
                    } else if (data.success) {
                        alert(data.success);
                        window.location.reload();
                    }
                });
        }
    });
}


function addCookieItem(courseId, action, quantity){
    var id = null;
        for (var key in cart){
            if (cart[key].courseId == courseId){
                id = key
                break
            }
        }
    if (action == 'add'){
        if (id) {
            updateUserOrder(courseId, action, parseInt(quantity) + parseInt(cart[id].quantity))
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                } else {
                    if (data.success) {
                        cart[id].quantity = parseInt(quantity) + parseInt(cart[id].quantity)
                        document.cookie = 'cart=' + JSON.stringify(cart) + ";domain=;path=/"
                        alert(data.success);
                        window.location.reload()
                    }
                }
            })
            
        } else {
            updateUserOrder(courseId, action, quantity)
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                } else {
                    if (data.success) {
                        cart[Object.keys(cart).length] = {'courseId': courseId, 'quantity':quantity}
                        document.cookie = 'cart=' + JSON.stringify(cart) + ";domain=;path=/"
                        alert(data.success);
                        window.location.reload()
                    }
                }
            })
        }
    } else if (action == 'remove'){   
        if (id) {
            cart[id].quantity = parseInt(cart[id].quantity) - 1
            if (cart[id].quantity <= 0){
                delete cart[id]
            }
            document.cookie = 'cart=' + JSON.stringify(cart) + ";domain=;path=/"
            window.location.reload()
        }
    }
}

function updateUserOrder(courseId, action, quantity){
    
    var url = '/update_item/'
    var csrftoken = getCookie('csrftoken')
    body = JSON.stringify({'courseId': courseId, 'action': action, 'quantity': quantity})
    
    var res = fetch(url, {
        method:'POST',
        headers:{
        'Content-Type':'application/json',
        'X-CSRFToken':csrftoken,
        },
        body: body,
    })
    .then((response) => {
        return response.json()
    })

    return res
}