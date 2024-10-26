from django import forms
from .models import Flowers, Client, Address, ContactUs


class FlowerSelectionForm(forms.Form):
    """A form for selecting flowers and their quantities."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically add fields for each available flower
        flowers = Flowers.objects.all()
        for flower in flowers:
            self.fields[f'flower_{flower.id}_quantity'] = forms.IntegerField(
                label=f'Quantity for {flower.color}',
                min_value=0,
                initial=0,
                required=False
            )
            self.fields[f'flower_{flower.id}_id'] = forms.CharField(
                initial=flower.id,
                widget=forms.HiddenInput()
            )


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['city', 'zip_code', 'street', 'house_number']
        widgets = {
            'city': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Miestas'}),
            'street': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Gatvė'}),
            'house_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Namo Numeris'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Pašto Kodas'}),
        }


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['first_name', 'last_name', 'client_phone_number', 'email', 'delivery_option']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Vardas'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Pavardė'}),
            'client_phone_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Telefono Numeris'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'El. paštas'}),
            'delivery_option': forms.Select(choices=[
                ('lietuvos_pastas', 'Lietuvos paštas'),
                ('siuntos_autobusai', 'Siuntos Autobusai')
            ], attrs={'class': 'form-select'}),
        }

class ContactUsForm(forms.ModelForm):
    class Meta:
        model = ContactUs
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Jūsų vardas'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Jūsų el. paštas'
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Jūsų žinutė',
                'rows': 5
            }),
        }


class CustomLoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg', 'placeholder': 'Password'})
    )