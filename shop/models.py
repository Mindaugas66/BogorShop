from django.db import models


class Flowers(models.Model):
    color = models.CharField(verbose_name='Color', max_length=50)
    remaining = models.IntegerField(verbose_name='Remaining', default=0)
    price = models.FloatField(verbose_name='Price', default=1.99)
    cost_to_produce = models.FloatField(verbose_name='Cost to produce', default=0.30)
    flower_img = models.ImageField(upload_to='flowers/')
    bouquets_img = models.ImageField(upload_to='bouquets/')

    def __str__(self):
        return f"{self.color} - ${self.price}"


class DecorationType(models.Model):
    decoration_type = models.CharField(verbose_name='Decoration type', max_length=100)
    product_image = models.ImageField(upload_to='decorations/product/')

    def __str__(self):
        return self.decoration_type


class Decorations(models.Model):
    type = models.ForeignKey(DecorationType, verbose_name='Type', on_delete=models.CASCADE)
    color = models.CharField(verbose_name='Color', max_length=50)
    cost_to_buy = models.FloatField(verbose_name='Cost to buy', default=1)
    remaining = models.IntegerField(verbose_name='Remaining', default=0)
    price = models.FloatField(verbose_name='Price')
    image = models.ImageField(upload_to='decorations/')

    def __str__(self):
        return f" ({self.color}) - ${self.price}"


class WrappingPaper(models.Model):
    color = models.CharField(verbose_name='Color', max_length=50)
    remaining = models.FloatField(verbose_name='Remaining', default=0)
    image = models.ImageField(upload_to='wrapping_paper/')

    def __str__(self):
        return f'{self.color}'


class Client(models.Model):
    first_name = models.CharField(verbose_name='Vardas', max_length=30)
    last_name = models.CharField(verbose_name='Pavardė', max_length=40)
    client_phone_number = models.CharField(verbose_name='Telefono numeris', max_length=30)
    email = models.EmailField(verbose_name='El. Paštas', max_length=254, blank=True, null=True)
    client_address = models.ForeignKey('Address', on_delete=models.CASCADE, null=True)
    delivery_option = models.ForeignKey('DeliveryOption', verbose_name='Pristaytas', max_length=50, on_delete=models.CASCADE, null=True)
    ip = models.CharField(max_length=45, null=True, blank=True)  # Add this line for storing IP address

    def __str__(self):
        return f'{self.first_name} {self.last_name} {self.email} {self.client_phone_number} {self.client_address} {self.delivery_option} {self.ip}'


class DeliveryOption(models.Model):
    delivery_option = models.CharField(verbose_name='Pristatymo būdas', max_length=50)
    delivery_price = models.FloatField(verbose_name='Pristatymo kaina', default=0.00)
    delivery_description = models.TextField(verbose_name='Pristatymo aprašymas', blank=True, null=True)

    def __str__(self):
        return f'{self.delivery_option}'


class Address(models.Model):
    city = models.CharField(verbose_name='Miestas', max_length=30)
    zip_code = models.CharField(verbose_name='Pašto kodas', max_length=30)
    street = models.CharField(verbose_name='Gatvė', max_length=30)
    house_number = models.CharField(verbose_name='Namo numeris', max_length=30)

    def __str__(self):
        return f'{self.city} {self.zip_code} {self.street} {self.house_number}'


class Order(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="orders")
    flowers = models.ManyToManyField(Flowers, through='OrderFlower', related_name='orders')
    decorations = models.ManyToManyField(Decorations, through='OrderDecoration', related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    delivery_option = models.ForeignKey(DeliveryOption, on_delete=models.CASCADE, null=True)
    PAYMENT_CHOISES = [
        ('neapmokėtas', 'Neapmokėtas'),
        ('apmokėtas', 'Apmokėtas'),
    ]
    payment_status = models.CharField(max_length=20, choices=PAYMENT_CHOISES, default='neapmokėtas')
    STATUS_CHOICES = [
        ('vykdomas', 'Vykdomas'),
        ('atsauktas', 'Atšauktas'),
        ('issiustas', 'Išsiųstas'),
        ('ivykdytas', 'Ivykdytas'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='vykdomas',
        verbose_name='Order Status'
    )

    def __str__(self):
        return f"Order #{self.id} for {self.client} - Status: {self.get_status_display()}"

    def total_price(self):
        total = 0
        # Add up prices for flowers
        for order_flower in self.orderflower_set.all():
            total += order_flower.flower.price * order_flower.quantity
        # Add up prices for decorations
        for order_decoration in self.orderdecoration_set.all():
            total += order_decoration.decoration.price * order_decoration.quantity
        # Add delivery price if available
        if self.delivery_option:
            total += self.delivery_option.delivery_price
        return total


class OrderFlower(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    flower = models.ForeignKey(Flowers, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.flower.color}"


class OrderDecoration(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    decoration = models.ForeignKey(Decorations, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} x {self.decoration.color}"


class OrderWrappingPaper(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_wrapping_papers")
    wrapping_paper = models.ForeignKey(WrappingPaper, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.wrapping_paper.color} for Order #{self.order.id}"


class Cart(models.Model):
    session_key = models.CharField(max_length=40, null=True, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for session {self.session_key} created on {self.created_at}"

    def total_price(self):
        return sum(item.total_price() for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    flower = models.ForeignKey(Flowers, null=True, blank=True, on_delete=models.CASCADE)
    decoration = models.ForeignKey(Decorations, null=True, blank=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    wrapping_paper = models.ForeignKey('WrappingPaper', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        if self.flower:
            return f"{self.quantity} x {self.flower.color} (Flower)"
        else:
            return f"{self.quantity} x {self.decoration.color} (Decoration)"

    def total_price(self):
        if self.flower:
            return self.flower.price * self.quantity
        elif self.decoration:
            return self.decoration.price * self.quantity
        return 0


class ContactUs(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.email}"

class Visitor(models.Model):
    date = models.DateField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()

    def __str__(self):
        return f"Visitor on {self.date} from {self.ip_address}"
