import os
import logging
import stripe
from django.conf import settings
from django.utils import timezone
from .models import UserSubscription, Payment, Invoice

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripePaymentService:
    """Service for handling Stripe payment processing"""

    @staticmethod
    def create_subscription_checkout_session(user, plan):
        """Create a Stripe checkout session for subscription"""
        try:
            # Create or get customer
            customer = StripePaymentService._get_or_create_customer(user)

            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': plan.display_name,
                            'description': plan.description,
                        },
                        'unit_amount': int(plan.price_monthly * 100),  # Convert to cents
                        'recurring': {
                            'interval': 'month',
                        },
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"{settings.SITE_URL}/subscriptions/success/?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.SITE_URL}/subscriptions/cancel/",
                metadata={
                    'user_id': user.id,
                    'plan_id': plan.id,
                }
            )

            return session

        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            return None

    @staticmethod
    def handle_webhook_event(event):
        """Handle Stripe webhook events"""
        try:
            if event.type == 'checkout.session.completed':
                session = event.data.object
                StripePaymentService._handle_checkout_completed(session)

            elif event.type == 'invoice.payment_succeeded':
                invoice = event.data.object
                StripePaymentService._handle_payment_succeeded(invoice)

            elif event.type == 'invoice.payment_failed':
                invoice = event.data.object
                StripePaymentService._handle_payment_failed(invoice)

            elif event.type == 'customer.subscription.deleted':
                subscription = event.data.object
                StripePaymentService._handle_subscription_cancelled(subscription)

            return True

        except Exception as e:
            logger.error(f"Error handling webhook event {event.type}: {str(e)}")
            return False

    @staticmethod
    def _get_or_create_customer(user):
        """Get or create Stripe customer"""
        try:
            # Check if user already has a Stripe customer ID
            if hasattr(user, 'stripe_customer_id') and user.stripe_customer_id:
                return stripe.Customer.retrieve(user.stripe_customer_id)

            # Create new customer
            customer = stripe.Customer.create(
                email=user.email,
                name=f"{user.first_name} {user.last_name}".strip() or user.username,
                metadata={
                    'user_id': user.id,
                }
            )

            # Store customer ID (you'd need to add this field to User model)
            # user.stripe_customer_id = customer.id
            # user.save()

            return customer

        except Exception as e:
            logger.error(f"Error creating/retrieving customer: {str(e)}")
            raise

    @staticmethod
    def _handle_checkout_completed(session):
        """Handle successful checkout completion"""
        try:
            user_id = session.metadata.get('user_id')
            plan_id = session.metadata.get('plan_id')

            user = User.objects.get(id=user_id)
            plan = SubscriptionPlan.objects.get(id=plan_id)

            # Create or update subscription
            subscription, created = UserSubscription.objects.get_or_create(
                user=user,
                defaults={
                    'plan': plan,
                    'status': 'active',
                    'payment_method': 'card',
                    'start_date': timezone.now(),
                    'end_date': timezone.now() + timezone.timedelta(days=30),
                }
            )

            if not created:
                subscription.plan = plan
                subscription.status = 'active'
                subscription.payment_method = 'card'
                subscription.start_date = timezone.now()
                subscription.end_date = timezone.now() + timezone.timedelta(days=30)
                subscription.save()

            # Create payment record
            Payment.objects.create(
                subscription=subscription,
                amount=plan.price_monthly,
                payment_method='card',
                transaction_id=session.id,
                status='completed',
                payment_date=timezone.now(),
            )

            logger.info(f"Subscription created for user {user.username}")

        except Exception as e:
            logger.error(f"Error handling checkout completion: {str(e)}")

    @staticmethod
    def _handle_payment_succeeded(invoice):
        """Handle successful payment"""
        try:
            subscription_id = invoice.subscription
            amount = invoice.amount_paid / 100  # Convert from cents

            # Find our subscription by Stripe subscription ID
            subscription = UserSubscription.objects.filter(
                stripe_subscription_id=subscription_id
            ).first()

            if subscription:
                # Update subscription
                subscription.last_payment_date = timezone.now()
                subscription.status = 'active'
                subscription.save()

                # Create payment record
                Payment.objects.create(
                    subscription=subscription,
                    amount=amount,
                    payment_method='card',
                    transaction_id=invoice.id,
                    status='completed',
                    payment_date=timezone.now(),
                )

                logger.info(f"Payment processed for subscription {subscription.id}")

        except Exception as e:
            logger.error(f"Error handling payment success: {str(e)}")

    @staticmethod
    def _handle_payment_failed(invoice):
        """Handle failed payment"""
        try:
            subscription_id = invoice.subscription

            subscription = UserSubscription.objects.filter(
                stripe_subscription_id=subscription_id
            ).first()

            if subscription:
                # Mark subscription as having payment issues
                subscription.status = 'pending'
                subscription.save()

                logger.warning(f"Payment failed for subscription {subscription.id}")

        except Exception as e:
            logger.error(f"Error handling payment failure: {str(e)}")

    @staticmethod
    def _handle_subscription_cancelled(stripe_subscription):
        """Handle subscription cancellation"""
        try:
            subscription = UserSubscription.objects.filter(
                stripe_subscription_id=stripe_subscription.id
            ).first()

            if subscription:
                subscription.status = 'cancelled'
                subscription.save()

                logger.info(f"Subscription cancelled for user {subscription.user.username}")

        except Exception as e:
            logger.error(f"Error handling subscription cancellation: {str(e)}")

    @staticmethod
    def cancel_subscription(subscription):
        """Cancel a subscription"""
        try:
            if subscription.stripe_subscription_id:
                # Cancel in Stripe
                stripe.Subscription.delete(subscription.stripe_subscription_id)

            # Update local record
            subscription.status = 'cancelled'
            subscription.save()

            return True

        except Exception as e:
            logger.error(f"Error cancelling subscription: {str(e)}")
            return False

    @staticmethod
    def create_payment_intent(amount, currency='usd'):
        """Create a Stripe payment intent for one-time payments"""
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency,
                automatic_payment_methods={
                    'enabled': True,
                },
            )
            return intent
        except Exception as e:
            logger.error(f"Error creating payment intent: {str(e)}")
            return None


class PayPalPaymentService:
    """Service for handling PayPal payments"""

    PAYPAL_API_BASE = "https://api.paypal.com" if not settings.DEBUG else "https://api.sandbox.paypal.com"

    def __init__(self):
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self.access_token = None

    def _get_access_token(self):
        """Get PayPal access token"""
        try:
            import base64
            import requests

            auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            headers = {
                'Authorization': f'Basic {auth}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            response = requests.post(
                f"{self.PAYPAL_API_BASE}/v1/oauth2/token",
                headers=headers,
                data={'grant_type': 'client_credentials'}
            )
            response.raise_for_status()

            self.access_token = response.json()['access_token']
            return self.access_token

        except Exception as e:
            logger.error(f"Error getting PayPal access token: {str(e)}")
            return None

    def create_subscription(self, user, plan):
        """Create PayPal subscription"""
        try:
            if not self.access_token:
                self._get_access_token()

            # This would implement PayPal subscription creation
            # For brevity, returning a placeholder
            return {
                'id': f'paypal_sub_{user.id}_{plan.id}',
                'status': 'pending'
            }

        except Exception as e:
            logger.error(f"Error creating PayPal subscription: {str(e)}")
            return None


class PaymentService:
    """Unified payment service interface"""

    @staticmethod
    def create_subscription(user, plan, payment_method='stripe'):
        """Create subscription with specified payment method"""
        if payment_method == 'stripe':
            return StripePaymentService.create_subscription_checkout_session(user, plan)
        elif payment_method == 'paypal':
            service = PayPalPaymentService()
            return service.create_subscription(user, plan)
        else:
            raise ValueError(f"Unsupported payment method: {payment_method}")

    @staticmethod
    def process_webhook(request):
        """Process payment webhook"""
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return StripePaymentService.handle_webhook_event(event)

        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return False