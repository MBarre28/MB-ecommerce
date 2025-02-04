from django.shortcuts import render, redirect, get_object_or_404
from .models import (
    Product,
    Order,
    OrderItem,
    Category,
    Cart,
    CartItem,
    ShippingAddress,
    Coupon,
    Payment,
)
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.db import transaction
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login, logout, authenticate 
from .forms import ShippingAddressForm, CouponForm, PaymentForm


@login_required
# registration form for the user account
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'User created sucessfully.')
            return redirect(request, 'product_list')
        else: 
            messages.error(request, 'Invalid username or password, try again.')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

# login form for validating username and password 




def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data = request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Logged in successfully.')
                next_url = request.GET.get('next', 'product_list')
                return redirect(next_url)
            else:
                messages.error(request, 'User not found, invalid username or password.')
        else:
            messages.error(request, 'User not found, invalid username or password.')
    else:
        form = AuthenticationForm()
        return render(request, 'login.html', {'form': form})

# logout from the e-commerce site 

def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('product_list')
        
            

# Product list view for the list of products
    

class ProductListView(ListView):
    model = Product
    template_name = "list.html"
    context_object_name = "products"

    def get_queryset(self):
        queryset = super().get_queryset().filter(available=True)
        category_slug = self.kwargs.get("category_slug")

        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            queryset = queryset.filter(category=category)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["category_slug"] = self.kwargs.get("category_slug")
        return context


# Adding product to the cart

class CategoryListView(ListView):
    model = Category
    template_name = "categories.html"
    context_object_name = "categories"


def get_or_create_cart(request):
    session_id = request.session.get("cart_id")

    if not request.session.session_key:
        request.session.create()

    if session_id:
        try:
            cart = Cart.objects.get(session_id=session_id)
            return cart
        except Cart.DoesNotExist:
            pass

    cart = Cart.objects.create(session_id=request.session.session_key)
    request.session["cart_id"] = cart.session_id
    return cart



class ProductDetailView(DetailView):
    model = Product
    template_name = "detail.html"
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()

        cart = get_or_create_cart(self.request)
        try:
            cart_item = CartItem.objects.get(cart=cart, product=self.object)
            context["in_cart"] = True
            context["cart_item"] = cart_item
        except CartItem.DoesNotExist:
            context["in_cart"] = False

        return context


def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    cart = get_or_create_cart(request)

    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 1))

        try:
            cart_item = CartItem.objects.get(cart=cart, product=product)

            # Update quantity if product exists
            if product.stock >= cart_item.quantity + quantity:
                cart_item.quantity += quantity
                cart_item.save()
                messages.success(request, "Cart updated successfully.")
            else:
                messages.error(request, "No enough stock available.")

        except CartItem.DoesNotExist:

            # Create a new item if product  doesn't exist in the cart
            if product.stock >= quantity:
                CartItem.objects.create(cart=cart, product=product, quantity=quantity)

                messages.success(request, "Product added to cart successfully.")
            else:
                messages.success(request, "No enough stock available.")

    return redirect("cart_detail")


# update the cart_update function to allow updating the quantity directly
def cart_update(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, cart=cart, product=product)

    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 0))

        if quantity > 0:

            if product.stock >= quantity:
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, "Cart updated successfully.")
            else:
                messages.success(request, "No enough stock available.")
        else:
            cart_item.delete()
            messages.success(request, "Product was removed successfully")

    return redirect("cart_detail")


def cart_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, cart=cart, product=product)
    cart_item.delete()
    messages.success(request, "Product was removed successfully")
    return redirect("cart_detail")


def cart_detail(request):
    cart = get_or_create_cart(request)
    cart_items = CartItem.objects.filter(cart=cart).select_related("product")

    # fixed the cart_total for the cart items

    cart_total = (
        CartItem.objects.filter(cart=cart).aggregate(
            total=Sum(F("product__price") * F("quantity"))
        )["total"]
        or 0
    )

    return render(
        request,
        "cart_detail.html",
        {"cart_items": cart_items, "cart_total": cart_total},
    )


@login_required
def checkout(request):

    # Get the cart items from the cart and creating the order
    try:
        cart = Cart.objects.prefetch_related('items').get(
        session_id=request.session.session_key)
        cart_items = cart.items.all()
        if not cart_items.exists():
            messages.error(request, "Cart has no items, please select a cart")
            return redirect("cart_detail")
        
    except Cart.DoesNotExist:
        messages.error(request, "Cart has no items, please select a cart")
        return redirect("cart_detail")

    # creating the shipping and payment forms
    shipping_form = ShippingAddressForm(request.POST or None)
    payment_form = PaymentForm(request.POST or None)
    coupon_form = CouponForm(request.POST or None)

    if request.method == "POST":

        if (
            shipping_form.is_valid()
            and payment_form.is_valid()
            and (not coupon_form.data or coupon_form.is_valid())
        ):

            with transaction.atomic():
                shipping_address = shipping_form.save(commit=False)
                shipping_address.user = request.user
                shipping_address.save()

                total_price = (
                    CartItem.objects.filter(cart=cart).aggregate(
                        total=Sum(F("product__price") * F("quantity"))
                    )["total"] or 0
                )

                coupon = None
                if coupon_form.is_valid():
                    coupon_form = coupon_form.clear_data["coupon"]
                if coupon.is_valid():
                    total_price *= 1 - (coupon.discount_perentage / 100)
                    coupon.current_usage += 1
                    coupon.save()

                order = Order.objects.create(
                    user=request.user,
                    total_price=total_price,
                )

                # creating the order

                order_items = []
                for cart_item in cart_items:
                    order_item = OrderItem.objects.create(
                        order = order,
                        product = cart_item.product,
                        quantity = cart_item.quantity,
                    )
                    product = cart_item.product
                    product.stock -= cart_item.quantity
                    product.save()
                    order_items.append(order_item)

                payment_form = Payment.objects.create(
                    user=request.user,
                    order=order,
                    payment_method=payment_form.cleaned_data["payment_method"],
                    amount=total_price,
                    payment_status="pending",
                )

                cart_items.delete()
                cart.delete()

                messages.sucess(request, "your order has been placed successfully")
                return redirect("order_confirmation", order_id=order.id)
    

    

    context = {
        'cart_items': cart_items,
        'shipping_form': shipping_form,
        'coupon_form': coupon_form,
        'total_price': CartItem.objects.filter(cart=cart).aggregate(
        total=Sum(F("product__price") * F("quantity"))
        )["total"] or 0
    }

    return render(request, 'checkout.html', context)


@login_required
# This view is use to display the order confirmation page.
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "order_confirmation.html", {"order": order})


# This view is use to display the order history page.
@login_required
def order_history(request, order_id):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "order_history.html", {"orders": orders})
