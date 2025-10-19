from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription, Invoice, Payment

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'price_monthly', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'display_name')

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'start_date', 'end_date', 'auto_renew')
    list_filter = ('status', 'plan', 'auto_renew', 'start_date')
    search_fields = ('user__username', 'plan__name')
    readonly_fields = ('start_date',)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'subscription', 'amount', 'status', 'issue_date', 'due_date')
    list_filter = ('status', 'issue_date', 'due_date')
    search_fields = ('invoice_number', 'subscription__user__username')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('subscription', 'amount', 'payment_method', 'status', 'payment_date')
    list_filter = ('status', 'payment_method', 'payment_date')
    search_fields = ('subscription__user__username', 'transaction_id')
