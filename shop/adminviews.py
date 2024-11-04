from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Flowers, Decorations, DecorationType, OrderFlower, OrderDecoration, Order, WrappingPaper, Visitor
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import CustomLoginForm, FlowersAdminForm, DecorationsAdminForm, WrappingPaperAdminForm
from django.contrib.auth import authenticate, login
from django.utils import timezone
from django.db.models import Count, Sum, F
from django.contrib.sessions.models import Session

def admin_login(request):
    if request.method == 'POST':
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
    # Previous counts and data
    flower_count = Flowers.objects.count()
    decoration_count = Decorations.objects.count()
    order_count = Order.objects.count()
    in_progress_count = Order.objects.filter(status='vykdomas').count()
    out_for_delivery_count = Order.objects.filter(status='issiustas').count()
    complete_count = Order.objects.filter(status='ivykdytas').count()

    now = timezone.now()
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_month = now.replace(day=1)
    start_of_year = now.replace(month=1, day=1)
    visits_last_24_hours = Visitor.objects.filter(date__gte=now - timezone.timedelta(days=1)).count()
    visits_this_month = Visitor.objects.filter(date__gte=start_of_month).count()
    total_visits_this_year = Visitor.objects.filter(date__gte=start_of_year).count()

    # Get the current date to filter orders for the current month
    today = timezone.now()
    start_of_month = today.replace(day=1)

    # Calculate Total Sales Revenue for all time using total_price method for each order
    total_sales_revenue = sum(order.total_price() for order in Order.objects.all())

    # Calculate Total Sales Revenue This Month
    total_sales_revenue_this_month = sum(
        order.total_price() for order in Order.objects.filter(created_at__gte=start_of_month)
    )

    # Calculate Total Cost for producing/sourcing flowers and decorations (all time)
    flower_cost = OrderFlower.objects.aggregate(total=Sum(F('quantity') * F('flower__cost_to_produce')))['total'] or 0.0
    decoration_cost = OrderDecoration.objects.aggregate(total=Sum(F('quantity') * F('decoration__cost_to_buy')))['total'] or 0.0
    total_cost = flower_cost + decoration_cost

    # Calculate Total Cost This Month (only orders from this month)
    flower_cost_this_month = OrderFlower.objects.filter(order__created_at__gte=start_of_month).aggregate(
        total=Sum(F('quantity') * F('flower__cost_to_produce'))
    )['total'] or 0.0
    decoration_cost_this_month = OrderDecoration.objects.filter(order__created_at__gte=start_of_month).aggregate(
        total=Sum(F('quantity') * F('decoration__cost_to_buy'))
    )['total'] or 0.0
    total_cost_this_month = flower_cost_this_month + decoration_cost_this_month

    # Calculate Total Profit
    total_profit = total_sales_revenue - total_cost
    total_profit_this_month = total_sales_revenue_this_month - total_cost_this_month

    # Visitor data for chart
    past_month = today - timezone.timedelta(days=30)
    visitor_data = (
        Visitor.objects.filter(date__gte=past_month)
        .extra(select={'day': 'date(date)'})
        .values('day')
        .annotate(visitor_count=Count('id'))
        .order_by('day')
    )
    visitor_dates = [entry['day'] for entry in visitor_data]
    visitor_counts = [entry['visitor_count'] for entry in visitor_data]

    # Count active users (last 5 minutes)
    active_user_count = count_active_users(timeout_minutes=5)

    # Context for the template
    context = {
        'flower_count': flower_count,
        'visits_last_24_hours': visits_last_24_hours,
        'visits_this_month': visits_this_month,
        'total_visits_this_year': total_visits_this_year,
        'decoration_count': decoration_count,
        'order_count': order_count,
        'total_sales_revenue': total_sales_revenue,
        'total_profit': total_profit,
        'total_sales_revenue_this_month': total_sales_revenue_this_month,
        'total_profit_this_month': total_profit_this_month,
        'visitor_dates': visitor_dates,
        'visitor_counts': visitor_counts,
        'active_user_count': active_user_count,
        'in_progress_count': in_progress_count,
        'out_for_delivery_count': out_for_delivery_count,
        'complete_count': complete_count,
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


def count_active_users(timeout_minutes=3):
    # Calculate the threshold time for activity
    threshold = timezone.now() - timezone.timedelta(minutes=timeout_minutes)

    # Query sessions and count active ones
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    active_user_count = 0

    for session in active_sessions:
        # Get session data
        data = session.get_decoded()
        last_activity = data.get('last_activity')
        if last_activity:
            last_activity = timezone.datetime.fromisoformat(last_activity)
            if last_activity >= threshold:
                active_user_count += 1

    return active_user_count

def admin_inventory(request):
    # Get all flowers and calculate the remaining percentage for each
    flowers = Flowers.objects.all()
    flower_inventory_data = []

    for flower in flowers:
        remaining_percentage = min(100, max(0, (flower.remaining / 100) * 100))
        color = 'bg-green-500' if remaining_percentage >= 60 else 'bg-yellow-500' if remaining_percentage >= 20 else 'bg-red-500'

        flower_inventory_data.append({
            'name': flower.color,
            'remaining': flower.remaining,
            'remaining_percentage': remaining_percentage,
            'color': color,
            'image_url': flower.flower_img.url,
        })

    # Get all decorations and calculate the remaining percentage for each
    decorations = Decorations.objects.all()
    decoration_inventory_data = []

    for decoration in decorations:
        remaining_percentage = min(100, max(0, (decoration.remaining / 20) * 100))
        color = 'bg-green-500' if remaining_percentage >= 60 else 'bg-yellow-500' if remaining_percentage >= 20 else 'bg-red-500'

        decoration_inventory_data.append({
            'name': decoration.color,
            'remaining': decoration.remaining,
            'remaining_percentage': remaining_percentage,
            'color': color,
            'image_url': decoration.image.url if decoration.image else None,
        })

    # Get all wrapping papers and calculate the remaining percentage for each
    wrapping_papers = WrappingPaper.objects.all()
    wrapping_paper_inventory_data = []

    for paper in wrapping_papers:
        remaining_percentage = min(100, max(0, (paper.remaining / 50) * 100))  # Max count for 100% is 50
        color = 'bg-green-500' if remaining_percentage >= 60 else 'bg-yellow-500' if remaining_percentage >= 20 else 'bg-red-500'

        wrapping_paper_inventory_data.append({
            'name': paper.color,
            'remaining': paper.remaining,
            'remaining_percentage': remaining_percentage,
            'color': color,
            'image_url': paper.image.url if paper.image else None,
        })
    context = {
        'flower_inventory_data': flower_inventory_data,
        'decoration_inventory_data': decoration_inventory_data,
        'wrapping_paper_inventory_data': wrapping_paper_inventory_data,
    }
    return render(request, 'admin/inventory.html', context)