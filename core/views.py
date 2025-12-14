from __future__ import annotations

from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from datetime import date

from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from .forms import (
	AttendanceForm,
	ChildForm,
	ClassroomForm,
	GuardianForm,
	SearchQuery,
	child_search_filter,
	classroom_search_filter,
)
from .models import Attendance, AttendanceStatus, Child, ChildStatus, Classroom, Guardian


class PageTitleMixin:
	page_title: str | None = None

	def get_page_title(self) -> str:
		if self.page_title:
			return self.page_title
		model = getattr(self, "model", None)
		if model is None:
			return "Form"
		return str(model._meta.verbose_name).title()

	def get_context_data(self, **kwargs: object) -> dict[str, object]:
		ctx = super().get_context_data(**kwargs)
		ctx["page_title"] = self.get_page_title()
		return ctx


class HomeView(TemplateView):
	template_name = "core/home.html"


class ClassroomListView(LoginRequiredMixin, ListView):
	model = Classroom
	template_name = "core/classroom_list.html"
	context_object_name = "classrooms"
	paginate_by = 10

	def get_queryset(self) -> QuerySet[Classroom]:
		qs: QuerySet[Classroom] = Classroom.objects.all().order_by("name")
		search = SearchQuery.from_request(self.request)
		if search.q:
			qs = qs.filter(classroom_search_filter(search.q))
		return qs

	def get_context_data(self, **kwargs: object) -> dict[str, object]:
		ctx = super().get_context_data(**kwargs)
		ctx["q"] = (self.request.GET.get("q") or "").strip()
		return ctx


class ClassroomCreateView(LoginRequiredMixin, PageTitleMixin, CreateView):
	model = Classroom
	form_class = ClassroomForm
	template_name = "core/form.html"
	success_url = reverse_lazy("core:classroom_list")
	page_title = "Create classroom"

	def form_valid(self, form: ClassroomForm) -> HttpResponse:
		response = super().form_valid(form)
		messages.success(self.request, "Classroom created.")
		return response


class ClassroomUpdateView(LoginRequiredMixin, PageTitleMixin, UpdateView):
	model = Classroom
	form_class = ClassroomForm
	template_name = "core/form.html"
	success_url = reverse_lazy("core:classroom_list")
	page_title = "Edit classroom"

	def form_valid(self, form: ClassroomForm) -> HttpResponse:
		response = super().form_valid(form)
		messages.success(self.request, "Classroom updated.")
		return response


class ClassroomDeleteView(LoginRequiredMixin, DeleteView):
	model = Classroom
	template_name = "core/confirm_delete.html"
	success_url = reverse_lazy("core:classroom_list")

	def form_valid(self, form: object) -> HttpResponse:
		messages.success(self.request, "Classroom deleted.")
		return super().form_valid(form)


class ChildListView(LoginRequiredMixin, ListView):
	model = Child
	template_name = "core/child_list.html"
	context_object_name = "children"
	paginate_by = 10

	def get_queryset(self) -> QuerySet[Child]:
		qs: QuerySet[Child] = Child.objects.select_related("classroom").all()
		search = SearchQuery.from_request(self.request)
		if search.q:
			qs = qs.filter(child_search_filter(search.q))
		return qs.order_by("last_name", "first_name")

	def get_context_data(self, **kwargs: object) -> dict[str, object]:
		ctx = super().get_context_data(**kwargs)
		ctx["q"] = (self.request.GET.get("q") or "").strip()
		return ctx


class ChildCreateView(LoginRequiredMixin, PageTitleMixin, CreateView):
	model = Child
	form_class = ChildForm
	template_name = "core/form.html"
	success_url = reverse_lazy("core:child_list")
	page_title = "Register child"

	def form_valid(self, form: ChildForm) -> HttpResponse:
		response = super().form_valid(form)
		messages.success(self.request, "Child created.")
		return response


class ChildUpdateView(LoginRequiredMixin, PageTitleMixin, UpdateView):
	model = Child
	form_class = ChildForm
	template_name = "core/form.html"
	success_url = reverse_lazy("core:child_list")
	page_title = "Edit child"

	def form_valid(self, form: ChildForm) -> HttpResponse:
		response = super().form_valid(form)
		messages.success(self.request, "Child updated.")
		return response


