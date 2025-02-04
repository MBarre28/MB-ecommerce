from django.contrib import admin
from .models import Product, Order, OrderItem, Category, Cart, CartItem, ShippingAddress, Payment, Coupon 

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(ShippingAddress)
admin.site.register(Payment)
admin.site.register(Coupon)

