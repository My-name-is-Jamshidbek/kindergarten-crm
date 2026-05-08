from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from django.contrib.auth import authenticate
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
	Attendance,
	AttendanceStatus,
	Child,
	ChildStatus,
	Classroom,
	Guardian,
	KindergartenLocation,
	MonthlyBilling,
	MonthlyBillingStatus,
	Tariff,
)
from .roles import (
	ROLE_ACCOUNTANT,
	ROLE_ADMIN,
	ROLE_EDUCATOR,
	ROLE_LABELS,
	default_url_for_user,
	primary_role,
	user_has_role,
)


def _forbidden() -> Response:
	return Response({"detail": "Bu amal uchun ruxsat yo'q."}, status=status.HTTP_403_FORBIDDEN)


def _require_role(request, *roles: str) -> Response | None:
	if user_has_role(request.user, roles):
		return None
	return _forbidden()


def _require_educator(request) -> Response | None:
	if primary_role(request.user) == ROLE_EDUCATOR:
		return None
	return _forbidden()


def _parse_date(value: str | None):
	if not value:
		return timezone.localdate()
	try:
		return datetime.strptime(value, "%Y-%m-%d").date()
	except ValueError:
		return timezone.localdate()


def _parse_time(value: object):
	if value is None or value == "":
		return None
	if not isinstance(value, str):
		raise ValueError
	return datetime.strptime(value, "%H:%M").time()


def _parse_billing_month(value: str | None) -> str:
	if not value:
		return timezone.localdate().strftime("%Y-%m")
	val = value.strip()
	if len(val) == 10 and val[4] == "-" and val[7] == "-":
		val = val[:7]
	try:
		year = int(val[0:4])
		month = int(val[5:7])
	except Exception:
		return timezone.localdate().strftime("%Y-%m")
	if len(val) != 7 or val[4] != "-" or month < 1 or month > 12 or year < 1900:
		return timezone.localdate().strftime("%Y-%m")
	return val


def _money(value: Decimal | None) -> str:
	return str(value or Decimal("0"))


def serialize_user(user) -> dict[str, object]:
	role = primary_role(user)
	return {
		"id": user.pk,
		"username": user.get_username(),
		"role": role,
		"role_label": ROLE_LABELS.get(role, ""),
		"default_url": default_url_for_user(user),
		"is_superuser": user.is_superuser,
	}


def serialize_classroom(classroom: Classroom) -> dict[str, object]:
	return {
		"id": classroom.pk,
		"name": classroom.name,
		"age_group": classroom.age_group,
		"capacity": classroom.capacity,
	}


def serialize_tariff(tariff: Tariff | None) -> dict[str, object] | None:
	if tariff is None:
		return None
	return {
		"id": tariff.pk,
		"name": tariff.name,
		"amount": _money(tariff.amount),
		"is_active": tariff.is_active,
		"description": tariff.description,
	}


def serialize_child(child: Child) -> dict[str, object]:
	return {
		"id": child.pk,
		"first_name": child.first_name,
		"last_name": child.last_name,
		"full_name": str(child),
		"birth_date": child.birth_date.isoformat(),
		"age_years": child.age_years,
		"status": child.status,
		"status_label": child.get_status_display(),
		"classroom": serialize_classroom(child.classroom),
		"tariff": serialize_tariff(child.tariff),
	}


def serialize_guardian(guardian: Guardian) -> dict[str, object]:
	return {
		"id": guardian.pk,
		"first_name": guardian.first_name,
		"last_name": guardian.last_name,
		"full_name": str(guardian),
		"phone": guardian.phone,
		"email": guardian.email,
		"is_primary": guardian.is_primary,
		"child": {
			"id": guardian.child_id,
			"full_name": str(guardian.child),
			"classroom": guardian.child.classroom.name,
		},
	}


def serialize_attendance(row: Attendance) -> dict[str, object]:
	return {
		"id": row.pk,
		"date": row.attendance_date.isoformat(),
		"status": row.status,
		"status_label": row.get_status_display(),
		"check_in_time": row.check_in_time.isoformat(timespec="minutes") if row.check_in_time else None,
		"check_out_time": row.check_out_time.isoformat(timespec="minutes") if row.check_out_time else None,
		"absence_reason": row.absence_reason,
		"notes": row.notes,
		"child": serialize_child(row.child),
	}


def serialize_billing(row: MonthlyBilling) -> dict[str, object]:
	return {
		"id": row.pk,
		"billing_month": row.billing_month,
		"amount": _money(row.amount),
		"status": row.status,
		"status_label": row.get_status_display(),
		"paid_at": row.paid_at.isoformat() if row.paid_at else None,
		"notes": row.notes,
		"child": serialize_child(row.child),
	}


