from django.db import models
from django.contrib.auth.models import User

class Typ(models.Model):
    name = models.CharField(max_length=255)
    def __str__(self):
        return f"{self.name}"

class Menu(models.Model):
    name = models.CharField(max_length=255)
    typ = models.ForeignKey(Typ  ,on_delete=models.SET_NULL, null=True, blank=True )
    price = models.DecimalField(max_digits=8, decimal_places=0)

    def __str__(self):
        return f"{self.name} ({self.typ})  {self.price} da "


class Table(models.Model):
    number = models.IntegerField(unique=True)
    is_occupied = models.BooleanField(default=False)

    def __str__(self):
        return f"Table {self.number}"


class OrderItem(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='items')  # Link to Order
    menu_item = models.ForeignKey(Menu, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    comment = models.CharField(max_length=20,default='')

    def __str__(self):
        return f"({self.quantity} .) {self.menu_item.name}"

    def get_total_price(self):
        return self.menu_item.price * self.quantity


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),

    ]

    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_printed = models.BooleanField(default=False)

    def __str__(self):
        return f"Order {self.id} - Status: {self.status}"

    def calculate_total(self):
        total = sum(item.get_total_price() for item in self.items.all())
        self.total_price = total
        self.save()
class DeliveryOrder(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]

    customer_phone = models.CharField(max_length=20)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_printed = models.BooleanField(default=False)


    def __str__(self):
        return f"Order {self.id} - Status: {self.status}"

    def calculate_total(self):
        total = sum(item.get_total_price() for item in self.items.all())
        self.total_price = total
        self.save()


class DeliveryItem(models.Model):
    order = models.ForeignKey(DeliveryOrder, on_delete=models.CASCADE, related_name='items')  # Link to Order
    menu_item = models.ForeignKey(Menu, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    comment = models.CharField(max_length=20,default='')

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name}"

    def get_total_price(self):
        return self.menu_item.price * self.quantity




class ServerOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE , related_name='user', unique=True)
    order = models.IntegerField(default=0)
    def __str__(self):
        return f"{self.user} x {self.order}"