class ChildDeleteView(LoginRequiredMixin, DeleteView):
	model = Child
	template_name = "core/confirm_delete.html"
	success_url = reverse_lazy("core:child_list")

	def form_valid(self, form: object) -> HttpResponse:
		messages.success(self.request, "Child deleted.")
		return super().form_valid(form)


class GuardianListView(LoginRequiredMixin, ListView):
	model = Guardian
	template_name = "core/guardian_list.html"
	context_object_name = "guardians"
	paginate_by = 10

	def get_queryset(self) -> QuerySet[Guardian]:
		return Guardian.objects.select_related("child", "child__classroom").order_by(
			"last_name", "first_name"
		)


class GuardianCreateView(LoginRequiredMixin, PageTitleMixin, CreateView):
	model = Guardian
	form_class = GuardianForm
	template_name = "core/form.html"
	success_url = reverse_lazy("core:guardian_list")
	page_title = "Add guardian"

	def form_valid(self, form: GuardianForm) -> HttpResponse:
		response = super().form_valid(form)
		messages.success(self.request, "Guardian created.")
		return response


class GuardianUpdateView(LoginRequiredMixin, PageTitleMixin, UpdateView):
	model = Guardian
	form_class = GuardianForm
	template_name = "core/form.html"
	success_url = reverse_lazy("core:guardian_list")
	page_title = "Edit guardian"

	def form_valid(self, form: GuardianForm) -> HttpResponse:
		response = super().form_valid(form)
		messages.success(self.request, "Guardian updated.")
		return response


class GuardianDeleteView(LoginRequiredMixin, DeleteView):
	model = Guardian
	template_name = "core/confirm_delete.html"
	success_url = reverse_lazy("core:guardian_list")

	def form_valid(self, form: object) -> HttpResponse:
		messages.success(self.request, "Guardian deleted.")
		return super().form_valid(form)


def _parse_date(value: str | None) -> date:
	if not value:
		return timezone.localdate()
	try:
		return datetime.strptime(value, "%Y-%m-%d").date()
	except ValueError:
		return timezone.localdate()


