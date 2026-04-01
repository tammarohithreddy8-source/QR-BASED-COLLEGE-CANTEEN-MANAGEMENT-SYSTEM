# --- Imports and Setup ---
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.hashers import make_password, check_password
from django.http import HttpResponse
from django.core.files import File
import openpyxl
import qrcode
from io import BytesIO
import base64
import json
from django.db.models import Sum, F, FloatField
from django.utils.timezone import now
from datetime import timedelta
import random
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Staff, Order, Item, CartItem, OrderItem, Feedback, Student
from .forms import QRUploadForm, UploadQRCodeForm, PasswordResetRequestForm, PasswordResetVerifyForm
from .decorators import staff_required
# --- Helper Function ---
# Check if a user is in a specific group
def in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()
# --- General Views ---
# Render the home page
def logout_view(request):
    logout(request)
    return redirect('home')
def home(request):
    return render(request, 'home.html')
# Render the index (landing) page
def index(request):
    return render(request, 'index.html')
# --- Authentication / Logout ---
# Logout a logged-in user
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('home')
# --- Admin Views ---
def admin_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            messages.success(request, 'Admin login successful.', extra_tags='admin success')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid credentials.', extra_tags='admin error')
    return render(request, 'admin_login.html')
# =====================================================================
# ADD THESE TWO VIEWS TO YOUR views.py
# Paste them right after your existing admin_login view (around line 58)
# =====================================================================
def admin_register(request):
    """
    Allows a new admin (superuser) to register.
    After registration, redirects to admin_login.
    """
    if request.method == 'POST':
        username  = request.POST.get('username', '').strip()
        email     = request.POST.get('email', '').strip()
        password  = request.POST.get('password', '')
        confirm   = request.POST.get('confirm_password', '')
 
        # --- Validations ---
        if not username or not email or not password:
            messages.error(request, "All fields are required.")
            return render(request, 'admin_register.html')
 
        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'admin_register.html')
 
        if not email.endswith('@gmail.com'):
            messages.error(request, "Email must be a Gmail address (@gmail.com).")
            return render(request, 'admin_register.html')
 
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, 'admin_register.html')
 
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'admin_register.html')
 
        # --- Create superuser / admin ---
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        messages.success(request, f"Admin account '{username}' created successfully! Please log in.")
        return redirect('admin_login')
 
    return render(request, 'admin_register.html')
 
 
def staff_register(request):
    """
    Allows a new canteen staff member to self-register.
    After registration, redirects to staff_login.
    """
    if request.method == 'POST':
        username  = request.POST.get('username', '').strip()
        name      = request.POST.get('name', '').strip()
        email     = request.POST.get('email', '').strip()
        password  = request.POST.get('password', '')
        confirm   = request.POST.get('confirm_password', '')
        profile   = request.FILES.get('profile')
 
        # --- Validations ---
        if not username or not name or not email or not password:
            messages.error(request, "All fields are required.")
            return render(request, 'staff_register.html')
 
        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'staff_register.html')
 
        if not email.endswith('@gmail.com'):
            messages.error(request, "Email must be a Gmail address (@gmail.com).")
            return render(request, 'staff_register.html')
 
        if Staff.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, 'staff_register.html')
 
        if Staff.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'staff_register.html')
 
        # --- Create staff record ---
        staff = Staff(
            username=username,
            name=name,
            email=email,
            password=make_password(password),
        )
        if profile:
            staff.profile = profile
        staff.save()
 
        # --- Send welcome email (best-effort) ---
        try:
            send_mail(
                subject='Welcome to eCanteen – Your Staff Account',
                message=(
                    f"Hi {name},\n\n"
                    f"Your staff account has been created.\n\n"
                    f"Username : {username}\n"
                    f"Password : {password}\n\n"
                    f"Please log in and change your password immediately."
                ),
                from_email='destfinder9564@gmail.com',
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception:
            pass  # email failure should not block registration
 
        messages.success(request, "Staff account created successfully! Please log in.")
        return redirect('staff_login')
 
    return render(request, 'staff_register.html')

def admin_register(request):
    """
    Allows a new admin (superuser) to register.
    After registration, redirects to admin_login.
    """
    if request.method == 'POST':
        username  = request.POST.get('username', '').strip()
        email     = request.POST.get('email', '').strip()
        password  = request.POST.get('password', '')
        confirm   = request.POST.get('confirm_password', '')

        # --- Validations ---
        if not username or not email or not password:
            messages.error(request, "All fields are required.")
            return render(request, 'admin_register.html')

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'admin_register.html')

        if not email.endswith('@gmail.com'):
            messages.error(request, "Email must be a Gmail address (@gmail.com).")
            return render(request, 'admin_register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, 'admin_register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'admin_register.html')

        # --- Create superuser / admin ---
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        messages.success(request, f"Admin account '{username}' created successfully! Please log in.")
        return redirect('admin_login')

    return render(request, 'admin_register.html')


