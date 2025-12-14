from __future__ import annotations

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True


class Classroom(TimeStampedModel):
	name = models.CharField(max_length=120, unique=True)
	age_group = models.CharField(max_length=50)
	capacity = models.PositiveIntegerField()

	class Meta:
		ordering = ["name"]

	def __str__(self) -> str:
		return self.name


class ChildStatus(models.TextChoices):
	ACTIVE = "active", "Active"
	INACTIVE = "inactive", "Inactive"


class Child(TimeStampedModel):
	first_name = models.CharField(max_length=80)
	last_name = models.CharField(max_length=80)
	birth_date = models.DateField()
	classroom = models.ForeignKey(
		Classroom,
		on_delete=models.PROTECT,
		related_name="children",
	)
	status = models.CharField(
		max_length=10,
		choices=ChildStatus.choices,
		default=ChildStatus.ACTIVE,
	)

	class Meta:
		ordering = ["last_name", "first_name"]

	def __str__(self) -> str:
		return f"{self.first_name} {self.last_name}"

	@property
	def age_years(self) -> int:
		today = timezone.localdate()
		years = today.year - self.birth_date.year
		if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
			years -= 1
		return max(years, 0)


class Guardian(TimeStampedModel):
	first_name = models.CharField(max_length=80)
	last_name = models.CharField(max_length=80)
	phone = models.CharField(max_length=30)
	email = models.EmailField()
	child = models.ForeignKey(
		Child,
		on_delete=models.CASCADE,
		related_name="guardians",
	)
	is_primary = models.BooleanField(default=False)

	class Meta:
		ordering = ["last_name", "first_name"]

	def __str__(self) -> str:
		return f"{self.first_name} {self.last_name}"


class AttendanceStatus(models.TextChoices):
	EXPECTED = "expected", "Expected"
	PRESENT = "present", "Present"
	ABSENT = "absent", "Absent"
	LATE = "late", "Late"
	HALF_DAY = "half_day", "Half-day"


class Attendance(TimeStampedModel):
	child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="attendance")
	attendance_date = models.DateField(default=timezone.localdate)
	status = models.CharField(
		max_length=10,
		choices=AttendanceStatus.choices,
		default=AttendanceStatus.EXPECTED,
	)
	check_in_time = models.TimeField(blank=True, null=True)
	check_out_time = models.TimeField(blank=True, null=True)
	absence_reason = models.TextField(blank=True)
	notes = models.TextField(blank=True)

	class Meta:
		ordering = ["-attendance_date", "child__last_name", "child__first_name"]
		constraints = [
			models.UniqueConstraint(
				fields=["child", "attendance_date"], name="uniq_attendance_child_date"
			)
		]
		indexes = [
			models.Index(fields=["attendance_date", "status"]),
		]

	def __str__(self) -> str:
		return f"{self.child} · {self.attendance_date}"


class AuthorizedPickup(TimeStampedModel):
	child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="authorized_pickups")
	full_name = models.CharField(max_length=160)
	relationship = models.CharField(max_length=80)
	phone = models.CharField(max_length=30)
	id_document_number = models.CharField(max_length=80, blank=True)
	is_active = models.BooleanField(default=True)
	valid_from = models.DateField(blank=True, null=True)
	valid_until = models.DateField(blank=True, null=True)

	class Meta:
		ordering = ["-is_active", "full_name"]

	def __str__(self) -> str:
		return f"{self.full_name} ({self.child})"

# Create your models here.