class AttendanceListView(LoginRequiredMixin, ListView):
	model = Attendance
	template_name = "core/attendance_list.html"
	context_object_name = "attendances"
	paginate_by = 25

	def dispatch(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
		self.attendance_date = _parse_date(request.GET.get("date"))
		return super().dispatch(request, *args, **kwargs)

	def _auto_create_expected_if_empty(self) -> None:
		if Attendance.objects.filter(attendance_date=self.attendance_date).exists():
			return
		active_children = Child.objects.filter(status=ChildStatus.ACTIVE)
		Attendance.objects.bulk_create(
			[
				Attendance(child=child, attendance_date=self.attendance_date, status=AttendanceStatus.EXPECTED)
				for child in active_children
			],
			ignore_conflicts=True,
		)

	def get_queryset(self) -> QuerySet[Attendance]:
		self._auto_create_expected_if_empty()

		qs: QuerySet[Attendance] = Attendance.objects.select_related(
			"child", "child__classroom"
		).filter(attendance_date=self.attendance_date)

		q = (self.request.GET.get("q") or "").strip()
		if q:
			qs = qs.filter(child_search_filter(q))

		classroom_id = (self.request.GET.get("classroom") or "").strip()
		if classroom_id:
			qs = qs.filter(child__classroom_id=classroom_id)

		status = (self.request.GET.get("status") or "").strip()
		if status:
			qs = qs.filter(status=status)

		return qs.order_by("child__last_name", "child__first_name")

	def get_context_data(self, **kwargs: object) -> dict[str, object]:
		ctx = super().get_context_data(**kwargs)
		ctx["page_title"] = "Attendance"
		ctx["date"] = self.attendance_date
		ctx["q"] = (self.request.GET.get("q") or "").strip()
		ctx["classrooms"] = Classroom.objects.all().order_by("name")
		ctx["selected_classroom"] = (self.request.GET.get("classroom") or "").strip()
		ctx["selected_status"] = (self.request.GET.get("status") or "").strip()
		ctx["statuses"] = AttendanceStatus.choices

		base_qs = Attendance.objects.filter(attendance_date=self.attendance_date)
		ctx["count_present"] = base_qs.filter(status=AttendanceStatus.PRESENT).count()
		ctx["count_late"] = base_qs.filter(status=AttendanceStatus.LATE).count()
		ctx["count_absent"] = base_qs.filter(status=AttendanceStatus.ABSENT).count()
		ctx["count_not_marked"] = base_qs.filter(status=AttendanceStatus.EXPECTED).count()
		return ctx


class AttendanceUpdateView(LoginRequiredMixin, PageTitleMixin, UpdateView):
	model = Attendance
	form_class = AttendanceForm
	template_name = "core/attendance_form.html"
	page_title = "Edit attendance"

	def get_success_url(self) -> str:
		date_str = self.object.attendance_date.strftime("%Y-%m-%d")
		return f"{reverse_lazy('core:attendance_list')}?date={date_str}"

	def form_valid(self, form: AttendanceForm) -> HttpResponse:
		response = super().form_valid(form)
		messages.success(self.request, "Attendance updated.")
		return response


class AttendanceQuickMarkView(LoginRequiredMixin, View):
	allowed = {
		AttendanceStatus.PRESENT,
		AttendanceStatus.ABSENT,
		AttendanceStatus.LATE,
		AttendanceStatus.HALF_DAY,
		AttendanceStatus.EXPECTED,
	}

	def post(self, request: HttpRequest, pk: int, status: str) -> HttpResponse:
		if status not in self.allowed:
			return HttpResponseBadRequest("Invalid status")
		try:
			attendance = Attendance.objects.select_related("child").get(pk=pk)
		except Attendance.DoesNotExist:
			return HttpResponseBadRequest("Attendance not found")

		attendance.status = status
		attendance.save(update_fields=["status", "updated_at"])
		messages.success(request, f"Marked {attendance.child} as {attendance.get_status_display()}.")

		date_str = attendance.attendance_date.strftime("%Y-%m-%d")
		return_url = request.META.get("HTTP_REFERER") or f"{reverse_lazy('core:attendance_list')}?date={date_str}"
		return HttpResponseRedirect(return_url)


class AttendanceSetTimeView(LoginRequiredMixin, View):
	def post(self, request: HttpRequest, pk: int, field: str) -> HttpResponse:
		if field not in {"check_in_time", "check_out_time"}:
			return HttpResponseBadRequest("Invalid field")
		value = (request.POST.get("time") or "").strip()
		if not value:
			return HttpResponseBadRequest("Missing time")
		try:
			time_value = datetime.strptime(value, "%H:%M").time()
		except ValueError:
			return HttpResponseBadRequest("Invalid time")

		attendance = Attendance.objects.get(pk=pk)
		setattr(attendance, field, time_value)
		attendance.save(update_fields=[field, "updated_at"])
		messages.success(request, "Time updated.")
		date_str = attendance.attendance_date.strftime("%Y-%m-%d")
		return_url = request.META.get("HTTP_REFERER") or f"{reverse_lazy('core:attendance_list')}?date={date_str}"
		return HttpResponseRedirect(return_url)


class AttendanceBulkMarkPresentView(LoginRequiredMixin, View):
	def post(self, request: HttpRequest) -> HttpResponse:
		date_val = _parse_date(request.POST.get("date"))
		classroom_id = (request.POST.get("classroom") or "").strip()
		if not classroom_id:
			return HttpResponseBadRequest("Missing classroom")

		children = Child.objects.filter(status=ChildStatus.ACTIVE, classroom_id=classroom_id)
		if not children.exists():
			messages.info(request, "No active children in that classroom.")
			return HttpResponseRedirect(
				f"{reverse_lazy('core:attendance_list')}?date={date_val.strftime('%Y-%m-%d')}&classroom={classroom_id}"
			)

		# Ensure records exist, then mark Present.
		Attendance.objects.bulk_create(
			[
				Attendance(child=child, attendance_date=date_val, status=AttendanceStatus.EXPECTED)
				for child in children
			],
			ignore_conflicts=True,
		)
		Attendance.objects.filter(attendance_date=date_val, child__in=children).update(
			status=AttendanceStatus.PRESENT
		)
		messages.success(request, "Marked classroom as present.")
		return HttpResponseRedirect(
			f"{reverse_lazy('core:attendance_list')}?date={date_val.strftime('%Y-%m-%d')}&classroom={classroom_id}"
		)

# Create your views here.
