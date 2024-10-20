from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),  # Home page
    path('delivery_order/', views.delivery_order, name='delivery_order'),
    path('fetch-orders/', views.fetch_orders, name='fetch_orders'), 
    path('fetch-delivery/', views.fetch_delivery, name='fetch_delivery'), 
    path('submit-order/', views.submit_order, name='submit_order'),
    path('delivery-submit-order/', views.delivery_submit_order, name='delivery_submit_order'),
    path('order_system/', views.order_system, name='order_system'),
    path('delivery_order_system/', views.delivery_order_system, name='delivery_order_system'),
    
    path('chef/', views.chef_view, name='chef_page'),
    
    
]
