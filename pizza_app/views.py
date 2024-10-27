from django.shortcuts import render
from django.utils import timezone
from .models import *
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth import login, logout, authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import F
import json
import logging
# Commands for Django management
# python3 manage.py create_groups
# python3 manage.py runserver 0.0.0.0:8000
# python manage.py makemigrations
# python manage.py migrate
# daphne -b 0.0.0.0 -p 8000 pizza_manage.asgi:application
def login_view(request):
    if request.method == 'POST':
        # Extract username and password from POST data
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Query the database to authenticate the user
        user = authenticate(request, username=username, password=password)

        if user is not None:  # Check if user exists
            # If the user is authenticated, log them in and redirect to the admin page



            login(request, user)
            request.session['username'] = username
            return redirect('home')
        else:
            # If authentication fails, render login page with an error message
            return render(request, 'login.html', {'error': 'Invalid username'})
    else:
        # If the request method is not POST, render the login page
        return render(request, 'login.html')

def fetch_orders(request):
    orders_today = Order.objects.filter(order_date__date=timezone.now().date(),status='pending').prefetch_related('items')
    order_data = []

    for order in orders_today:
        items = [{"name": item.menu_item.name, "quantity": item.quantity , "comment": item.comment , "typ":str(item.menu_item.typ) } for item in order.items.all()]
        order_data.append({
            "id": order.id,
            "table_number": f'Table {order.table.number}' if order.table else "N/A",
            "items": items,
            "order_date": order.order_date.strftime('%Y-%m-%d %H:%M'),
            "status": order.status,
            "total_price": str(order.total_price)  # Convert to string for JSON serialization
        })

    return JsonResponse({"orders": order_data})


def fetch_delivery(request):
    orders_today = DeliveryOrder.objects.filter(order_date__date=timezone.now().date(),status='pending').prefetch_related('items')
    order_data = []

    for order in orders_today:
        items = [{"name": item.menu_item.name, "quantity": item.quantity , "comment": item.comment , "typ":str(item.menu_item.typ) } for item in order.items.all()]
        order_data.append({
            "id": order.id,
            "number": f' {order.customer_phone}' if order.customer_phone else "N/A",
            "items": items,
            "order_date": order.order_date.strftime('%Y-%m-%d %H:%M'),
            "status": order.status,
            "total_price": str(order.total_price)  # Convert to string for JSON serialization
        })

    return JsonResponse({"orders": order_data})


@login_required(login_url='login')
def home(request):
    # Check if the user is a superuser or has the specific 'is_superadmin' attribute
    if request.user.is_superuser:  # or use request.user.is_superadmin if defined
        to_day = timezone.now().date()

        # Filter orders by today's date
        orders_today = Order.objects.filter(order_date__date=to_day)

        context = {
            'orders_today': orders_today,
        }
        return render(request, 'index3.html', context)
    else:
        return redirect(order_system)

@login_required(login_url='login')
def delivery_order(request):
    # Get today's date
    to_day = timezone.now().date()

    # Filter orders by today's date
    orders_today = DeliveryOrder.objects.filter(order_date__date=to_day)

    context = {
        'orders_today': orders_today,
    }
    return render(request, 'delivery_order.html', context)

@login_required(login_url='login')
def delivery_order_system(request):
    menu = Menu.objects.all()
    typ = Typ.objects.all()
    return render(request,'delivery.html', {'menus': menu , 'typs':typ})


@login_required(login_url='login')
def order_system(request):
    menu = Menu.objects.all()
    tables = Table.objects.all()
    typ = Typ.objects.all()
    return render(request,'table.html', {'menus': menu , 'tables': tables , 'typs':typ})



def chef_view(request):
    return render(request, 'chef.html')

logger = logging.getLogger(__name__)

