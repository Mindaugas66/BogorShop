from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.cache import cache_control
from .models import Flowers, Decorations, DecorationType, CartItem, DeliveryOption, OrderFlower, OrderDecoration, Order
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import ClientForm, AddressForm, ContactUsForm, CustomLoginForm
from .utils import get_or_create_cart
from django.contrib.auth import authenticate, login


def index(request):
    products = Flowers.objects.all()
    context = {
        'products': products,  # Rename to reflect the actual data
    }
    return render(request, 'index.html', context=context)


# User-agent strings for common mobile devices
MOBILE_USER_AGENTS = ['Android', 'iPhone', 'BlackBerry', 'Opera Mini', 'Windows Phone']


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@never_cache
def flower(request):
    flowers_data = Flowers.objects.all()
    first_product = flowers_data.first()

    # Fetch decoration categories
    decoration_types = DecorationType.objects.filter(id__in=[1, 4, 6])

    # Detect if the request is from a mobile device
    is_mobile = any(agent in request.META['HTTP_USER_AGENT'].lower() for agent in MOBILE_USER_AGENTS)

    if is_mobile:
        # Render the mobile version of the page
        return render(request, 'bouquet/flowers_mobile.html', {
            'flowers_data': flowers_data,
            'first_product': first_product,
            'decoration_types': decoration_types,  # Pass the decoration categories

        })
    else:
        # Render the desktop version of the page with decoration categories
        return render(request, 'bouquet/flowers_desktop.html', {
            'flowers_data': flowers_data,
            'first_product': first_product,
            'decoration_types': decoration_types,  # Pass the decoration categories
        })

def decoration(request):
    dec_types = DecorationType.objects.all()  # Fetch all decoration types
    # Dictionary to hold the first product price for each decoration type
    first_product_prices = {}

    for dec_type in dec_types:
        # Get the first decoration (product) for the current decoration type
        first_decoration = Decorations.objects.filter(type=dec_type).first()
        if first_decoration:
            # Store the price of the first decoration for this type
            first_product_prices[dec_type.id] = first_decoration.price
        else:
            # If there are no decorations for this type, store None
            first_product_prices[dec_type.id] = None

    context = {
        'dec_types': dec_types,
        'first_product_prices': first_product_prices,  # Pass the dictionary to the template
    }
    return render(request, 'decorations.html', context)


def product_detail(request, deco_type_id):
    # Get the decoration type
    deco_type = get_object_or_404(DecorationType, id=deco_type_id)

    # Get all the decorations (products) associated with this type
    decorations = Decorations.objects.filter(type=deco_type)

    context = {
        'deco_type': deco_type,
        'decorations': decorations,
    }
    return render(request, 'product.html', context)

def faq(request):
    return render(request, 'components/footer/duk.html')


def contact_view(request):
    if request.method == 'POST':
        form = ContactUsForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Jūsų žinutė buvo sėkmingai išsiųsta.')
            return redirect('shop:contact')  # Adjust this to the correct URL name
        else:
            messages.error(request, 'Klaida! Patikrinkite įvestus duomenis.')
    else:
        form = ContactUsForm()

    return render(request, 'components/footer/contacts.html', {'form': form})

def delivery(request):
    return render(request, 'components/footer/shipping.html')


# views.py
def add_to_cart(request):
    """Handle adding flowers or decorations to the cart."""
    cart = get_or_create_cart(request)

    if request.method == 'POST':
        # Add flowers to the cart
        flower_ids = request.POST.getlist('flower_id[]')
        flower_quantities = request.POST.getlist('quantity[]')

        for flower_id, quantity in zip(flower_ids, flower_quantities):
            flower = Flowers.objects.get(id=flower_id)
            quantity = int(quantity)
            if quantity > 0:
                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart, flower=flower, decoration=None
                )
                # Set the quantity directly rather than incrementing
                if created:
                    cart_item.quantity = quantity
                else:
                    cart_item.quantity += quantity
                cart_item.save()

        # Add decorations to the cart
        decoration_ids = request.POST.getlist('decoration_id[]')
        decoration_quantities = request.POST.getlist('quantity[]')

        for decoration_id, quantity in zip(decoration_ids, decoration_quantities):
            decoration = Decorations.objects.get(id=decoration_id)
            quantity = int(quantity)
            if quantity > 0:
                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart, flower=None, decoration=decoration
                )
                # Set the quantity directly rather than incrementing
                if created:
                    cart_item.quantity = quantity
                else:
                    cart_item.quantity += quantity
                cart_item.save()

    return redirect('shop:cart')


