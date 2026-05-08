from __future__ import annotations

from django.urls import path

from . import api

app_name = "api"

urlpatterns = [
	path("auth/login/", api.LoginAPIView.as_view(), name="login"),
	path("auth/me/", api.MeAPIView.as_view(), name="me"),
	path("dashboard/", api.DashboardAPIView.as_view(), name="dashboard"),
	path("classrooms/", api.ClassroomListAPIView.as_view(), name="classroom_list"),
	path("children/", api.ChildListAPIView.as_view(), name="child_list"),
	path("guardians/", api.GuardianListAPIView.as_view(), name="guardian_list"),
	path("tariffs/", api.TariffListAPIView.as_view(), name="tariff_list"),
	path("attendance/", api.AttendanceListAPIView.as_view(), name="attendance_list"),
	path("attendance/bulk/mark-present/", api.AttendanceBulkMarkPresentAPIView.as_view(), name="attendance_bulk_mark_present"),
	path("attendance/<int:pk>/", api.AttendanceUpdateAPIView.as_view(), name="attendance_update"),
	path("attendance/<int:pk>/mark/", api.AttendanceMarkAPIView.as_view(), name="attendance_mark"),
	path("billing/monthly/", api.MonthlyBillingListAPIView.as_view(), name="billing_monthly_list"),
	path("billing/monthly/mark/", api.MonthlyBillingMarkAPIView.as_view(), name="billing_monthly_mark"),
	path("location/", api.LocationAPIView.as_view(), name="location"),
]