def staff_register(request):
    """
    Allows a new canteen staff member to self-register.
    After registration, redirects to staff_login.
    """
    if request.method == 'POST':
        username  = request.POST.get('username', '').strip()
        name      = request.POST.get('name', '').strip()
        email     = request.POST.get('email', '').strip()
        password  = request.POST.get('password', '')
        confirm   = request.POST.get('confirm_password', '')
        profile   = request.FILES.get('profile')

        # --- Validations ---
        if not username or not name or not email or not password:
            messages.error(request, "All fields are required.")
            return render(request, 'staff_register.html')

        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'staff_register.html')

        if not email.endswith('@gmail.com'):
            messages.error(request, "Email must be a Gmail address (@gmail.com).")
            return render(request, 'staff_register.html')

        if Staff.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, 'staff_register.html')

        if Staff.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'staff_register.html')

        # --- Create staff record ---
        staff = Staff(
            username=username,
            name=name,
            email=email,
            password=make_password(password),
        )
        if profile:
            staff.profile = profile
        staff.save()

        # --- Send welcome email (best-effort) ---
        try:
            send_mail(
                subject='Welcome to eCanteen – Your Staff Account',
                message=(
                    f"Hi {name},\n\n"
                    f"Your staff account has been created.\n\n"
                    f"Username : {username}\n"
                    f"Password : {password}\n\n"
                    f"Please log in and change your password immediately."
                ),
                from_email='destfinder9564@gmail.com',
                recipient_list=[email],
                fail_silently=True,
            )
        except Exception:
            pass  # email failure should not block registration

        messages.success(request, "Staff account created successfully! Please log in.")
        return redirect('staff_login')

    return render(request, 'staff_register.html')

def admin_logout_view(request):
    logout(request)
    messages.success(request, 'Admin logged out successfully.', extra_tags='admin success')
    return redirect('admin_login')
from collections import defaultdict
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from .models import Student, Staff, Order, OrderItem
from django.db.models import Sum, F, FloatField
@staff_member_required
def admin_dashboard(request):
    user = request.user
    today = timezone.now().date()

    # Student and staff counts
    student_count = Student.objects.count()
    staff_count = Staff.objects.count()

    # Today's revenue
    today_revenue = Order.objects.filter(created_at__date=today).aggregate(
        total=Sum('total_price')
    )['total'] or 0

    # Last 2 days revenue (chart)
    days = [today - timedelta(days=i) for i in range(1, -1, -1)]
    revenue_values = []
    for day in days:
        day_orders = Order.objects.filter(created_at__date=day)
        day_total = OrderItem.objects.filter(order__in=day_orders).aggregate(
            total=Sum(F('item__price') * F('quantity'), output_field=FloatField())
        )['total'] or 0
        revenue_values.append(day_total)

    # Recent activities
   
    # Weekly orders per day (Monday to Sunday)
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)
    
    weekly_orders = Order.objects.filter(order_date__date__range=(start_of_week, end_of_week))

    # Count per day (0=Monday, ..., 6=Sunday)
    daily_counts = defaultdict(int)
    for order in weekly_orders:
        weekday = order.order_date.weekday()
        daily_counts[weekday] += 1

    # Ensure order from Mon (0) to Sun (6)
    weekly_order_count = [daily_counts.get(i, 0) for i in range(7)]

    # Weekly revenue
    weekly_revenue = OrderItem.objects.filter(order__in=weekly_orders).aggregate(
        total=Sum(F('item__price') * F('quantity'), output_field=FloatField())
    )['total'] or 0

    context = {
        'student_count': student_count,
        'staff_count': staff_count,
        'today_order_count': Order.objects.filter(created_at__date=today).count(),
        'today_revenue': today_revenue,
        'chart_labels': [day.strftime('%b %d') for day in days],
        'chart_data': revenue_values,
       
        'weekly_order_count': weekly_order_count,  # Now it's a list!
        'weekly_revenue': weekly_revenue,
        'user': user,
    }

    return render(request, 'admin_dashboard.html', context)


# Manage staff list
@staff_member_required
def admin_manage(request):
    staff_list = Staff.objects.all()
    return render(request, 'admin_manage.html', {'staff_list': staff_list})
# Add a new staff member
@staff_member_required
def add_staff(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        profile = request.FILES.get('profile')
        # Validate Gmail email
        if not email.endswith('@gmail.com'):
            messages.error(request, "Email must end with @gmail.com.")
            return redirect('admin_manage')
        # Check for existing username
        if Staff.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('admin_manage')
        if not profile:
            messages.error(request, "Profile image is required.")
            return redirect('admin_manage')
        # Save staff with hashed password
        staff = Staff.objects.create(
            username=username,
            name=name,
            email=email,
            password=make_password(password),
            profile=profile
        )
        # Send credentials via email
        try:
            send_mail(
                subject='Your eCanteen Staff Account Details',
                message=(
                    f"Hi {name},\n\n"
                    f"You have been added as a staff member in eCanteen.\n\n"
                    f"Login credentials:\n"
                    f"Username: {username}\n"
                    f"Password: {password}\n\n"
                    f"Please log in and change your password as soon as possible."
                ),
                from_email='ecanteen@yourdomain.com',
                recipient_list=[email],
                fail_silently=False
            )
        except Exception as e:
            messages.warning(request, f"Staff created but email not sent. Error: {str(e)}")
        else:
            messages.success(request, "Staff added successfully and credentials sent to email.")
        return redirect('admin_manage')
    return redirect('admin_manage')
def edit_profile(request):
    # your logic here
    return render(request, 'edit_profile.html')
# Edit existing staff
@staff_member_required
def edit_staff(request, id):
    staff = get_object_or_404(Staff, id=id)
    if request.method == 'POST':
        staff.username = request.POST['username']
        staff.name = request.POST['name']
        staff.email = request.POST['email']
        staff.role = request.POST['role']
        password = request.POST.get('password')
        if password:
            staff.password = make_password(password)
        staff.save()
        messages.success(request, "Staff updated successfully.")
        return redirect('admin_manage')
    return render(request, 'edit_staff.html', {'staff': staff})
# Delete a staff member
@staff_member_required
def delete_staff(request, id):
    staff = get_object_or_404(Staff, id=id)
    staff.delete()
    messages.success(request, "Staff deleted.")
    return redirect('admin_manage')
# View all orders (admin)
@staff_member_required
def admin_orders(request):
    orders = Order.objects.select_related('user').prefetch_related('items').all().order_by('-created_at')
    return render(request, 'admin_orders.html', {'orders': orders})
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
# View order report (admin)
@staff_member_required
def admin_report(request):
    orders = Order.objects.select_related('user').prefetch_related('items').all().order_by('-created_at')
    # Filter by date (YYYY-MM-DD)
    date_filter = request.GET.get('date')
    if date_filter:
        date_obj = parse_date(date_filter)
        if date_obj:
            orders = orders.filter(created_at__date=date_obj)

    # Pagination: 10 orders per page
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj,
        'date_filter': date_filter,
    }
    return render(request, 'admin_report.html', context)
    


