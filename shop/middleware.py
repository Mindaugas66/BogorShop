from .models import Visitor
from django.utils import timezone


class VisitorLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get the visitor's IP address
        ip_address = request.META.get('REMOTE_ADDR')

        # Get today's date
        today = timezone.now().date()

        # Check if a visit from this IP was already logged today
        if not Visitor.objects.filter(ip_address=ip_address, date=today).exists():
            # Log the visitor if not already logged today
            Visitor.objects.create(ip_address=ip_address)

        # Process the response as usual
        response = self.get_response(request)
        return response


class VisitorActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Update the session with the current time if the session is new or has activity
        request.session['last_activity'] = timezone.now().isoformat()

        return response