def serialize_location(location: KindergartenLocation) -> dict[str, object]:
	return {
		"name": location.name,
		"address": location.address,
		"latitude": str(location.latitude) if location.latitude is not None else None,
		"longitude": str(location.longitude) if location.longitude is not None else None,
		"has_coordinates": location.has_coordinates,
		"google_maps_url": location.google_maps_url,
		"openstreetmap_embed_url": location.openstreetmap_embed_url,
	}


class LoginAPIView(APIView):
	permission_classes = [AllowAny]

	def post(self, request) -> Response:
		username = (request.data.get("username") or "").strip()
		password = request.data.get("password") or ""
		user = authenticate(request, username=username, password=password)
		if user is None:
			return Response({"detail": "Login yoki parol noto'g'ri."}, status=status.HTTP_400_BAD_REQUEST)
		if not user.is_active:
			return Response({"detail": "Foydalanuvchi faol emas."}, status=status.HTTP_403_FORBIDDEN)
		if primary_role(user) != ROLE_EDUCATOR:
			return Response(
				{"detail": "Mobil ilova faqat tarbiyachi roli uchun."},
				status=status.HTTP_403_FORBIDDEN,
			)
		token, _created = Token.objects.get_or_create(user=user)
		return Response({"token": token.key, "user": serialize_user(user)})


class MeAPIView(APIView):
	def get(self, request) -> Response:
		denied = _require_educator(request)
		if denied:
			return denied
		return Response({"user": serialize_user(request.user)})


class DashboardAPIView(APIView):
	def get(self, request) -> Response:
		denied = _require_educator(request)
		if denied:
			return denied

		today = timezone.localdate()
		attendance_qs = Attendance.objects.filter(attendance_date=today)
		month = today.strftime("%Y-%m")
		billing_qs = MonthlyBilling.objects.filter(billing_month=month)
		return Response(
			{
				"role": ROLE_EDUCATOR,
				"attendance": {
					"date": today.isoformat(),
					"present": attendance_qs.filter(status=AttendanceStatus.PRESENT).count(),
					"late": attendance_qs.filter(status=AttendanceStatus.LATE).count(),
					"absent": attendance_qs.filter(status=AttendanceStatus.ABSENT).count(),
					"expected": attendance_qs.filter(status=AttendanceStatus.EXPECTED).count(),
				},
				"billing": {
					"month": month,
					"paid": billing_qs.filter(status=MonthlyBillingStatus.PAID).count(),
					"unpaid": billing_qs.filter(status=MonthlyBillingStatus.UNPAID).count(),
					"paid_amount": _money(
						billing_qs.filter(status=MonthlyBillingStatus.PAID).aggregate(total=models.Sum("amount"))["total"]
					),
					"unpaid_amount": _money(
						billing_qs.filter(status=MonthlyBillingStatus.UNPAID).aggregate(total=models.Sum("amount"))["total"]
					),
				},
				"counts": {
					"classrooms": Classroom.objects.count(),
					"active_children": Child.objects.filter(status=ChildStatus.ACTIVE).count(),
					"guardians": Guardian.objects.count(),
					"tariffs": Tariff.objects.count(),
				},
				"location": serialize_location(KindergartenLocation.get_solo()),
			}
		)


class ClassroomListAPIView(APIView):
	def get(self, request) -> Response:
		denied = _require_educator(request)
		if denied:
			return denied
		rows = Classroom.objects.all().order_by("name")
		return Response({"results": [serialize_classroom(row) for row in rows]})


class ChildListAPIView(APIView):
	def get(self, request) -> Response:
		denied = _require_role(request, ROLE_ADMIN)
		if denied:
			return denied
		rows = Child.objects.select_related("classroom", "tariff").order_by("last_name", "first_name")
		q = (request.query_params.get("q") or "").strip()
		if q:
			rows = rows.filter(models.Q(first_name__icontains=q) | models.Q(last_name__icontains=q))
		return Response({"results": [serialize_child(row) for row in rows]})


class GuardianListAPIView(APIView):
	def get(self, request) -> Response:
		denied = _require_educator(request)
		if denied:
			return denied
		rows = Guardian.objects.select_related("child", "child__classroom").order_by("last_name", "first_name")
		q = (request.query_params.get("q") or "").strip()
		if q:
			rows = rows.filter(
				models.Q(first_name__icontains=q)
				| models.Q(last_name__icontains=q)
				| models.Q(phone__icontains=q)
				| models.Q(email__icontains=q)
				| models.Q(child__first_name__icontains=q)
				| models.Q(child__last_name__icontains=q)
			)
		return Response({"results": [serialize_guardian(row) for row in rows]})