# Download order report as Excel file
@staff_member_required
def download_report(request):
    orders = Order.objects.select_related('user').all()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Orders Report"

    headers = ['Order ID', 'Student Username', 'Total Price', 'Status', 'Created At']
    ws.append(headers)

    for order in orders:
        ws.append([
            order.id,
            order.user.username,
            float(order.total_price),
            order.status,
            order.created_at.strftime("%Y-%m-%d %H:%M"),
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=orders_report.xlsx'
    wb.save(response)
    return response


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Avg
from django.shortcuts import render
from .models import Feedback
from datetime import datetime
@staff_member_required
def admin_feedback(request):
    feedback_list = Feedback.objects.select_related('student').all().order_by('-created_at')

    # --- Date Filtering ---
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            feedback_list = feedback_list.filter(created_at__date__gte=start)
        except ValueError:
            pass

    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            feedback_list = feedback_list.filter(created_at__date__lte=end)
        except ValueError:
            pass

    # --- Pagination ---
    paginator = Paginator(feedback_list, 10)
    page = request.GET.get('page')

    try:
        feedbacks = paginator.page(page)
    except PageNotAnInteger:
        feedbacks = paginator.page(1)
    except EmptyPage:
        feedbacks = paginator.page(paginator.num_pages)

    # --- Rating Summary ---
    rating_counts_raw = Feedback.objects.values('rating').annotate(count=Count('rating'))
    rating_summary = []
    counts = {item['rating']: item['count'] for item in rating_counts_raw}
    for i in range(5, 0, -1):
        rating_summary.append({
            'star': i,
            'count': counts.get(i, 0)
        })

    # --- Average Rating ---
    average_rating = Feedback.objects.aggregate(avg=Avg('rating'))['avg']

    context = {
        'feedbacks': feedbacks,
        'rating_summary': rating_summary,
        'average_rating': average_rating,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'admin_feedback.html', context)


# --- Staff Views ---

# Staff login view
def staff_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        try:
            staff = Staff.objects.get(username=username)
            if check_password(password, staff.password):
                request.session['staff_id'] = staff.id
                request.session['staff_name'] = staff.name
                messages.success(request, "Successfully logged in.",extra_tags='canteen success')
                return redirect('staff_dashboard')
        except Staff.DoesNotExist:
            pass
        messages.error(request, "Invalid credentials.",extra_tags='canteen error')
    return render(request, 'staff_login.html')


# Staff dashboard
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.timezone import now
from .models import Staff, Order, Student, User  # Adjust if needed

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from .models import Staff, Order, OrderItem, Student, User
from django.views.decorators.csrf import csrf_exempt
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.timezone import now
from django.utils import timezone
from .models import Staff, Student, Order, OrderItem
from django.contrib.auth.models import User
@staff_required
def staff_dashboard(request):
    if 'staff_id' not in request.session:
        messages.error(request, "Please log in first.")
        return redirect('staff_login')

    staff = get_object_or_404(Staff, id=request.session['staff_id'])
    today = now().date()

    # Get all student users linked via username
    student_usernames = Student.objects.values_list('username', flat=True)
    student_user_ids = User.objects.filter(username__in=student_usernames)

    # Order statistics
    orders_today = Order.objects.filter(created_at__date=today, user__in=student_user_ids).count()
    orders_pending = Order.objects.filter(status='pending').count()
    orders_confirmed = Order.objects.filter(status='confirmed').count()
    orders_prepared = Order.objects.filter(status='prepared').count()

    # Detailed order lists (if needed in dashboard)
    orders_today_list = Order.objects.filter(created_at__date=today, user__in=student_user_ids)
    orders_pending_list = Order.objects.filter(status='pending')
    orders_confirmed_list = Order.objects.filter(status='confirmed')

    # Staff-specific confirmed orders
    confirmed_by_this_staff = Order.objects.filter(status='confirmed', staff=staff)
    total_amount = sum(order.total_price for order in confirmed_by_this_staff)
    total_count = confirmed_by_this_staff.count()

    # Attach optional stats to staff object
    staff.total_confirmed_amount = total_amount
    staff.confirmed_orders_count = total_count
   

    # All today's OrderItems including cancelled ones
    tasks = OrderItem.objects.select_related('order', 'item').filter(
        order__status__in=['pending', 'preparing', 'prepared', 'confirmed', 'cancelled'],
        order__created_at__date=today
    ).order_by('-order__created_at')
    paginator = Paginator(tasks, 10)  # Show 10 tasks per page
    page_number = request.GET.get('page')  # Get the page number from the query string
    tasks_page = paginator.get_page(page_number)

    context = {
        'staff_name': request.session.get('staff_name'),
        'orders_today': orders_today,
        'orders_pending': orders_pending,
        'orders_prepared': orders_prepared,
        'orders_confirmed': orders_confirmed,
        'orders_today_details': orders_today_list,
        'orders_pending_details': orders_pending_list,
        'orders_confirmed_details': orders_confirmed_list,
        'tasks': tasks,
        'tasks': tasks_page,
    }

    return render(request, 'staff_dashboard.html', context)


from .models import Order, Notification

@csrf_exempt
def update_order_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            new_status = data.get('status')

            if not order_id or not new_status:
                return JsonResponse({'error': 'Missing order_id or status'}, status=400)

            order = get_object_or_404(Order, id=order_id)

            valid_statuses = ['accepted', 'prepared', 'delivered']
            if new_status not in valid_statuses:
                return JsonResponse({'error': 'Invalid status'}, status=400)

            # Update order status
            order.status = new_status
            order.save()

            # Create notification message
            status_messages = {
                'accepted': 'Your order has been accepted by the canteen.',
                'prepared': 'Your order is now prepared and ready.',
                'delivered': 'Your order has been delivered successfully.',
            }

            # Create a notification for the student
            Notification.objects.create(
                user=order.user,
                message=status_messages.get(new_status, 'Order status updated.'),
                status=new_status
            )

            return JsonResponse({'success': True, 'order_id': order_id, 'status': new_status})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)



# Staff logout
def staff_logout(request):
    request.session.flush()
    messages.info(request, "Logged out successfully.",extra_tags='canteen success')
    return redirect('staff_login')


# Manage food items (staff)
@staff_required
def manage_food(request):
    staff = get_object_or_404(Staff, id=request.session['staff_id'])
    items = Item.objects.all()
    if request.method == 'POST':
        if 'add_item' in request.POST:
            name = request.POST.get('name')
            price = request.POST.get('price')
            image = request.FILES.get('image')
            if name and price:
                Item.objects.create(name=name, price=price, image=image)
                messages.success(request, "Food item added successfully.")
            else:
                messages.error(request, "Please provide valid details.")
        elif 'delete_item' in request.POST:
            item_id = request.POST.get('item_id')
            Item.objects.filter(id=item_id).delete()
            messages.success(request, "Food item deleted.")
        return redirect('manage_food')
    context = {
        'staff_name': request.session.get('staff_name'),
        
    }
    context.update({'items': items})
    return render(request, 'manage_food.html', context)


# Manage inventory stock
@staff_required
def manage_inventory(request):
    staff = get_object_or_404(Staff, id=request.session['staff_id'])
    items = Item.objects.all()
    if request.method == 'POST':
        for item in items:
            field = f'add_stock_{item.id}'
            if field in request.POST:
                try:
                    added_qty = int(request.POST[field])
                    if added_qty >= 0:
                        item.quantity_available += added_qty
                        item.save()
                        messages.success(request, f"Added {added_qty} units to {item.name}.")
                    else:
                        messages.error(request, "Quantity cannot be negative.")
                except ValueError:
                    messages.error(request, f"Invalid input for {item.name}.")
        return redirect('manage_inventory')
    context = {
        'staff_name': request.session.get('staff_name'),
        
    }
    context.update({'items': items})
    return render(request, 'manage_inventory.html', context)


# --- Student Signup/Login/Dashboard ---

# Student signup view

def student_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password1)
            student = Student.objects.create(
                username=username,
                email=email,
                name=username,
                # don't store plain password here
            )

            # Create notification for admin user(s)
            admins = User.objects.filter(is_superuser=True)  # or staff=True if you want staff to get it
           

            messages.success(request, 'Account created. Please log in.',extra_tags='student success')
            return redirect('student_login')

    return render(request, 'student_signup.html')

