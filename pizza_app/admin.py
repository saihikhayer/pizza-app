from django.contrib import admin
from .models import *
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Menu)
admin.site.register(Table)
admin.site.register(Typ)
admin.site.register(DeliveryOrder)
admin.site.register(ServerOrder)


# Register your models here.
