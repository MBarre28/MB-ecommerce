from django.urls import path
from .views import (ProductListView, ProductDetailView,
                     CategoryListView, cart_add, cart_detail,
                     checkout, cart_remove, cart_update, order_confirmation, 
                     order_history, login_view, logout_view, register)

urlpatterns = [
    path('', ProductListView.as_view(), name='product_list'),
    path('categories/', CategoryListView.as_view(), name='categories_list'),
    path('category/<slug:category_slug>/', ProductListView.as_view(), name='category_products'),
    path('product/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('cart/add/<int:product_id>/', cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', cart_remove, name='cart_remove'),
    path('cart/update/<int:product_id>/', cart_update, name='cart_update'),
    path('cart/', cart_detail, name='cart_detail'),
    path('checkout/', checkout, name='checkout'),


    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

]
 