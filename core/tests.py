from __future__ import annotations

from datetime import date
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import (
	Attendance,
	AttendanceStatus,
	Child,
	ChildStatus,
	Classroom,
	Guardian,
	MonthlyBilling,
	MonthlyBillingStatus,
	Tariff,
)


class ModelSmokeTests(TestCase):
	def test_can_create_models(self) -> None:
		classroom = Classroom.objects.create(name="Sunflowers", age_group="3-4", capacity=10)
		child = Child.objects.create(
			first_name="Emma",
			last_name="Smith",
			birth_date=date(2020, 1, 1),
			classroom=classroom,
			status=ChildStatus.ACTIVE,
		)
		guardian = Guardian.objects.create(
			first_name="Olivia",
			last_name="Smith",
			phone="+11234567890",
			email="olivia.smith@example.com",
			child=child,
			is_primary=True,
		)

		self.assertEqual(str(classroom), "Sunflowers")
		self.assertEqual(str(child), "Emma Smith")
		self.assertEqual(str(guardian), "Olivia Smith")


class ClassroomListViewTests(TestCase):
	def test_list_view_returns_200_when_logged_in(self) -> None:
		User = get_user_model()
		user = User.objects.create_user(username="testuser", password="testpass123")

		classroom = Classroom.objects.create(name="Rainbows", age_group="4-5", capacity=12)

		self.client.force_login(user)
		resp = self.client.get(reverse("core:classroom_list"))

		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, classroom.name)


class AttendanceTests(TestCase):
	def test_status_choices_include_expected_present_absent_late_half_day(self) -> None:
		values = {value for value, _label in AttendanceStatus.choices}
		self.assertIn(AttendanceStatus.EXPECTED, values)
		self.assertIn(AttendanceStatus.PRESENT, values)
		self.assertIn(AttendanceStatus.ABSENT, values)
		self.assertIn(AttendanceStatus.LATE, values)
		self.assertIn(AttendanceStatus.HALF_DAY, values)

	def test_list_view_autocreates_records_for_empty_date_when_logged_in(self) -> None:
		User = get_user_model()
		user = User.objects.create_user(username="attuser", password="testpass123")
		classroom = Classroom.objects.create(name="Stars", age_group="5-6", capacity=10)
		child = Child.objects.create(
			first_name="Ava",
			last_name="Davis",
			birth_date=date(2020, 1, 1),
			classroom=classroom,
			status=ChildStatus.ACTIVE,
		)

		self.assertEqual(Attendance.objects.count(), 0)

		self.client.force_login(user)
		resp = self.client.get(reverse("core:attendance_list"))

		self.assertEqual(resp.status_code, 200)
		self.assertTrue(Attendance.objects.filter(child=child).exists())
		self.assertContains(resp, child.last_name)


class MonthlyBillingTests(TestCase):
	def test_list_view_autocreates_rows_for_month(self) -> None:
		User = get_user_model()
		user = User.objects.create_user(username="mbuser", password="testpass123")

		classroom = Classroom.objects.create(name="MB", age_group="3-4", capacity=10)
		tariff = Tariff.objects.create(name="Standard", amount="500.00", is_active=True)
		child = Child.objects.create(
			first_name="Ava",
			last_name="Jones",
			birth_date=date(2020, 1, 1),
			classroom=classroom,
			tariff=tariff,
			status=ChildStatus.ACTIVE,
		)

		self.assertEqual(MonthlyBilling.objects.count(), 0)
		self.client.force_login(user)
		resp = self.client.get(reverse("core:billing_monthly_list"), {"month": "2025-12"})
		self.assertEqual(resp.status_code, 200)
		self.assertTrue(MonthlyBilling.objects.filter(child=child, billing_month="2025-12").exists())
		row = MonthlyBilling.objects.get(child=child, billing_month="2025-12")
		self.assertEqual(str(row.amount), "500.00")
		self.assertContains(resp, child.last_name)

	def test_mark_paid_uses_child_and_month(self) -> None:
		User = get_user_model()
		user = User.objects.create_user(username="mbuser2", password="testpass123")
		classroom = Classroom.objects.create(name="MB2", age_group="3-4", capacity=10)
		tariff = Tariff.objects.create(name="Premium", amount="600.00", is_active=True)
		child = Child.objects.create(
			first_name="Mason",
			last_name="Smith",
			birth_date=date(2020, 1, 1),
			classroom=classroom,
			tariff=tariff,
			status=ChildStatus.ACTIVE,
		)

		self.client.force_login(user)
		resp = self.client.post(
			reverse("core:billing_monthly_mark", kwargs={"status": "paid"}),
			{"child": str(child.pk), "month": "2025-12"},
		)
		self.assertEqual(resp.status_code, 302)
		row = MonthlyBilling.objects.get(child=child, billing_month="2025-12")
		self.assertEqual(str(row.amount), "600.00")
		self.assertEqual(row.status, MonthlyBillingStatus.PAID)
		self.assertIsNotNone(row.paid_at)

# Create your tests here.
