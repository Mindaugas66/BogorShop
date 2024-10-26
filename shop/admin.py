from django.contrib import admin

from .models import Flowers, Decorations, Materials, Order, Client, DecorationType, DeliveryOption, OrderDecoration, OrderFlower, Cart, CartItem, ContactUs


class FlowersAdmin(admin.ModelAdmin):
    list_display = ('color', 'remaining', 'price', 'flower_img', 'bouquets_img')


class DecorationAdmin(admin.ModelAdmin):
    list_display = ('type', 'color', 'remaining', 'price', 'image')


class DecorationTypeAdmin(admin.ModelAdmin):
    list_display = ('decoration_type',)


class MaterialsAdmin(admin.ModelAdmin):
    list_display = ('name', 'remaining', 'price')


class ClientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'client_phone_number', 'client_address')

    def get_total(self, obj):
        return obj.total()

    get_total.short_description = 'Total'


class DeliveryOptionAdmin(admin.ModelAdmin):
    list_display = ('delivery_option', 'delivery_price')

class ContactUsAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'message')


admin.site.register(Flowers, FlowersAdmin)
admin.site.register(Decorations, DecorationAdmin)
admin.site.register(Materials, MaterialsAdmin)
admin.site.register(Order)
admin.site.register(OrderFlower)
admin.site.register(OrderDecoration)
admin.site.register(Client, ClientAdmin)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(DecorationType, DecorationTypeAdmin)
admin.site.register(DeliveryOption, DeliveryOptionAdmin)
admin.site.register(ContactUs, ContactUsAdmin)
