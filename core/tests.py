from __future__ import annotations

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Attendance, AttendanceStatus, Child, ChildStatus, Classroom, Guardian


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

# Create your tests here.
