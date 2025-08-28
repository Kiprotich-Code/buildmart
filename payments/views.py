from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import requests
import uuid
from .models import BoostPlan, Boost
from .serializers import BoostPlanSerializer, BoostSerializer
from products.models import Product

class BoostPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing BoostPlans. Read-only as plans are typically admin-managed or static.
    """
    queryset = BoostPlan.objects.all()
    serializer_class = BoostPlanSerializer
    permission_classes = [IsAuthenticated]

class BoostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Boosts. Users can list their own boosts and initiate new ones.
    """
    serializer_class = BoostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Boost.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='initiate')
    def initiate_boost(self, request):
        """
        Custom action to initiate a boost for a listing.
        - Validates ownership of the listing.
        - Creates a pending Boost instance.
        - Initializes payment with Flutterwave and returns a payment link for frontend redirect.
        - Frontend should handle redirect to the link and post-payment callback.
        """
        listing_id = request.data.get('listing_id')
        plan_id = request.data.get('plan_id')

        if not listing_id or not plan_id:
            return Response({'error': 'listing_id and plan_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plan = BoostPlan.objects.get(id=plan_id)
            listing = Product.objects.get(id=listing_id, owner=request.user)  # Adjust 'owner' to your Listing model's user field
        except BoostPlan.DoesNotExist:
            return Response({'error': 'Invalid plan'}, status=status.HTTP_400_BAD_REQUEST)
        except Product.DoesNotExist:
            return Response({'error': 'Listing not found or not owned by you'}, status=status.HTTP_400_BAD_REQUEST)

        # Check for existing active boost (optional: business logic to prevent overlap or allow extension)
        existing_boost = Boost.objects.filter(listing=listing, is_active=True).first()
        if existing_boost:
            # For extension: adjust start_date to after current end_date
            start_date = existing_boost.end_date
        else:
            start_date = None

        tx_ref = str(uuid.uuid4())
        boost = Boost.objects.create(
            user=request.user,
            listing=listing,
            plan=plan,
            tx_ref=tx_ref,
            payment_status='pending'
        )

        # Flutterwave payment initialization
        payload = {
            "tx_ref": tx_ref,
            "amount": str(plan.price),
            "currency": "NGN",
            "redirect_url": "https://yourdomain.com/payment/callback",  # Replace with your frontend callback URL
            "payment_options": "card,banktransfer,ussd,mobilemoney",
            "customer": {
                "email": request.user.email,
                "phonenumber": request.user.profile.phone if hasattr(request.user, 'profile') else "",  # Adjust if phone is available
                "name": request.user.get_full_name() or request.user.username
            },
            "customizations": {
                "title": "BuildMart Boost Payment",
                "description": f"Payment for {plan.name} boost on listing: {listing.name}",
                "logo": "https://yourdomain.com/logo.png"  # Optional: replace with your logo URL
            }
        }

        headers = {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                "https://api.flutterwave.com/v3/payments",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            payment_link = data['data']['link']
            return Response({'payment_link': payment_link, 'boost_id': boost.id}, status=status.HTTP_200_OK)
        except requests.RequestException as e:
            boost.delete()  # Cleanup on failure
            return Response({'error': f'Failed to initialize payment: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@permission_classes([])
def flutterwave_webhook(request):
    """
    Webhook endpoint for Flutterwave to notify on payment events.
    - Verifies the transaction with Flutterwave API for security.
    - Updates the Boost status on successful payment.
    - Always return 200 to acknowledge receipt.
    """
    if request.method != 'POST':
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    payload = request.data
    event = payload.get('event')
    if event != 'charge.completed':
        return Response(status=status.HTTP_200_OK)  # Acknowledge but ignore other events

    data = payload.get('data')
    if not data:
        return Response(status=status.HTTP_200_OK)

    tx_ref = data.get('tx_ref')
    fw_tx_id = data.get('id')

    try:
        boost = Boost.objects.get(tx_ref=tx_ref)
        if boost.payment_status == 'paid':
            return Response(status=status.HTTP_200_OK)  # Idempotent: already processed

        # Verify transaction with Flutterwave
        headers = {
            "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}"
        }
        verify_url = f"https://api.flutterwave.com/v3/transactions/{fw_tx_id}/verify"
        response = requests.get(verify_url, headers=headers)
        response.raise_for_status()
        ver_data = response.json()['data']

        if (
            ver_data['status'] == 'successful' and
            float(ver_data['amount']) == float(boost.plan.price) and
            ver_data['currency'] == 'NGN' and
            ver_data['tx_ref'] == tx_ref
        ):
            boost.payment_status = 'paid'
            # Handle extension if existing boost
            existing_boost = Boost.objects.filter(listing=boost.listing, is_active=True).exclude(id=boost.id).first()
            if existing_boost:
                boost.start_date = existing_boost.end_date
                boost.end_date = boost.start_date + timedelta(days=boost.plan.duration_days)
            else:
                boost.start_date = timezone.now()
                boost.end_date = boost.start_date + timedelta(days=boost.plan.duration_days)
            boost.is_active = True
            boost.save()
        else:
            boost.payment_status = 'failed'
            boost.save()
    except (Boost.DoesNotExist, requests.RequestException):
        pass 

    return Response(status=status.HTTP_200_OK)