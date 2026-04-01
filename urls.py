from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import contact_view
from .views import get_live_order_status
urlpatterns = [
    # Home and Index
    path('', views.home, name='home'),
    path('index/', views.index, name='index'),
  path('logout/', views.logout_view, name='logout'),
    # Logout
 

    # -------------------
    # Admin URLs
    # -------------------
    path('login/admin/', views.admin_login, name='admin_login'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path('register/admin/', views.admin_register, name='admin_register'),
    path('register/staff/', views.staff_register, name='staff_register'),
 
    path('admin_manage/', views.admin_manage, name='admin_manage'),
    path('admin_add-staff/', views.add_staff, name='add_staff'),
    path('admin_edit-staff/<int:id>/', views.edit_staff, name='edit_staff'),
    path('admin_delete-staff/<int:id>/', views.delete_staff, name='delete_staff'),
    path('admin_orders/', views.admin_orders, name='admin_orders'),
    path('admin_report/', views.admin_report, name='admin_report'),
    path('admin_report/download/', views.download_report, name='download_report'),
    path('admin_feedback/', views.admin_feedback, name='admin_feedback'),
   path('orders/delete_all/', views.admin_delete_all_orders, name='admin_delete_all_orders'),
    path('admin_logout/', views.admin_logout_view, name='admin_logout'),


    # -------------------
    # Staff URLs
    # -------------------
    path('staff_login/', views.staff_login, name='staff_login'),
    path('staff_dashboard/', views.staff_dashboard, name='staff_dashboard'),
    
       path('staff/logout/', views.staff_logout, name='staff_logout'),

    path('manage_food/', views.manage_food, name='manage_food'),
path('manage_inventory/', views.manage_inventory, name='manage_inventory'),

path('staff_payments/', views.staff_payments, name='staff_payments'),
path('edit_profile/', views.edit_profile,name='edit_profile'),
path('staff/profile/', views.staff_profile, name='staff_profile'),
path('staff/accept-order/', views.accept_order, name='accept_order'),
# urls.py
path('mark-prepared/', views.mark_order_prepared, name='mark_order_prepared'),
path('update_order_status/', views.update_order_status, name='update_order_status'),





    # -------------------
    # Student URLs
    # -------------------
      path('signup/', views.student_signup, name='student_signup'),
    path('login/', views.student_login, name='student_login'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/logout/', views.student_logout, name='student_logout'),
    path('student/menu/', views.view_menu, name='view_menu'),
    path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
       path('remove_from_cart/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('order_status/', views.order_status, name='order_status'),
    path('student/feedback/', views.student_feedback, name='student_feedback'),
     path('profile/', views.student_profile, name='student_profile'),
      path('credit-card/<int:order_id>/', views.credit_card_payment, name='credit_card_payment'),
      # core/urls.py
path('notifications/read/', views.mark_notifications_read, name='mark_notifications_read'),

         
      
    # -------------------
    # Orders and QR
    # -------------------
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),

    path('place_order/', views.place_order, name='place_order'),
    
     path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset-verify/', views.password_reset_verify, name='password_reset_verify'),
     path('wallet/add/', views.add_money_wallet, name='add_money_wallet'),
     path('contact/', contact_view, name='contact'),
     path('cancel_order/<int:order_id>/', views.cancel_order, name='cancel_order'),
       path('place-order/', views.place_order, name='place_order'),
    path('order/<int:order_id>/', views.order_details_by_qr, name='order_detail_by_qr'),
     path('pay-online/<int:order_id>/', views.pay_online, name='pay_online'),
 path('reorder/<int:order_id>/', views.reorder_view, name='reorder'),
path('api/live-order-status/', get_live_order_status, name='get_live_order_status'),

]
