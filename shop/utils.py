from .models import Cart

def get_or_create_cart(request):
    # Create or retrieve a cart using the session key
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart