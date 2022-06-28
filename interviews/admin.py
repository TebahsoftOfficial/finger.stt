from django.contrib import admin
from .models import Interviews, Category, Client, Manager, CodeShare, Purchase

# Add User model for customizing
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

class InterviewsAdmin(admin.ModelAdmin):
    #list_display = ('id', 'title', 'duration', 'created_at', 'author')
    list_display = ('id', 'title', 'duration', 'created_at', 'author', 'delete_flag', 'share_flag', 'gd_cmk', 'gs_cmk', 'sm_cmk', 'smr_cmk')
    ordering = ['-created_at']

admin.site.register(Interviews, InterviewsAdmin)

#class CategoryAdmin(admin.ModelAdmin):
#    prepopulated_fields = {'slug':('name',)}

#admin.site.register(Category, CategoryAdmin)
admin.site.register(Category)

admin.site.register(Client)


class ManagerAdmin(admin.ModelAdmin):
    #list_display = ('mid', 'max_time', 'use_time','expire_at')
    list_display = ('mid', 'paid_time', 'max_time', 'use_time', 'expire_at', 'accum_time')
    ordering = ['-expire_at']

admin.site.register(Manager, ManagerAdmin)

class CodeShareAdmin(admin.ModelAdmin):
    #list_display = ('code', 'mid', 'interview_obj', 'expire_at')
    list_display = ('code', 'mid', 'interview_obj', 'expire_at', 'owner_list')

admin.site.register(CodeShare, CodeShareAdmin)


# Register your models here.
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'date_joined', 'last_login', 'email', 'is_staff') # Added last_login
    ordering = ['-date_joined']

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

#Register some others
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('type', 'amount', 'code', 'expire_at', 'user_count', 'used_count', 'owner_id', 'user_list', 'usable') # Added last_login
    ordering = ['-expire_at']

admin.site.register(Purchase, PurchaseAdmin)