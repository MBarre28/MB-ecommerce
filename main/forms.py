from django import forms
from .models import ShippingAddress, Payment, Coupon

class ShippingAddressForm(forms.ModelForm):
    is_default = forms.BooleanField(
        required=False, 
        label= 'Make Shipping Address Default',

        
        )
    
    class Meta:
        model = ShippingAddress
        fields = [
            'full_name',
            'address',
            'city',
            'zip_code',
            'country',
            'state',
            'phone_number',
            'is_default',

        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),

        }


class PaymentForm(forms.Form):
    payment_method =  forms.ChoiceField(
    choices=Payment.PAYMENT_METHODS,
    widget = forms.Select ( attrs= {'class': 'form-control'}),
    )

class CouponForm(forms.Form):
    coupon_code = forms.CharField(
        max_length= 20,
        widget =  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Coupon Code'}),
        label = 'Coupon Code',
        required = False, 
    )


    def clean_coupon_code(self):
        code = self.cleaned_data.get('coupon_code')
        if not code:
            return None
        
        try:
            coupon = Coupon.objects.get(code = code)
            if not coupon.is_valid():
                raise forms.ValidationError('Coupon has expired or reached its usage limit, please enter a valid coupon code.')
        
        except Coupon.DoesNotExist:
            raise forms.ValidationError('Coupon does not exist, please enter a valid coupon code.')