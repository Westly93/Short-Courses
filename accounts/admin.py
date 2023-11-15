from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import UserAccount, AuditTrail, Inquiry, ProofOfPayment, Profile, ProofOfPaymentReject
# Register your models here.

admin.site.register(UserAccount, SimpleHistoryAdmin)
admin.site.register(AuditTrail)
admin.site.register(Inquiry)
admin.site.register(ProofOfPayment, SimpleHistoryAdmin)
admin.site.register(Profile)
admin.site.register(ProofOfPaymentReject)
