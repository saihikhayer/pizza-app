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
    path('get_new_orders/', views.get_new_orders, name='get_new_orders'),
    path('get_delivery_orders/', views.get_delivery_orders, name='get_delivery_orders'),
    path('is_print/', views.is_print, name='is_print'),
    path('is_print_delivery/', views.is_print_delivery, name='is_print_delivery'),
    path('order-statistics/', views.order_statistics, name='order_statistics'),
    path('confirm_order/', views.confirm_order, name='confirm_order'),
    path('delete_order/', views.delete_order, name='delete_order'),
    path('confirm_delivery/', views.confirm_delivery, name='confirm_delivery'),
    path('delete_delivery/', views.delete_delivery, name='delete_delivery'),
    path('login/', views.login_view, name='login'),



]