# Student login
def student_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful. Welcome back!',extra_tags='student success')
            return redirect('student_dashboard')  # change to your actual dashboard URL
        else:
            messages.error(request, 'Invalid username or password.',extra_tags='student error')
    return render(request, 'student_login.html')

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Student

@login_required
def student_profile(request):
    # Fetch current student's record
    student = get_object_or_404(Student, username=request.user.username)

    if request.method == 'POST':
        # Profile update form
        if 'update_profile' in request.POST:
            name = request.POST.get('name')
            username = request.POST.get('username')
            email = request.POST.get('email')
            contact = request.POST.get('contact')
            address = request.POST.get('address')
            profile_picture = request.FILES.get('profile_picture')

            # Update Student model
            student.name = name
            student.username = username
            student.email = email
            student.contact = contact
            student.address = address
            if profile_picture:
                student.profile_picture = profile_picture
            student.save()

            # Update User model (optional: if you want email/username to stay in sync)
            user = request.user
            user.username = username
            user.email = email
            user.save()

            messages.success(request, 'Profile updated successfully.')

        # Password change form
        elif 'change_password' in request.POST:
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
            else:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)  # Keep user logged in
                messages.success(request, 'Password changed successfully.')

    return render(request, 'student_profile.html', {'student': student})
# Student dashboard view
from .models import Student, Order, Feedback, Notification

@login_required(login_url='student_login')
def student_dashboard(request):
    user = request.user

    # ✅ Get student object using email or OneToOne
    try:
        student = Student.objects.get(email=user.email)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('student_login')

    orders_placed_count = Order.objects.filter(user=user).count()
    pending_orders_count = Order.objects.filter(user=user, status='pending').count()
    feedback_count = Feedback.objects.filter(student=user).count()
    recent_orders = Order.objects.filter(user=user).order_by('-created_at')[:5]

    all_notifications = Notification.objects.filter(user=user).order_by('-created_at')
    notifications_count = all_notifications.filter(is_read=False).count()
    notifications = all_notifications[:10]

    context = {
        'student': student,  # ✅ pass student object to template
        'orders_placed_count': orders_placed_count,
        'pending_orders_count': pending_orders_count,
        'feedback_count': feedback_count,
        'recent_orders': recent_orders,
        'notifications': notifications,
        'notifications_count': notifications_count,
    }
    return render(request, 'student_dashboard.html', context)

