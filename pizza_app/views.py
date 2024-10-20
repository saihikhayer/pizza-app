from django.shortcuts import render
from django.utils import timezone
from .models import *
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
# Commands for Django management
# python3 manage.py create_groups  
# python3 manage.py runserver 0.0.0.0:8000
# python3 manage.py makemigrations
# python3 manage.py migrate 
# daphne -b 0.0.0.0 -p 8000 pizza_manage.asgi:application

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
    orders_today = DeliveryOrder.objects.filter(order_date__date=timezone.now().date()).prefetch_related('items')
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


def home(request):
    # Get today's date
    to_day = timezone.now().date()
    
    # Filter orders by today's date
    orders_today = Order.objects.filter(order_date__date=to_day)

    context = {
        'orders_today': orders_today,
    }
    return render(request, 'index3.html', context)

def delivery_order(request):
    # Get today's date
    to_day = timezone.now().date()
    
    # Filter orders by today's date
    orders_today = DeliveryOrder.objects.filter(order_date__date=to_day)

    context = {
        'orders_today': orders_today,
    }
    return render(request, 'delivery_order.html', context)

def delivery_order_system(request):
    menu = Menu.objects.all()
    typ = Typ.objects.all()
    return render(request,'delivery.html', {'menus': menu , 'typs':typ})



def order_system(request):
    menu = Menu.objects.all()
    tables = Table.objects.all()
    typ = Typ.objects.all()
    return render(request,'table.html', {'menus': menu , 'tables': tables , 'typs':typ})



def chef_view(request):
    return render(request, 'chef.html')

@csrf_exempt
def submit_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            table_number = data.get('table_number')
            items = data.get('items')
            total_price = float(data.get('total_price'))  # Convert to float here

            table = get_object_or_404(Table, number=table_number)
            order = Order.objects.create(table=table, total_price=total_price)

            order_details = []
            for item in items:
                menu_item = get_object_or_404(Menu, id=item['name'])
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=item['quantity'],
                    comment=item.get('comment', '')
                )
                order_details.append(f"{item['quantity']} x {menu_item } {'(' + item.get('comment', '') + ')' if item.get('comment', '') else ''} - ")

             # Format the detailed message to be sent via WebSocket
            formatted_order = "\n".join(order_details)
            message = (
                f"New order for Table {table_number}:\n"
                f"Items:- \n{formatted_order}\n"
                f"-Total Price: ${total_price:.2f}"  # This will now work correctly
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
            print(e)
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)


@csrf_exempt
def delivery_submit_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            number = data.get('number')
            items = data.get('items')
            total_price = float(data.get('total_price'))  # Convert to float here

            
            order = DeliveryOrder.objects.create(customer_phone=number, total_price=total_price)

            order_details = []
            for item in items:
                menu_item = get_object_or_404(Menu, id=item['name'])
                DeliveryItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=item['quantity'],
                    comment=item.get('comment', '')
                )
                order_details.append(f"{item['quantity']} x {menu_item } {'(' + item.get('comment', '') + ')' if item.get('comment', '') else ''}")

             # Format the detailed message to be sent via WebSocket
            formatted_order = "\n".join(order_details)
            message = (
                f"New order for Table {number}:\n"
                f"Items:\n{formatted_order}\n"
                f"Total Price: ${total_price:.2f}"  # This will now work correctly
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
            print(e)
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)
