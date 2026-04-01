# decorators.py
from django.shortcuts import redirect
from django.contrib import messages
def staff_required(view_func):
    def wrapper(request, *args, **kwargs):
        if 'staff_id' not in request.session:
            messages.error(request, "Staff login required.")
            return redirect('staff_login')
        return view_func(request, *args, **kwargs)
    return wrapper