@csrf_exempt  # Use with caution; enable CSRF protection for authenticated clients if possible.
def submit_order(request):
    if request.method == 'POST':
        try:
            # Parse JSON data
            data = json.loads(request.body.decode('utf-8'))
            table_number = data.get('table_number')
            items = data.get('items')
            total_price = float(data.get('total_price'))

            if not (table_number and items and total_price >= 0):
                return JsonResponse({"error": "Missing or invalid data"}, status=400)

            with transaction.atomic():
                # Fetch table and create order
                table = get_object_or_404(Table, number=table_number)
                order = Order.objects.create(table=table, total_price=total_price)

                order_details, item_count = [], 0
                for item in items:
                    menu_item = get_object_or_404(Menu, id=item['id'])
                    quantity = int(item.get('quantity', 1))
                    comment = item.get('comment', '')

                    OrderItem.objects.create(order=order, menu_item=menu_item, quantity=quantity, comment=comment)
                    order_details.append(f"{quantity} x {menu_item.name} ({comment})" if comment else f"{quantity} x {menu_item.name}")
                    item_count += quantity

                # Ensure ServerOrder entry exists for the user
                server_order, created = ServerOrder.objects.get_or_create(user=request.user, defaults={'order': 0})
                server_order.order = F('order') + item_count
                server_order.save()

                # WebSocket message formatting
                formatted_order = "\n".join(order_details)
                message = f"New order for Table {table_number}:\nItems:\n{formatted_order}\nTotal Price: {total_price:.2f} DZD"

                # Optional: Send message via WebSocket

            return JsonResponse({"message": "Order submitted successfully!"})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Table.DoesNotExist:
            return JsonResponse({"error": "Table not found"}, status=404)
        except Menu.DoesNotExist:
            return JsonResponse({"error": "Menu item not found"}, status=404)
        except Exception as e:
            logger.error(f"Error submitting order: {e}")
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)
@csrf_exempt  # Disable CSRF (handle with caution)
def delivery_submit_order(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request
            data = json.loads(request.body.decode('utf-8'))

            # Extract necessary data
            number = data.get('number')  # Table number or customer phone
            items = data.get('items')
            total_price = float(data.get('total_price'))  # Ensure it's a float

            # Create a new delivery order in the database
            order = DeliveryOrder.objects.create(customer_phone=number, total_price=total_price)

            order_details = []
            for item in items:
                # Retrieve menu item using the ID from the request
                menu_item = get_object_or_404(Menu, id=item['id'])  # Make sure 'id' holds the ID

                # Create delivery item associated with the order
                DeliveryItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=item['quantity'],
                    comment=item.get('comment', '')  # Optional comment
                )
                order_details.append(f"{item['quantity']} x {menu_item.name} {'(' + item.get('comment', '') + ')' if item.get('comment', '') else ''}")

            # Format the message to be sent via WebSocket
            formatted_order = "\n".join(order_details)
            message = (
                f"New order for Table {number}:\n"
                f"Items:\n{formatted_order}\n"
                f"Total Price: {total_price:.2f} DZD"  # Replace $ with DZD
            )

            # Notify the chef via WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "orders",  # Channel group for orders
                {
                    'type': 'order_message',  # Custom message type
                    'message': message  # Detailed order message
                }
            )

            return JsonResponse({"message": "Order submitted successfully!"})

        except Exception as e:
            # Log the error and return an appropriate error message
            print(f"Error: {e}")
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Order

def get_delivery_orders(request):
    """Fetch orders that have not been printed."""
    orders = DeliveryOrder.objects.filter(is_printed=False)
    messages = []

    for order in orders:
        order_details = []
        items = order.items.all()  # Get all order items related to this order

        # Process each item in the order
        for item in items:
            order_details.append(f"({item.quantity} .) {item.menu_item} ({item.comment})")

        # Format the order
        formatted_order = "\n".join(order_details)
        message = [order.id,(
            f"New order for {order.customer_phone}:\n"
            f"Items:\n{formatted_order}\n"),
            f" {order.total_price:.2f}"]
        messages.append(message)

    return JsonResponse({"messages": messages}, status=200)

def get_new_orders(request):
    """Fetch orders that have not been printed."""
    orders = Order.objects.filter(is_printed=False)
    messages = []

    for order in orders:
        order_details = []
        items = order.items.all()  # Get all order items related to this order

        # Process each item in the order
        for item in items:
            order_details.append(f"({item.quantity} .) {item.menu_item} ({item.comment})")

        # Format the order
        formatted_order = "\n".join(order_details)
        message = [order.id,(
            f"New order for {order.table}:\n"
            f"Items:\n{formatted_order}\n"),
            f" {order.total_price:.2f}"
            ]
        messages.append(message)

    return JsonResponse({"messages": messages}, status=200)
@csrf_exempt  # Allow POST requests without CSRF tokens (ensure this is safe for your app)
def is_print(request):
    """Mark an order as printed based on its ID."""
    if request.method == 'POST':
        order_id = request.POST.get('order_id')  # Corrected from request.get to request.POST.get

        try:
            # Get the order and mark it as printed
            order = Order.objects.get(id=order_id)
            order.is_printed = True
            order.save()
            return JsonResponse({"message": "Order marked as printed."}, status=200)
        except Order.DoesNotExist:
            return JsonResponse({"error": "Order not found."}, status=404)

    return JsonResponse({"error": "Invalid request method."}, status=400)

