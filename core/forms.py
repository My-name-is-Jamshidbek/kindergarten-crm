from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from .models import Attendance, AttendanceStatus, Child, Classroom, Guardian


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ["name", "age_group", "capacity"]


class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ["first_name", "last_name", "birth_date", "classroom", "status"]
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_birth_date(self) -> date:
        birth_date: date = self.cleaned_data["birth_date"]
        if birth_date > timezone.localdate():
            raise ValidationError("Birth date cannot be in the future.")
        return birth_date

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean()
        classroom: Classroom | None = cleaned.get("classroom")
        if not classroom:
            return cleaned

        qs = Child.objects.filter(classroom=classroom)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.count() >= classroom.capacity:
            raise ValidationError(
                {"classroom": f"{classroom.name} is at full capacity ({classroom.capacity})."}
            )

        return cleaned


class GuardianForm(forms.ModelForm):
    class Meta:
        model = Guardian
        fields = ["first_name", "last_name", "phone", "email", "child", "is_primary"]

    def clean_phone(self) -> str:
        phone: str = self.cleaned_data["phone"]
        compact = "".join(ch for ch in phone if ch.isdigit() or ch == "+")
        if len([ch for ch in compact if ch.isdigit()]) < 7:
            raise ValidationError("Enter a valid phone number.")
        return phone

    def save(self, commit: bool = True) -> Guardian:
        guardian: Guardian = super().save(commit=commit)
        if guardian.is_primary:
            Guardian.objects.filter(child=guardian.child).exclude(pk=guardian.pk).update(
                is_primary=False
            )
        return guardian


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = [
            "attendance_date",
            "status",
            "check_in_time",
            "check_out_time",
            "absence_reason",
            "notes",
        ]
        widgets = {
            "attendance_date": forms.DateInput(attrs={"type": "date"}),
            "check_in_time": forms.TimeInput(attrs={"type": "time"}),
            "check_out_time": forms.TimeInput(attrs={"type": "time"}),
            "absence_reason": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean()
        status = cleaned.get("status")
        check_in = cleaned.get("check_in_time")
        check_out = cleaned.get("check_out_time")
        reason = (cleaned.get("absence_reason") or "").strip()

        if check_in and check_out and check_out < check_in:
            raise ValidationError({"check_out_time": "Check-out must be after check-in."})

        if status == AttendanceStatus.ABSENT and not reason:
            raise ValidationError({"absence_reason": "Please provide an absence reason."})

        return cleaned


@dataclass(frozen=True)
class SearchQuery:
    q: str

    @classmethod
    def from_request(cls, request: Any) -> "SearchQuery":
        raw = (request.GET.get("q") or "").strip()
        return cls(q=raw)


def classroom_search_filter(q: str) -> Q:
    return Q(name__icontains=q)


def child_search_filter(q: str) -> Q:
    return Q(first_name__icontains=q) | Q(last_name__icontains=q)
