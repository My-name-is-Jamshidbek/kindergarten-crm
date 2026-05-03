from __future__ import annotations

from decimal import Decimal
import re
from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
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


class KindergartenLocation(TimeStampedModel):
	name = models.CharField(max_length=120, default="Anvar Bog'cha")
	address = models.CharField(max_length=255, blank=True)
	latitude = models.DecimalField(
		max_digits=9,
		decimal_places=6,
		blank=True,
		null=True,
		validators=[MinValueValidator(-90), MaxValueValidator(90)],
	)
	longitude = models.DecimalField(
		max_digits=9,
		decimal_places=6,
		blank=True,
		null=True,
		validators=[MinValueValidator(-180), MaxValueValidator(180)],
	)

	class Meta:
		verbose_name = "Kindergarten location"
		verbose_name_plural = "Kindergarten location"

	def __str__(self) -> str:
		return self.name

	@classmethod
	def get_solo(cls) -> "KindergartenLocation":
		location, _created = cls.objects.get_or_create(pk=1)
		return location

	@property
	def has_coordinates(self) -> bool:
		return self.latitude is not None and self.longitude is not None

	@property
	def coordinates_display(self) -> str:
		if not self.has_coordinates:
			return ""
		return f"{self.latitude}, {self.longitude}"

	@property
	def google_maps_url(self) -> str:
		if not self.has_coordinates:
			return ""
		return f"https://www.google.com/maps/search/?api=1&query={self.latitude},{self.longitude}"

	@property
	def openstreetmap_embed_url(self) -> str:
		if not self.has_coordinates:
			return ""
		lat = float(self.latitude)
		lng = float(self.longitude)
		bbox = f"{lng - 0.01:.6f}%2C{lat - 0.006:.6f}%2C{lng + 0.01:.6f}%2C{lat + 0.006:.6f}"
		return f"https://www.openstreetmap.org/export/embed.html?bbox={bbox}&layer=mapnik&marker={lat:.6f}%2C{lng:.6f}"


class ChildStatus(models.TextChoices):
	ACTIVE = "active", "Faol"
	INACTIVE = "inactive", "Nofaol"


class Tariff(TimeStampedModel):
	name = models.CharField(max_length=120, unique=True)
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	is_active = models.BooleanField(default=True)
	description = models.TextField(blank=True)

	class Meta:
		ordering = ["-is_active", "name"]

	def __str__(self) -> str:
		return f"{self.name} ({self.amount})"


class Child(TimeStampedModel):
	first_name = models.CharField(max_length=80)
	last_name = models.CharField(max_length=80)
	birth_date = models.DateField()
	classroom = models.ForeignKey(
		Classroom,
		on_delete=models.PROTECT,
		related_name="children",
	)
	tariff = models.ForeignKey(
		Tariff,
		on_delete=models.SET_NULL,
		related_name="children",
		blank=True,
		null=True,
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
	EXPECTED = "expected", "Kutilmoqda"
	PRESENT = "present", "Keldi"
	ABSENT = "absent", "Kelmagan"
	LATE = "late", "Kechikdi"
	HALF_DAY = "half_day", "Yarim kun"


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
def _validate_billing_month(value: str | None) -> None:
	if not value:
		return
	if not re.match(r"^\d{4}-\d{2}$", value):
		raise ValidationError("Billing month must be in YYYY-MM format.")
	month = int(value[5:7])
	if month < 1 or month > 12:
		raise ValidationError("Billing month must be in YYYY-MM format.")


def current_billing_month() -> str:
	return timezone.localdate().strftime("%Y-%m")


class MonthlyBillingStatus(models.TextChoices):
	UNPAID = "unpaid", "To‘lanmagan"
	PAID = "paid", "To‘langan"


class MonthlyBilling(TimeStampedModel):
	"""Simplified billing (attendance-style): one row per child per month."""
	child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="monthly_billing")
	billing_month = models.CharField(max_length=7, default=current_billing_month, validators=[_validate_billing_month])
	amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
	status = models.CharField(
		max_length=10,
		choices=MonthlyBillingStatus.choices,
		default=MonthlyBillingStatus.UNPAID,
	)
	paid_at = models.DateTimeField(blank=True, null=True)
	notes = models.TextField(blank=True)

	class Meta:
		ordering = ["-billing_month", "child__last_name", "child__first_name"]
		constraints = [
			models.UniqueConstraint(
				fields=["child", "billing_month"],
				name="uniq_monthly_billing_child_month",
			),
		]
		indexes = [
			models.Index(fields=["billing_month", "status"]),
		]

	def __str__(self) -> str:
		return f"{self.child} · {self.billing_month}"

	@property
	def badge_class(self) -> str:
		return "success" if self.status == MonthlyBillingStatus.PAID else "secondary"

	def mark_paid(self) -> None:
		self.status = MonthlyBillingStatus.PAID
		self.paid_at = timezone.now()
		self.save(update_fields=["status", "paid_at", "updated_at"])

	def mark_unpaid(self) -> None:
		self.status = MonthlyBillingStatus.UNPAID
		self.paid_at = None
		self.save(update_fields=["status", "paid_at", "updated_at"])