# Student logout
@login_required
def student_logout(request):
    logout(request)
    messages.info(request, "Logged out successfully.",extra_tags='student success')
    return redirect('student_login')


# --- Menu, Cart, and Orders ---

# View menu (student)
from django.contrib.auth.decorators import login_required
from .models import Item, Notification, Student

@login_required
def view_menu(request):
    user = request.user
    menu_items = Item.objects.all()
    student = get_object_or_404(Student, email=request.user.email)
    # Fetch notifications
    all_notifications = Notification.objects.filter(user=user).order_by('-created_at')
    notifications_count = all_notifications.filter(is_read=False).count()
    notifications = all_notifications[:10]

    # Get favorites (if you use custom Student model)
    try:
        student = Student.objects.get(email=user.email)
       
    except Student.DoesNotExist:
        favorite_ids = []

    context = {
        'menu_items': menu_items,
        'notifications': notifications,
        'notifications_count': notifications_count,
        'student': student  
        
    }

    return render(request, 'view_menu.html', context)



# Add item to cart
@login_required
def add_to_cart(request):
    if request.method == "POST":
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 1))
        item = get_object_or_404(Item, id=item_id)
        if quantity > item.quantity_available:
            messages.error(request, "Requested quantity exceeds available stock.")
            return redirect('view_menu')
        cart_item, created = CartItem.objects.get_or_create(user=request.user, item=item)
        cart_item.quantity = min(cart_item.quantity + quantity if not created else quantity, item.quantity_available)
        cart_item.save()
        messages.success(request, f"Added {quantity} x {item.name} to your cart.")
    return redirect('view_menu')

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import CartItem



# Remove item from cart
@login_required
def remove_from_cart(request, cart_item_id):
    CartItem.objects.filter(id=cart_item_id, user=request.user).delete()
    messages.success(request, "Item removed from cart.")
    return redirect('view_cart')

@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)

    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
            available_stock = cart_item.item.quantity_available

            if quantity < 1:
                messages.error(request, "Quantity must be at least 1.")
            elif quantity > available_stock:
                messages.error(request, f"Only {available_stock} items available in stock.")
            else:
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, f"Updated {cart_item.item.name} quantity to {quantity}.")
        except ValueError:
            messages.error(request, "Invalid quantity entered.")

    return redirect('view_cart')
# Place order

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Order
from .forms import UploadQRCodeForm

from datetime import timedelta
from django.utils.timezone import now


from .models import Student  # import if not already
from django.shortcuts import get_object_or_404
@login_required
def order_status(request):
    user = request.user
    form = UploadQRCodeForm(request.POST or None, request.FILES or None)

    status_filter = request.GET.get('status', None)

    orders_qs = Order.objects.filter(user=user)
    if status_filter in ['pending', 'confirmed']:
        orders_qs = orders_qs.filter(status=status_filter)

    paginator = Paginator(orders_qs.order_by('-created_at'), 5)
    page_number = request.GET.get('page')
    orders_page = paginator.get_page(page_number)

    # Attach prep_time to each order as preparation_time and can_cancel flag
    for order in orders_page:
        if hasattr(order, 'prep_time'):
            order.preparation_time = order.prep_time
        elif hasattr(order, 'order') and hasattr(order.order, 'prep_time'):
            order.preparation_time = order.order.prep_time
        else:
            order.preparation_time = None

        time_passed = now() - order.created_at
        order.can_cancel = (
            order.status in ['pending', 'confirmed'] and
            time_passed <= timedelta(minutes=1)
        )
        order.remaining_seconds = max(0, 60 - int(time_passed.total_seconds()))

    # 🧩 Get student's wallet balance
    student = get_object_or_404(Student, email=request.user.email)

    # Handle QR code upload
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "QR Code uploaded successfully.")
        redirect_url = 'order_status'
        query_params = ''
        if status_filter:
            query_params += f'?status={status_filter}'
        if page_number:
            query_params += f'&page={page_number}' if query_params else f'?page={page_number}'
        return redirect(redirect_url + query_params)

    context = {
        'orders': orders_page,
        'form': form,
        'status_filter': status_filter,
        'student': student  # ✅ Pass student into template
    }
    return render(request, 'order_status.html', context)

from django.urls import reverse
from django.contrib import messages
from .models import Order, OrderItem
# Staff QR-based payment verification
@staff_required
def staff_payments(request):
    staff = get_object_or_404(Staff, id=request.session['staff_id'])
    order = None
    order_items = None
    if request.method == 'POST':
        if 'confirm_order_id' in request.POST:
            try:
                order_to_confirm = Order.objects.get(id=int(request.POST['confirm_order_id']))
                order_to_confirm.status = 'confirmed'
                order_to_confirm.save()
                # Create notification for the student who placed the order
               
                messages.success(request, "Order confirmed.")
                return redirect(f"{reverse('staff_payments')}?order_id={order_to_confirm.id}")
            except Order.DoesNotExist:
                messages.error(request, "Order not found.")
    
        qr_code_data = request.POST.get('qr_code_data')
        if qr_code_data:
            try:
                order = Order.objects.get(qr_code=qr_code_data)
            except Order.DoesNotExist:
                try:
                    order = Order.objects.get(id=int(qr_code_data))
                except (Order.DoesNotExist, ValueError):
                    messages.error(request, "Order not found.")
                    order = None
    # For GET or after redirect with order_id param
    if request.method == 'GET' or order is None:
        order_id = request.GET.get('order_id')
        if order_id:
            try:
                order = Order.objects.get(id=int(order_id))
            except Order.DoesNotExist:
                messages.error(request, "Order not found.")
                order = None
    if order:
        order_items = OrderItem.objects.filter(order=order)

    return render(request, 'staff_payments.html', {
        'order': order,
        'order_items': order_items,
        'staff_name': request.session.get('staff_name'),
    })
