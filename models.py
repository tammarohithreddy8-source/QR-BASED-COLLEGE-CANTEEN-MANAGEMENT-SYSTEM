from django.db import models
from django.contrib.auth.models import User

class Staff(models.Model):
    username = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    password = models.CharField(max_length=128)
    profile = models.ImageField(upload_to='profiles/', null=True, blank=True)
    def __str__(self):
        return self.name

from django.contrib.auth.models import AbstractUser
from decimal import Decimal
class Student(models.Model):
    name = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128, default='12345')
    contact = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    join_date = models.DateField(auto_now_add=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return self.name
class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    available = models.BooleanField(default=True)
    quantity_available = models.PositiveIntegerField(default=0)  # Quantity provided by staff
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='images/', null=True, blank=True)

    def __str__(self):
        return self.name


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.item.name} for {self.user.username}"

from django.utils import timezone  
from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

from django.utils import timezone
from django.utils.timezone import localdate
from django.contrib.auth.models import User

from datetime import timedelta
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),      # when staff accepts
        ('preparing', 'Preparing'),      # being prepared
        ('prepared', 'Prepared'),        # ready to collect
        ('delivered', 'Delivered'),      # collected by student
        ('cancelled', 'Cancelled'),
    ]
    PAYMENT_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('UPI', 'UPI'),
        ('CARD', 'Card'),
        ('NETBANKING', 'Net Banking'),
    ]
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    staff = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, blank=True)
    order_date = models.DateTimeField(default=timezone.now)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    qr_code = models.ImageField(upload_to='qr_codes/', null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    prep_time = models.PositiveIntegerField(null=True, blank=True)  # in minutes
    prep_start_time = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"
    def check_and_update_status(self):
        if self.status == 'preparing' and self.prep_start_time and self.prep_time:
            elapsed = (timezone.now() - self.prep_start_time).total_seconds() / 60
            if elapsed >= self.prep_time:
                self.status = 'prepared'
                self.save()
                return True
        return False
    # models.py
    def get_remaining_prep_time(self):
        if self.status == 'preparing' and self.prep_start_time and self.prep_time:
            elapsed = (timezone.now() - self.prep_start_time).total_seconds() / 60
            remaining = max(0, self.prep_time - int(elapsed))
            return remaining
        return 0
    @property
    def calculated_total_price(self):
        return sum(item.item.price * item.quantity for item in self.items.all())

   


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    created_at = models.DateTimeField(default=now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username} at {self.created_at}"



class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.quantity} x {self.item.name}"


class Feedback(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    comments = models.TextField()
    rating = models.IntegerField(default=0)  # Add this line
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback by {self.student.username} on {self.created_at.strftime('%Y-%m-%d')}"
    
class Notification(models.Model):
    STATUS_CHOICES = [
        ('accepted', 'Order Accepted'),
        ('prepared', 'Order Prepared'),
        ('delivered', 'Order Delivered'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='accepted')  # <-- default added
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.status}"