class TariffListAPIView(APIView):
	def get(self, request) -> Response:
		denied = _require_role(request, ROLE_ADMIN, ROLE_ACCOUNTANT)
		if denied:
			return denied
		rows = Tariff.objects.all().order_by("-is_active", "name")
		return Response({"results": [serialize_tariff(row) for row in rows]})


class AttendanceListAPIView(APIView):
	def get(self, request) -> Response:
		denied = _require_educator(request)
		if denied:
			return denied

		attendance_date = _parse_date(request.query_params.get("date"))
		if not Attendance.objects.filter(attendance_date=attendance_date).exists():
			active_children = Child.objects.filter(status=ChildStatus.ACTIVE)
			Attendance.objects.bulk_create(
				[
					Attendance(child=child, attendance_date=attendance_date, status=AttendanceStatus.EXPECTED)
					for child in active_children
				],
				ignore_conflicts=True,
			)

		rows = Attendance.objects.select_related("child", "child__classroom", "child__tariff").filter(
			attendance_date=attendance_date
		)
		classroom = (request.query_params.get("classroom") or "").strip()
		if classroom:
			rows = rows.filter(child__classroom_id=classroom)
		row_status = (request.query_params.get("status") or "").strip()
		if row_status:
			rows = rows.filter(status=row_status)
		q = (request.query_params.get("q") or "").strip()
		if q:
			rows = rows.filter(models.Q(child__first_name__icontains=q) | models.Q(child__last_name__icontains=q))
		rows = rows.order_by("child__last_name", "child__first_name")

		base_qs = Attendance.objects.filter(attendance_date=attendance_date)
		return Response(
			{
				"date": attendance_date.isoformat(),
				"summary": {
					"present": base_qs.filter(status=AttendanceStatus.PRESENT).count(),
					"late": base_qs.filter(status=AttendanceStatus.LATE).count(),
					"absent": base_qs.filter(status=AttendanceStatus.ABSENT).count(),
					"expected": base_qs.filter(status=AttendanceStatus.EXPECTED).count(),
				},
				"statuses": [{"value": value, "label": label} for value, label in AttendanceStatus.choices],
				"results": [serialize_attendance(row) for row in rows],
			}
		)


class AttendanceMarkAPIView(APIView):
	def post(self, request, pk: int) -> Response:
		denied = _require_educator(request)
		if denied:
			return denied
		row_status = (request.data.get("status") or "").strip()
		if row_status not in {value for value, _label in AttendanceStatus.choices}:
			return Response({"detail": "Noto'g'ri holat."}, status=status.HTTP_400_BAD_REQUEST)
		row = get_object_or_404(Attendance.objects.select_related("child", "child__classroom", "child__tariff"), pk=pk)
		row.status = row_status
		row.save(update_fields=["status", "updated_at"])
		return Response({"attendance": serialize_attendance(row)})


class AttendanceUpdateAPIView(APIView):
	def patch(self, request, pk: int) -> Response:
		denied = _require_educator(request)
		if denied:
			return denied
		row = get_object_or_404(Attendance.objects.select_related("child", "child__classroom", "child__tariff"), pk=pk)

		row_status = (request.data.get("status") or row.status).strip()
		if row_status not in {value for value, _label in AttendanceStatus.choices}:
			return Response({"detail": "Noto'g'ri holat."}, status=status.HTTP_400_BAD_REQUEST)

		try:
			check_in = _parse_time(request.data.get("check_in_time")) if "check_in_time" in request.data else row.check_in_time
			check_out = _parse_time(request.data.get("check_out_time")) if "check_out_time" in request.data else row.check_out_time
		except ValueError:
			return Response({"detail": "Vaqt HH:MM formatida bo'lishi kerak."}, status=status.HTTP_400_BAD_REQUEST)

		absence_reason = request.data.get("absence_reason", row.absence_reason)
		notes = request.data.get("notes", row.notes)
		absence_reason = "" if absence_reason is None else str(absence_reason).strip()
		notes = "" if notes is None else str(notes).strip()

		if check_in and check_out and check_out < check_in:
			return Response({"detail": "Chiqish vaqti kirish vaqtidan keyin bo'lishi kerak."}, status=status.HTTP_400_BAD_REQUEST)
		if row_status == AttendanceStatus.ABSENT and not absence_reason:
			return Response({"detail": "Kelmagan holati uchun sabab kiriting."}, status=status.HTTP_400_BAD_REQUEST)

		row.status = row_status
		row.check_in_time = check_in
		row.check_out_time = check_out
		row.absence_reason = absence_reason
		row.notes = notes
		row.save(
			update_fields=[
				"status",
				"check_in_time",
				"check_out_time",
				"absence_reason",
				"notes",
				"updated_at",
			]
		)
		return Response({"attendance": serialize_attendance(row)})