@csrf_exempt  # Allow POST requests without CSRF tokens (ensure this is safe for your app)
def is_print_delivery(request):
    """Mark an order as printed based on its ID."""
    if request.method == 'POST':
        order_id = request.POST.get('order_id')  # Corrected from request.get to request.POST.get

        try:
            # Get the order and mark it as printed
            order = DeliveryOrder.objects.get(id=order_id)
            order.is_printed = True
            order.save()
            return JsonResponse({"message": "Order marked as printed."}, status=200)
        except Order.DoesNotExist:
            return JsonResponse({"error": "Order not found."}, status=404)

    return JsonResponse({"error": "Invalid request method."}, status=400)





from django.db.models import Count, Sum
from django.utils import timezone


from django.db.models import Sum, F

from django.shortcuts import render
from .models import OrderItem  # Assuming you have this model for order items


@login_required(login_url='login')
def order_statistics(request):
    if request.user.is_superuser:

        # Existing restaurant statistics
        total_orders = OrderItem.objects.aggregate(total=Sum('quantity'))['total'] or 0

        # Get top dish data for formatting
        top_dish_data = Menu.objects.annotate(order_count=Count('orderitem')).order_by('-order_count').first()
        top_dish = f"{top_dish_data.typ.name} - {top_dish_data.name}" if top_dish_data else 'N/A'

        total_revenue = Order.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0

        # Calculate today's orders
        orders_today = OrderItem.objects.filter(order__order_date__date=timezone.now().date()).aggregate(total=Sum('quantity'))['total'] or 0
        revenue_today = Order.objects.filter(order_date__date=timezone.now().date()).aggregate(Sum('total_price'))['total_price__sum'] or 0

        # Delivery statistics
        total_delivery_orders = DeliveryItem.objects.aggregate(total=Sum('quantity'))['total'] or 0

        # Get top delivery dish data for formatting
        top_delivery_dish_data = Menu.objects.annotate(delivery_count=Count('deliveryitem')).order_by('-delivery_count').first()
        top_delivery_dish = f"{top_delivery_dish_data.typ.name} - {top_delivery_dish_data.name}" if top_delivery_dish_data else 'N/A'

        total_delivery_revenue = DeliveryOrder.objects.aggregate(Sum('total_price'))['total_price__sum'] or 0

        # Calculate today's delivery orders
        delivery_orders_today = DeliveryItem.objects.filter(order__order_date__date=timezone.now().date()).aggregate(total=Sum('quantity'))['total'] or 0
        delivery_revenue_today = DeliveryOrder.objects.filter(order_date__date=timezone.now().date()).aggregate(Sum('total_price'))['total_price__sum'] or 0

        # Get menu labels formatted as 'typ-name' for graphs
        menu_labels = [f"{menu.typ.name} - {menu.name}" for menu in Menu.objects.all()]

        # Count the total quantity of each dish ordered (restaurant)
        menu_data = [OrderItem.objects.filter(menu_item__name=name.split(" - ")[-1]).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0 for name in menu_labels]

        # Count the total quantity of each dish ordered (delivery)
        delivery_data = [DeliveryItem.objects.filter(menu_item__name=name.split(" - ")[-1]).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0 for name in menu_labels]

        # Server order statistics
        server_orders = ServerOrder.objects.all()

        context = {
            'total_orders': total_orders,
            'top_dish': top_dish,
            'total_revenue': total_revenue,
            'orders_today': orders_today,
            'revenue_today': revenue_today,

            'total_delivery_orders': total_delivery_orders,
            'top_delivery_dish': top_delivery_dish,
            'total_delivery_revenue': total_delivery_revenue,
            'delivery_orders_today': delivery_orders_today,
            'delivery_revenue_today': delivery_revenue_today,

            'menu_labels': menu_labels,
            'menu_data': menu_data,
            'delivery_data': delivery_data,

            'server_orders': server_orders  # Pass server order data to the template
        }
        return render(request, 'order_statistics.html', context)
    else:
        return redirect(order_system)

def confirm_order(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        try:
            order = get_object_or_404(Order, id=order_id)
            order.status = 'completed'
            order.save()
            return JsonResponse({'status': 'success', 'message': 'Order marked as completed.'})
        except Order.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Order not found.'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)

def delete_order(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        try:
            order = get_object_or_404(Order, id=order_id)
            order.status = 'canceled'
            order.save()
            return JsonResponse({'status': 'success', 'message': 'Order marked as completed.'})
        except Order.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Order not found.'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)

def confirm_delivery(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        try:
            order = get_object_or_404(DeliveryOrder, id=order_id)
            order.status = 'completed'
            order.save()
            return JsonResponse({'status': 'success', 'message': 'Order marked as completed.'})
        except Order.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Order not found.'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)

def delete_delivery(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        try:
            order = get_object_or_404(DeliveryOrder, id=order_id)
            order.status = 'canceled'
            order.save()
            return JsonResponse({'status': 'success', 'message': 'Order marked as completed.'})
        except Order.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Order not found.'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)