# --- Feedback ---F
@login_required
def student_feedback(request):
    student = get_object_or_404(Student, email=request.user.email)
    if request.method == 'POST':
        comments = request.POST.get('feedback')
        rating = int(request.POST.get('rating', 0))
        Feedback.objects.create(student=request.user, comments=comments, rating=rating)
        messages.success(request, "Feedback submitted.")
        return redirect('student_feedback')
    context = {
        
        'student': student  # ✅ Pass student into template
    }
    return render(request, 'student_feedback.html',context)
# --- Admin Utility ---
def admin_delete_all_orders(request):
    if request.method == 'POST':
        Order.objects.all().delete()
        messages.success(request, "All orders deleted.")
    else:
        messages.error(request, "Invalid request.")

    return redirect(reverse('admin_orders'))
# --- Payment & QR Generation ---
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.models import User
# --- Password Reset via OTP ---
# Generate a 6-digit OTP
def generate_otp():
    return str(random.randint(100000, 999999))
def password_reset_request(request):
    form = PasswordResetRequestForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        try:
            user = User.objects.get(username=username)
            otp = generate_otp()
            request.session['password_reset_otp'] = otp
            request.session['password_reset_user'] = user.username
            send_mail('Your OTP', f'OTP: {otp}', 'noreply@ecanteen.com', [user.email])
            messages.success(request, "OTP sent to your email.")
            return redirect('password_reset_verify')
        except User.DoesNotExist:
            messages.error(request, "User not found.")
    return render(request, 'password_reset_request.html', {'form': form})
# Verify OTP and reset password
def password_reset_verify(request):
    form = PasswordResetVerifyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        otp = form.cleaned_data['otp']
        new_password = form.cleaned_data['new_password']
        if otp == request.session.get('password_reset_otp'):
            try:
                user = User.objects.get(username=request.session['password_reset_user'])
                user.password = make_password(new_password)
                user.save()
                request.session.flush()
                messages.success(request, "Password reset successful.")
                return redirect('home')
            except User.DoesNotExist:
                messages.error(request, "User not found.")
        else:
            messages.error(request, "Invalid OTP.")
    return render(request, 'password_reset_verify.html', {'form': form})
from django.views.decorators.csrf import csrf_exempt
@staff_required
def staff_profile(request):
    staff_id = request.session.get('staff_id')
    staff = get_object_or_404(Staff, id=staff_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        profile = request.FILES.get('profile')
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        # Update name and email
        staff.name = name
        staff.email = email
        # Update profile pic
        if profile:
            staff.profile = profile
        # Password change logic
        if current_password and new_password and confirm_password:
            if not check_password(current_password, staff.password):
                messages.error(request, "Current password is incorrect.")
            elif new_password != confirm_password:
                messages.error(request, "New passwords do not match.")
            else:
                staff.password = make_password(new_password)
                messages.success(request, "Password updated successfully.")
        staff.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('staff_profile') 
    context={
        'staff_name': request.session.get('staff_name'),
    } # Or reload same page
    context.update({'staff': staff})
    return render(request, 'staff_profile.html',context )

from django.shortcuts import render, get_object_or_404
from django.core.files.base import File
from io import BytesIO
import qrcode
import json
from django.views.decorators.csrf import csrf_protect  # make sure to import this
from .models import Order, OrderItem  # adjust import as per your project

@csrf_protect
def credit_card_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == "POST":
        cardholder = request.POST.get('cardholder', '').strip()
        cardnumber = request.POST.get('cardnumber', '').replace(' ', '')
        expiry = request.POST.get('expiry', '').strip()
        cvv = request.POST.get('cvv', '').strip()

        # You can add server-side validation here if you want

        # For demo, we assume payment is successful
        items = OrderItem.objects.filter(order=order)

        qr_content = {
            'order_id': order.id,
            'items': [{'name': i.item.name, 'quantity': i.quantity, 'price': float(i.item.price)} for i in items],
            'total': float(order.total_price),
            'payment_method': 'credit_card',
        }

        qr_img = qrcode.make(json.dumps(qr_content))
        buffer = BytesIO()
        qr_img.save(buffer, format='PNG')
        buffer.seek(0)
        order.qr_code.save(f'order_{order.id}_qr.png', File(buffer))
        order.save()

        # Render the QR code page with order info
        return render(request, 'order_qr_code.html', {'order': order})

    # If GET request, show the credit card form
    return render(request, 'credit_card.html', {'order': order})

from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.contrib import messages

def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        user_email = request.POST.get('email')
        message = request.POST.get('message')

        # Send to admin
        admin_email = 'destfinder9564@gmail.com'  # Change to your admin email
        admin_subject = f"New Contact Message from {name}"
        admin_message = f"Name: {name}\nEmail: {user_email}\nMessage:\n{message}"
        send_mail(admin_subject, admin_message, user_email, [admin_email])

        # Send to user
        user_subject = "Thank you for contacting eCanteen!"
        user_message = (
            f"Hi {name},\n\nThank you for reaching out to us. "
            "We have received your message and will get back to you shortly.\n\n"
            "Regards,\neCanteen Team"
        )
        send_mail(user_subject, user_message, admin_email, [user_email])

        # Add custom tag so we can filter it in the template
        messages.success(request, "Message sent successfully.", extra_tags='contact')
        return redirect('/')
 # Redirect after POST
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Order, Staff

import qrcode
from io import BytesIO
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files import File
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from urllib.parse import urlencode

from .models import Student, CartItem, Item, Order, OrderItem


@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    total = sum(item.quantity * item.item.price for item in cart_items)

    for item in cart_items:
        item.subtotal = item.quantity * item.item.price

    # Get student profile (based on email)
    try:
        student = Student.objects.get(email=request.user.email)
    except Student.DoesNotExist:
        student = None

    # Check if order_id is passed to show modal
    order = None
    qr_code_url = None
    order_id = request.GET.get('order_id')
    if order_id:
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            qr_code_url = order.qr_code.url if order.qr_code else None
        except Order.DoesNotExist:
            pass

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total': total,
        'student': student,
        'recent_order': order,
        'qr_code_url': qr_code_url,
    })


