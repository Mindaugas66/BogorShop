from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'shop'

urlpatterns = [
    path('', views.index, name='index'),
    path('puokste/', views.flower, name='flowers'),
    path('dekoracijos/', views.decoration, name='decorations'),
    path('product/<int:deco_type_id>/', views.product_detail, name='product_detail'),
    path('duk/', views.faq, name='faq'),
    path('Kontaktai/', views.contact_view, name='contact'),
    path('pristatymas/', views.delivery, name='shipping'),
    path('krepselis/', views.cart_view, name='cart'),
    path('krepselis/prideti/', views.add_to_cart, name='add_to_cart'),
    path('krepselis/atnaujinti/', views.update_cart, name='update_cart'),
    path('prekselis/pasalinti/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('krepselis/isvalyti/', views.clear_cart, name='clear_cart'),
    path('atsiskaitymas/', views.checkout_view, name='checkout'),
    path('uzsakymas/<int:order_id>/', views.checkout_complete_view, name='checkout_complete'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
