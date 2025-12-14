from __future__ import annotations

from django.contrib import admin

from .models import (
	Attendance,
	AuthorizedPickup,
	Child,
	Classroom,
	Guardian,
	Tariff,
	MonthlyBilling,
)


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
	list_display = ("name", "amount", "is_active", "created_at", "updated_at")
	search_fields = ("name", "description")
	list_filter = ("is_active",)


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
	list_display = ("name", "age_group", "capacity", "created_at", "updated_at")
	search_fields = ("name", "age_group")
	list_filter = ("age_group",)


@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
	list_display = (
		"first_name",
		"last_name",
		"birth_date",
		"classroom",
		"tariff",
		"status",
		"created_at",
		"updated_at",
	)
	search_fields = ("first_name", "last_name")
	list_filter = ("status", "classroom", "tariff")


@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
	list_display = (
		"first_name",
		"last_name",
		"child",
		"phone",
		"email",
		"is_primary",
		"created_at",
		"updated_at",
	)
	search_fields = ("first_name", "last_name", "email", "phone", "child__first_name", "child__last_name")
	list_filter = ("is_primary",)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
	list_display = (
		"child",
		"attendance_date",
		"status",
		"check_in_time",
		"check_out_time",
	)
	search_fields = ("child__first_name", "child__last_name")
	list_filter = ("attendance_date", "status", "child__classroom")
	date_hierarchy = "attendance_date"


@admin.register(AuthorizedPickup)
class AuthorizedPickupAdmin(admin.ModelAdmin):
	list_display = (
		"full_name",
		"child",
		"relationship",
		"phone",
		"is_active",
		"valid_from",
		"valid_until",
	)
	search_fields = ("full_name", "phone", "id_document_number", "child__first_name", "child__last_name")
	list_filter = ("is_active", "relationship")


@admin.register(MonthlyBilling)
class MonthlyBillingAdmin(admin.ModelAdmin):
	list_display = (
		"child",
		"billing_month",
		"amount",
		"status",
		"paid_at",
		"created_at",
		"updated_at",
	)
	search_fields = ("child__first_name", "child__last_name")
	list_filter = ("billing_month", "status", "child__classroom", "child__tariff")

# Register your models here.