from django.urls import reverse
from django.core.files import File
from django.utils.http import urlencode
from io import BytesIO
import qrcode
from decimal import Decimal
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CartItem, Order, OrderItem, Student


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
from django.utils.http import urlencode
from decimal import Decimal
from io import BytesIO
from django.core.files import File
import qrcode

from .models import CartItem, Order, OrderItem, Student, Item


@login_required
@transaction.atomic
def place_order(request):
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        cart_items = CartItem.objects.filter(user=request.user)

        if not cart_items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect('view_cart')

        total_price = sum(item.quantity * item.item.price for item in cart_items)

        # Get student record
        try:
            student = Student.objects.get(email=request.user.email)
        except Student.DoesNotExist:
            messages.error(request, "Student profile not found.")
            return redirect('view_cart')

        # Handle Wallet Payment
        if payment_method == "Wallet":
            if student.wallet_balance < total_price:
                messages.error(request, "Insufficient wallet balance.")
                return redirect('view_cart')
            student.wallet_balance -= Decimal(total_price)
            student.save()

        # Create the Order
        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            status='pending',
            payment_method=payment_method
        )

        # Add Order Items & reduce stock
        for cart_item in cart_items:
            item = cart_item.item
            quantity = cart_item.quantity

            # Check stock
            if item.quantity_available < quantity:
                messages.error(request, f"Only {item.quantity_available} units left for {item.name}.")
                order.delete()
                return redirect('view_cart')

            # Reduce available quantity
            item.quantity_available -= quantity
            item.save()

            # Add to order items
            OrderItem.objects.create(
                order=order,
                item=item,
                quantity=quantity,
                price=item.price * quantity
            )

        # Clear the cart
        cart_items.delete()

        # Generate QR Code
        qr_data = f"Order ID: {order.id}\n"
        qr_data += "Items:\n"
        for item in order.items.all():
            qr_data += f"{item.quantity} × {item.item.name} — ₹{item.price}\n"
        qr_data += f"Total: ₹{order.total_price}\n"
        qr_data += f"Link: {request.build_absolute_uri(reverse('order_detail_by_qr', args=[order.id]))}"

        qr_img = qrcode.make(qr_data)
        buffer = BytesIO()
        qr_img.save(buffer)
        filename = f'order_{order.id}_qr.png'
        order.qr_code.save(filename, File(buffer), save=True)

        # Redirect with order_id for modal
        query = urlencode({'order_id': order.id})
        return redirect(f"{reverse('view_cart')}?{query}")

    return redirect('view_cart')


# Used by staff/QR scan to see order by ID
@login_required
def order_details_by_qr(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'order_detail_scan.html', {'order': order})

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from .models import Order, Staff, Notification  # adjust import as needed

@csrf_exempt
def accept_order(request):
    if request.method == 'POST':
        try:
            order_id = request.POST.get('order_id')
            prep_time = request.POST.get('prep_time')
            
            if not order_id or not prep_time:
                return JsonResponse({'error': 'Missing order_id or prep_time'}, status=400)

            order = get_object_or_404(Order, id=order_id)
            staff = get_object_or_404(Staff, id=request.session.get('staff_id'))

            # ✅ Check if 1 minute has passed since order creation
            time_elapsed = timezone.now() - order.created_at
            if time_elapsed < timedelta(minutes=1):
                remaining = 60 - int(time_elapsed.total_seconds())
                return JsonResponse({
                    'error': f'You can only accept this order after 1 minute of creation. Try again in {remaining} seconds.'
                }, status=403)

            # ✅ Proceed with acceptance
            order.status = 'preparing'
            order.prep_time = int(prep_time)
            order.accepted_at = timezone.now()
            order.staff = staff
            order.save()

            # ✅ Create Notification
            Notification.objects.create(
                user=order.user,
                status='accepted',
                message='Your order has been accepted and is being prepared.'
            )

            return JsonResponse({
                'success': True,
                'order_id': order_id,
                'prep_time': prep_time
            })

        except ValueError:
            return JsonResponse({'error': 'Invalid prep_time'}, status=400)
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


