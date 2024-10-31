from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.cache import cache_control
from .models import Flowers, Decorations, DecorationType, CartItem, DeliveryOption, OrderFlower, OrderDecoration, Order, WrappingPaper
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import ClientForm, AddressForm, ContactUsForm, CustomLoginForm, FlowersAdminForm, DecorationsAdminForm, WrappingPaperAdminForm
from .utils import get_or_create_cart
from django.contrib.auth import authenticate, login
from django.db.models import Sum


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

    # Render a single template for both mobile and desktop
    return render(request, 'bouquet/flowers.html', {
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


# Admin views


def admin_login(request):
    if request.method == 'POST':
        print(request.POST)  # Debugging line to check form data
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('shop:admin_dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = CustomLoginForm()

    return render(request, 'admin/login.html', {'form': form})


@login_required
def admin_dashboard(request):
    # Count the number of flowers, decorations, and orders
    flower_count = Flowers.objects.count()
    decoration_count = Decorations.objects.count()
    order_count = Order.objects.count()

    # Calculate total revenue from all orders
    total_revenue = sum(order.total_price() for order in Order.objects.all())

    context = {
        'flower_count': flower_count,
        'decoration_count': decoration_count,
        'order_count': order_count,
        'total_revenue': total_revenue,
    }
    return render(request, 'admin/dashboard.html', context)


@login_required
def admin_products(request):
    # Fetch all products for the admin to manage
    flowers = Flowers.objects.all()
    decorations = Decorations.objects.all()

    return render(request, 'admin/admin_products.html', {
        'flowers': flowers,
        'decorations': decorations,
    })


@login_required
def admin_orders(request):
    orders = Order.objects.all()

    # Handle POST request for updating order or payment status from the list view
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        order = get_object_or_404(Order, id=order_id)

        # Update payment status
        if 'payment_status' in request.POST:
            new_payment_status = request.POST.get('payment_status')
            if new_payment_status in ['paid', 'not_paid']:
                order.payment_status = new_payment_status
                order.save()
                return JsonResponse({'success': True, 'payment_status': new_payment_status})

        # Update order status
        elif 'status' in request.POST:
            new_status = request.POST.get('status')
            if new_status in [choice[0] for choice in Order.STATUS_CHOICES]:
                order.status = new_status
                order.save()
                return JsonResponse({'success': True, 'status': new_status})

        # If an error occurs, return a JSON response with success as False
        return JsonResponse({'success': False, 'error': 'Invalid status value'})

    # For a GET request, render the list of orders
    context = {
        'orders': orders,
    }
    return render(request, 'admin/admin_orders.html', context)


@login_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Handle POST request for updating order or payment status
    if request.method == 'POST':
        # Check if updating the payment status
        if 'payment_status' in request.POST:
            new_payment_status = request.POST.get('payment_status')
            if new_payment_status in ['paid', 'not_paid']:
                order.payment_status = new_payment_status
                order.save()
                return JsonResponse({'success': True, 'payment_status': new_payment_status})

        # Check if updating the order status
        elif 'status' in request.POST:
            new_status = request.POST.get('status')
            if new_status in [choice[0] for choice in Order.STATUS_CHOICES]:
                order.status = new_status
                order.save()
                return JsonResponse({'success': True, 'status': new_status})

        # If an error occurs, return a JSON response with success as False
        return JsonResponse({'success': False, 'error': 'Invalid status value'})

    # Context for GET request to render the order details page
    order_flower_items = [
        {
            'flower': order_flower.flower,
            'quantity': order_flower.quantity,
            'price': order_flower.flower.price,
            'total_price': order_flower.quantity * order_flower.flower.price,
            'image_url': order_flower.flower.flower_img.url if order_flower.flower.flower_img else None
        }
        for order_flower in order.orderflower_set.all()
    ]

    order_decoration_items = [
        {
            'decoration': order_decoration.decoration,
            'quantity': order_decoration.quantity,
            'price': order_decoration.decoration.price,
            'total_price': order_decoration.quantity * order_decoration.decoration.price,
            'image_url': order_decoration.decoration.image.url if order_decoration.decoration.image else None
        }
        for order_decoration in order.orderdecoration_set.all()
    ]

    address = order.client.client_address

    context = {
        'order': order,
        'order_flower_items': order_flower_items,
        'order_decoration_items': order_decoration_items,
        'address': address,
    }
    return render(request, 'admin/admin_order.html', context)


def admin_products_flowers(request):
    # Fetch all flowers
    flowers = Flowers.objects.all()

    # If an edit is requested, get the flower to be edited
    flower_to_edit = None
    if 'edit_id' in request.GET:
        flower_id = request.GET.get('edit_id')
        flower_to_edit = get_object_or_404(Flowers, id=flower_id)

    # Handle form submission for adding or editing flowers
    if request.method == 'POST':
        if 'add_flower' in request.POST or 'edit_flower' in request.POST:
            if flower_to_edit:
                form = FlowersAdminForm(request.POST, request.FILES, instance=flower_to_edit)
            else:
                form = FlowersAdminForm(request.POST, request.FILES)

            if form.is_valid():
                form.save()
                if flower_to_edit:
                    messages.success(request, 'Flower updated successfully!')
                else:
                    messages.success(request, 'Flower added successfully!')
                return redirect('shop:admin_products_flowers')
            else:
                messages.error(request, 'Error processing form. Please check the form fields.')

        # Handle updating all flower prices
        elif 'change_all_prices' in request.POST:
            new_price = request.POST.get('new_price')
            flowers.update(price=new_price)
            messages.success(request, f'All flower prices have been updated to ${new_price}.')
            return redirect('shop:admin_products_flowers')

    # If no form submission, prepare an empty or pre-filled form
    else:
        if flower_to_edit:
            form = FlowersAdminForm(instance=flower_to_edit)
        else:
            form = FlowersAdminForm()

    return render(request, 'admin/view_products/admin_products_flowers.html', {
        'flowers': flowers,
        'form': form,
        'flower_to_edit': flower_to_edit,
    })


@login_required
def admin_products_decorations(request):
    # Fetch all decorations and decoration types
    decorations = Decorations.objects.select_related('type').all()
    decoration_types = DecorationType.objects.all()

    # If an edit is requested, get the decoration or decoration type to be edited
    decoration_to_edit = None
    decoration_type_to_edit = None
    form = None  # Ensure form is always defined

    if 'edit_id' in request.GET:
        decoration_id = request.GET.get('edit_id')
        decoration_to_edit = get_object_or_404(Decorations, id=decoration_id)
    elif 'edit_type_id' in request.GET:
        decoration_type_id = request.GET.get('edit_type_id')
        decoration_type_to_edit = get_object_or_404(DecorationType, id=decoration_type_id)

    # Handle form submission for adding or editing decorations
    if request.method == 'POST':
        if 'add_decoration' in request.POST or 'edit_decoration' in request.POST:
            # Process decoration form
            if decoration_to_edit:
                form = DecorationsAdminForm(request.POST, request.FILES, instance=decoration_to_edit)
            else:
                form = DecorationsAdminForm(request.POST, request.FILES)

            if form.is_valid():
                form.save()
                if decoration_to_edit:
                    messages.success(request, 'Decoration updated successfully!')
                else:
                    messages.success(request, 'Decoration added successfully!')
                return redirect('shop:admin_products_decorations')
            else:
                messages.error(request, 'Error processing form. Please check the form fields.')

        # Handle adding or editing a decoration type
        elif 'add_decoration_type' in request.POST or 'edit_decoration_type' in request.POST:
            decoration_type_name = request.POST.get('decoration_type_name')
            decoration_type_image = request.FILES.get('decoration_type_image')

            if decoration_type_name and decoration_type_image:
                if decoration_type_to_edit:
                    decoration_type_to_edit.decoration_type = decoration_type_name
                    decoration_type_to_edit.product_image = decoration_type_image
                    decoration_type_to_edit.save()
                    messages.success(request, 'Decoration type updated successfully!')
                else:
                    new_type = DecorationType(decoration_type=decoration_type_name, product_image=decoration_type_image)
                    new_type.save()
                    messages.success(request, f'Decoration type "{decoration_type_name}" added successfully!')
                # Refresh the decoration types queryset after adding a new type
                decoration_types = DecorationType.objects.all()
                return redirect('shop:admin_products_decorations')
            else:
                messages.error(request, 'Error adding/editing decoration type. Please fill in all required fields.')

    # If no form submission, prepare an empty or pre-filled form
    if not form:
        if decoration_to_edit:
            form = DecorationsAdminForm(instance=decoration_to_edit)
        else:
            form = DecorationsAdminForm()

    return render(request, 'admin/view_products/admin_products_decorations.html', {
        'decorations': decorations,
        'decoration_types': decoration_types,  # Updated queryset with the latest decoration types
        'form': form,
        'decoration_to_edit': decoration_to_edit,
        'decoration_type_to_edit': decoration_type_to_edit,
    })


@login_required
def delete_decoration_type(request, type_id):
    decoration_type = get_object_or_404(DecorationType, id=type_id)
    decoration_type.delete()
    return redirect('shop:admin_products_decorations')


@login_required
def admin_products_wrapping_paper(request):
    wrapping_papers = WrappingPaper.objects.all()

    if request.method == 'POST':
        edit_id = request.POST.get('edit_id')
        if edit_id:
            wrapping_paper = get_object_or_404(WrappingPaper, id=edit_id)
            form = WrappingPaperAdminForm(request.POST, request.FILES, instance=wrapping_paper)
            if form.is_valid():
                form.save()
                messages.success(request, 'Wrapping Paper updated successfully!')
            else:
                messages.error(request, 'Error updating Wrapping Paper. Please check the form fields.')
        else:
            form = WrappingPaperAdminForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                messages.success(request, 'Wrapping Paper added successfully!')
            else:
                messages.error(request, 'Error adding Wrapping Paper. Please check the form fields.')
        return redirect('shop:admin_products_wrapping_paper')

    edit_id = request.GET.get('edit_id')
    if edit_id:
        wrapping_paper = get_object_or_404(WrappingPaper, id=edit_id)
        form = WrappingPaperAdminForm(instance=wrapping_paper)
    else:
        form = WrappingPaperAdminForm()

    return render(request, 'admin/view_products/admin_products_wrapping_paper.html', {
        'wrapping_papers': wrapping_papers,
        'form': form,
    })


# API endpoint to get wrapping paper details
@login_required
def get_wrapping_paper(request, wrapping_paper_id):
    wrapping_paper = get_object_or_404(WrappingPaper, id=wrapping_paper_id)
    data = {
        'id': wrapping_paper.id,
        'color': wrapping_paper.color,
        'remaining': wrapping_paper.remaining,
    }
    return JsonResponse(data)


@login_required
def get_decoration(request, decoration_id):
    decoration = get_object_or_404(Decorations, id=decoration_id)
    data = {
        'id': decoration.id,
        'color': decoration.color,
        'price': decoration.price,
        'remaining': decoration.remaining,
    }
    return JsonResponse(data)


@login_required
def get_decoration_type(request, type_id):
    decoration_type = get_object_or_404(DecorationType, id=type_id)
    data = {
        'id': decoration_type.id,
        'decoration_type': decoration_type.decoration_type,
        'product_image': decoration_type.product_image.url if decoration_type.product_image else None,
    }
    return JsonResponse(data)

@login_required
def delete_decoration(request, decoration_id):
    decoration = get_object_or_404(Decorations, id=decoration_id)
    decoration.delete()
    messages.success(request, "Decoration deleted successfully!")
    return redirect('shop:admin_products_decorations')