class AttendanceBulkMarkPresentAPIView(APIView):
	def post(self, request) -> Response:
		denied = _require_educator(request)
		if denied:
			return denied
		attendance_date = _parse_date(request.data.get("date"))
		classroom_id = (request.data.get("classroom") or "").strip()
		if not classroom_id:
			return Response({"detail": "Guruh tanlanmadi."}, status=status.HTTP_400_BAD_REQUEST)

		children = Child.objects.filter(status=ChildStatus.ACTIVE, classroom_id=classroom_id)
		if not children.exists():
			return Response({"updated": 0, "detail": "Tanlangan guruhda faol bolalar yo'q."})

		Attendance.objects.bulk_create(
			[
				Attendance(child=child, attendance_date=attendance_date, status=AttendanceStatus.EXPECTED)
				for child in children
			],
			ignore_conflicts=True,
		)
		updated = Attendance.objects.filter(attendance_date=attendance_date, child__in=children).update(
			status=AttendanceStatus.PRESENT
		)
		return Response({"updated": updated, "date": attendance_date.isoformat(), "classroom": classroom_id})


class MonthlyBillingListAPIView(APIView):
	def get(self, request) -> Response:
		denied = _require_role(request, ROLE_ADMIN, ROLE_ACCOUNTANT)
		if denied:
			return denied
		billing_month = _parse_billing_month(request.query_params.get("month"))
		active_children = Child.objects.filter(status=ChildStatus.ACTIVE).select_related("tariff")
		existing = set(
			MonthlyBilling.objects.filter(billing_month=billing_month).values_list("child_id", flat=True)
		)
		to_create = []
		for child in active_children:
			if child.pk in existing:
				continue
			to_create.append(
				MonthlyBilling(
					child=child,
					billing_month=billing_month,
					amount=child.tariff.amount if child.tariff else Decimal("0"),
					status=MonthlyBillingStatus.UNPAID,
				)
			)
		if to_create:
			MonthlyBilling.objects.bulk_create(to_create, ignore_conflicts=True)

		rows = MonthlyBilling.objects.select_related("child", "child__classroom", "child__tariff").filter(
			billing_month=billing_month
		)
		classroom = (request.query_params.get("classroom") or "").strip()
		if classroom:
			rows = rows.filter(child__classroom_id=classroom)
		row_status = (request.query_params.get("status") or "").strip()
		if row_status:
			rows = rows.filter(status=row_status)
		rows = rows.order_by("child__last_name", "child__first_name")

		base_qs = MonthlyBilling.objects.filter(billing_month=billing_month)
		return Response(
			{
				"month": billing_month,
				"summary": {
					"paid": base_qs.filter(status=MonthlyBillingStatus.PAID).count(),
					"unpaid": base_qs.filter(status=MonthlyBillingStatus.UNPAID).count(),
				},
				"statuses": [{"value": value, "label": label} for value, label in MonthlyBillingStatus.choices],
				"results": [serialize_billing(row) for row in rows],
			}
		)


class MonthlyBillingMarkAPIView(APIView):
	def post(self, request) -> Response:
		denied = _require_role(request, ROLE_ADMIN, ROLE_ACCOUNTANT)
		if denied:
			return denied
		row_status = (request.data.get("status") or "").strip()
		if row_status not in {MonthlyBillingStatus.PAID, MonthlyBillingStatus.UNPAID}:
			return Response({"detail": "Noto'g'ri holat."}, status=status.HTTP_400_BAD_REQUEST)
		child_id = request.data.get("child")
		if not child_id:
			return Response({"detail": "Bola tanlanmadi."}, status=status.HTTP_400_BAD_REQUEST)
		month = _parse_billing_month(request.data.get("month"))
		child = get_object_or_404(Child.objects.select_related("tariff"), pk=child_id)
		row, _created = MonthlyBilling.objects.get_or_create(
			child=child,
			billing_month=month,
			defaults={
				"amount": child.tariff.amount if child.tariff else Decimal("0"),
				"status": MonthlyBillingStatus.UNPAID,
			},
		)
		if row_status == MonthlyBillingStatus.PAID:
			row.mark_paid()
		else:
			row.mark_unpaid()
		row = MonthlyBilling.objects.select_related("child", "child__classroom", "child__tariff").get(pk=row.pk)
		return Response({"billing": serialize_billing(row)})


class LocationAPIView(APIView):
	def get(self, request) -> Response:
		return Response({"location": serialize_location(KindergartenLocation.get_solo())})