def mark_order_prepared(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        
        try:
            order = Order.objects.get(id=order_id)
            order.status = 'prepared'
            order.save()

            # ✅ Create Notification
            Notification.objects.create(
                user=order.user,
                status='prepared',
                message='Your order is now ready for pickup.'
            )

            return redirect('staff_dashboard')

        except Order.DoesNotExist:
            messages.error(request, 'Order not found')
            return redirect('staff_dashboard')
    
    messages.error(request, 'Invalid request')
    return redirect('staff_dashboard')

from django.http import JsonResponse

def mark_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .models import Student


from decimal import Decimal

@login_required
def add_money_wallet(request):
    if request.method == 'POST':
        try:
            amount_str = request.POST.get('amount')
            method = request.POST.get('payment_method')

            if not amount_str or not method:
                messages.error(request, "Amount or Payment Method is missing.")
                return redirect('student_dashboard')

            amount = Decimal(amount_str)
            if amount <= 0:
                messages.error(request, "Amount must be greater than 0.")
                return redirect('student_dashboard')

            # Assuming request.user is linked to Student via OneToOneField or filtering logic
            student = Student.objects.get(email=request.user.email)

            student.wallet_balance += amount
            student.save()

            messages.success(request, f"₹{amount} added to your wallet via {method}.")
        except Student.DoesNotExist:
            messages.error(request, "Student profile not found.")
        except Exception as e:
            messages.error(request, f"Transaction failed: {e}")

    return redirect('student_dashboard')

from django.http import JsonResponse
from django.utils.timezone import now
from datetime import timedelta


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponseNotAllowed
from django.utils.timezone import now
from datetime import timedelta

from datetime import timedelta
from django.utils.timezone import now
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
def cancel_order(request, order_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    order = get_object_or_404(Order, id=order_id, user=request.user)
    time_passed = now() - order.created_at

    if order.status in ['pending', 'confirmed'] and time_passed <= timedelta(minutes=1):
        order.status = 'cancelled'
        order.save()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'Cancellation window expired'}, status=400)




@require_POST
def assign_prep_time(request, order_id):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    order = get_object_or_404(Order, id=order_id)
    prep_time = int(request.POST.get('prep_time', 0))

    if order.status == 'confirmed':
        order.prep_time = prep_time
        order.prep_start_time = timezone.now()
        order.status = 'preparing'
        order.save()
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid status for prep time'})

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Order, Student  # Adjust based on your app structure

@login_required
@csrf_exempt
def pay_online(request, order_id):
    if request.method == 'POST':
        try:
            order = get_object_or_404(Order, id=order_id, user=request.user)

            if order.status not in ['pending', 'confirmed']:
                return JsonResponse({'success': False, 'error': 'Order cannot be paid now'})

            payment_method = request.POST.get('payment_method')
            if not payment_method:
                return JsonResponse({'success': False, 'error': 'Payment method is required'})

            # Wallet Payment
            if payment_method == 'Wallet':
                try:
                    student = Student.objects.get(email=request.user.email)
                    if student.wallet_balance < order.total_price:
                        return JsonResponse({'success': False, 'error': 'Insufficient wallet balance'})
                    student.wallet_balance -= order.total_price
                    student.save()
                except Student.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Student profile not found'})

            # NetBanking Payment
            elif payment_method.lower() == 'netbanking':
                username = request.POST.get('netbank_username')
                password = request.POST.get('netbank_password')
                if not username or not password:
                    return JsonResponse({'success': False, 'error': 'NetBanking username and password are required'})
                # Here you can simulate or validate netbank login if needed
                # For now, we simulate successful netbanking login

            else:
                return JsonResponse({'success': False, 'error': 'Invalid payment method selected'})

            # Update order
            order.payment_method = payment_method
            order.status = 'confirmed'
            order.save()

            return JsonResponse({'success': True, 'message': 'Payment successful'})

        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Order not found'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Order, OrderItem
from django.contrib.auth.decorators import login_required
@login_required
def reorder_view(request, order_id):
    original_order = get_object_or_404(Order, id=order_id, user=request.user)
# Step 1: Create a new order instance
    new_order = Order.objects.create(
        user=request.user,
        total_price=original_order.total_price,
        payment_method='COD',  # or default
        status='pending',      # default status
    )
    # Step 2: Duplicate the order items
    for item in original_order.items.all():
        OrderItem.objects.create(
            order=new_order,
            item=item.item,
            quantity=item.quantity,
            price=item.price,
        )
    messages.success(request, f"Order #{new_order.id} placed successfully!")
    return redirect('order_status')
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Order
from django.utils.timezone import localtime
from django.utils.timezone import localtime
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Order
from django.utils.timezone import localtime
from django.http import JsonResponse
from .models import Order
@login_required
def get_live_order_status(request):
    try:
        # Get the latest *non-delivered* order first
        order = Order.objects.filter(user=request.user).exclude(status='delivered').latest('created_at')

        # If multiple orders exist, prioritize active over cancelled
        if order.status == 'cancelled':
            alt_order = Order.objects.filter(user=request.user).exclude(status__in=['delivered', 'cancelled']).order_by('-created_at').first()
            if alt_order:
                order = alt_order

        order.check_and_update_status()

        progress_map = {
            'pending': 25,
            'preparing': 50,
            'prepared': 75,
            'confirmed': 100,
            'cancelled': 0,
        }

        color_map = {
            'pending': 'bg-accent-600',
            'preparing': 'bg-accent-600',
            'prepared': 'bg-accent-600',
            'confirmed': 'bg-green-500',
            'cancelled': 'bg-red-500',
        }
        return JsonResponse({
            "order_id": order.id,
            "status": order.status.capitalize(),
            "progress": progress_map.get(order.status, 0),
           
            "prep_time": order.prep_time or getattr(order, 'preparation_time', None),
            "status_color": color_map.get(order.status, 'bg-accent-600'),
        })

    except Order.DoesNotExist:
        return JsonResponse({"error": "No active or cancelled orders found."}, status=404)