def update_cart(request):
    """Update item quantities in the cart."""
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 1))

        try:
            cart_item = CartItem.objects.get(id=item_id)
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()  # Remove item if quantity is zero
        except CartItem.DoesNotExist:
            pass

    return redirect('shop:cart')


def clear_cart(request):
    """Clear all items from the cart."""
    cart = get_or_create_cart(request)

    # Delete all items in the cart
    cart.items.all().delete()
    messages.success(request, 'Krepšelis išvalytas')

    return redirect('shop:cart')


def remove_from_cart(request, item_id):
    """Remove a specific item from the cart."""
    try:
        cart_item = CartItem.objects.get(id=item_id)
        cart_item.delete()
    except CartItem.DoesNotExist:
        pass

    return redirect('shop:cart')


def cart_view(request):
    """ Display the contents of the cart """
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    cart_total = cart.total_price()

    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
    }

    return render(request, 'cart.html', context)


def checkout_view(request):
    """Handle order creation and checkout process."""
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()

    if request.method == 'POST':
        client_form = ClientForm(request.POST)
        address_form = AddressForm(request.POST)

        if client_form.is_valid() and address_form.is_valid():
            # Save the address
            address = address_form.save()

            # Save the client, linking the address
            client = client_form.save(commit=False)
            client.client_address = address
            client.ip = get_client_ip(request)

            # Capture selected delivery option
            delivery_option_id = request.POST.get('delivery_option')
            if delivery_option_id:
                delivery_option = DeliveryOption.objects.get(id=delivery_option_id)
                client.delivery_option = delivery_option

            client.save()

            # Create a new order for this client
            order = Order.objects.create(client=client, delivery_option=client.delivery_option)

            # Process the cart items
            for cart_item in cart_items:
                if cart_item.flower:
                    # Add flowers to the order
                    OrderFlower.objects.create(order=order, flower=cart_item.flower, quantity=cart_item.quantity)
                elif cart_item.decoration:
                    # Add decorations to the order
                    OrderDecoration.objects.create(order=order, decoration=cart_item.decoration, quantity=cart_item.quantity)

            # Clear the cart after order submission
            cart.items.all().delete()  # Remove all items from the cart

            # Display a success message
            messages.success(request, 'Užsakymas pateiktas sėkmingai!')

            # Redirect to checkout complete, passing the order ID for reference
            return redirect('shop:checkout_complete', order_id=order.id)
        else:
            messages.error(request, 'Patikrinkite formos laukus ir bandykite dar kartą.')

    else:
        client_form = ClientForm()
        address_form = AddressForm()

    # Get available delivery options
    delivery_options = DeliveryOption.objects.all()

    return render(request, 'checkout/checkout.html', {
        'client_form': client_form,
        'address_form': address_form,
        'delivery_options': delivery_options,
        'cart_items': cart_items
    })


def checkout_complete_view(request, order_id):
    """Render the checkout complete page showing the order confirmation."""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'checkout/checkout_complete.html', {
        'order': order,
        'cart_total': order.total_price()
    })


def admin_login(request):
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('admin_dashboard')  # Redirect to custom admin dashboard
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = CustomLoginForm()

    return render(request, 'admin/login.html', {'form': form})


@login_required
def admin_dashboard(request):
    # Render a simple dashboard for now, later we can add sections like Orders, Clients, etc.
    return render(request, 'admin/dashboard.html')