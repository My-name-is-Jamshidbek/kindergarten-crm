from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import (
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


FIRST_NAMES = ["Emma", "Noah", "Olivia", "Liam", "Ava", "Sophia", "Mason", "Mia"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
PHONE_PREFIXES = ["+1", "+44", "+49"]


class Command(BaseCommand):
    help = "Seed demo classrooms, children, and guardians."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--classrooms", type=int, default=3)
        parser.add_argument("--children", type=int, default=15)

    @transaction.atomic
    def handle(self, *args, **options):
        classrooms_count: int = options["classrooms"]
        children_count: int = options["children"]

        classrooms = self._create_classrooms(classrooms_count)
        self._create_children_and_guardians(classrooms, children_count)

        tariffs = self._create_tariffs()
        self._assign_tariffs_to_children(tariffs)
        self._create_today_attendance()
        self._create_monthly_billing_seed()

        self.stdout.write(self.style.SUCCESS("Demo data created."))

    def _create_today_attendance(self) -> None:
        today = timezone.localdate()
        active_children = Child.objects.filter(status=ChildStatus.ACTIVE)
        created = 0
        for child in active_children:
            _, was_created = Attendance.objects.get_or_create(
                child=child,
                attendance_date=today,
                defaults={"status": AttendanceStatus.EXPECTED},
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Attendance seeded for today: {created} record(s) created."))

    def _create_monthly_billing_seed(self) -> None:
        """Create monthly billing rows for the current month."""
        today = timezone.localdate()
        billing_month = today.strftime("%Y-%m")
        active_children = list(
            Child.objects.filter(status=ChildStatus.ACTIVE).select_related("tariff").prefetch_related("guardians")
        )
        if not active_children:
            self.stdout.write(self.style.WARNING("No active children found; skipping monthly billing seed."))
            return

        created_rows = 0
        for child in active_children:
            default_amount = child.tariff.amount if child.tariff else Decimal(str(random.choice([450, 500, 550, 600])))
            _, created = MonthlyBilling.objects.get_or_create(
                child=child,
                billing_month=billing_month,
                defaults={"amount": default_amount, "status": MonthlyBillingStatus.UNPAID},
            )
            if created:
                created_rows += 1
        # Mark a few as paid for demo purposes.

        to_mark = max(1, created_rows // 3)
        ids = list(
            MonthlyBilling.objects.filter(billing_month=billing_month)
            .order_by("id")
            .values_list("id", flat=True)[:to_mark]
        )
        if ids:
            MonthlyBilling.objects.filter(id__in=ids).update(
                status=MonthlyBillingStatus.PAID,
                paid_at=timezone.now(),
            )

        self.stdout.write(self.style.SUCCESS(f"Monthly billing seeded: {created_rows} row(s) created for {billing_month}."))

    def _create_tariffs(self) -> list[Tariff]:
        defaults = [
            ("Standard", Decimal("500.00"), True, "Default monthly kindergarten fee"),
            ("Discount", Decimal("450.00"), True, "Reduced monthly fee"),
            ("Premium", Decimal("600.00"), True, "Premium monthly fee"),
        ]
        tariffs: list[Tariff] = []
        for name, amount, is_active, description in defaults:
            tariff, _ = Tariff.objects.get_or_create(
                name=name,
                defaults={"amount": amount, "is_active": is_active, "description": description},
            )
            if tariff.amount != amount or tariff.is_active != is_active or tariff.description != description:
                tariff.amount = amount
                tariff.is_active = is_active
                tariff.description = description
                tariff.save(update_fields=["amount", "is_active", "description", "updated_at"])
            tariffs.append(tariff)
        self.stdout.write(self.style.SUCCESS(f"Tariffs seeded: {len(tariffs)} tariff(s)."))
        return tariffs

    def _assign_tariffs_to_children(self, tariffs: list[Tariff]) -> None:
        if not tariffs:
            return
        active_children = list(Child.objects.filter(status=ChildStatus.ACTIVE))
        if not active_children:
            return
        assigned = 0
        for child in active_children:
            if child.tariff_id:
                continue
            child.tariff = random.choice(tariffs)
            child.save(update_fields=["tariff", "updated_at"])
            assigned += 1

        self.stdout.write(self.style.SUCCESS(f"Assigned tariffs to {assigned} active child(ren) (where missing)."))

    def _create_classrooms(self, count: int) -> list[Classroom]:
        defaults = [
            ("Sunflowers", "3-4", 10),
            ("Rainbows", "4-5", 12),
            ("Stars", "5-6", 14),
            ("Explorers", "6-7", 16),
        ]
        classrooms: list[Classroom] = []
        for idx in range(count):
            name, age_group, capacity = defaults[idx % len(defaults)]
            classroom, _ = Classroom.objects.get_or_create(
                name=f"{name} {idx + 1}" if idx >= len(defaults) else name,
                defaults={"age_group": age_group, "capacity": capacity},
            )
            if classroom.age_group != age_group or classroom.capacity != capacity:
                classroom.age_group = age_group
                classroom.capacity = capacity
                classroom.save(update_fields=["age_group", "capacity", "updated_at"])
            classrooms.append(classroom)
        return classrooms

    def _create_children_and_guardians(self, classrooms: list[Classroom], count: int) -> None:
        today = timezone.localdate()
        created = 0
        attempts = 0

        while created < count and attempts < count * 10:
            attempts += 1
            classroom = random.choice(classrooms)

            if Child.objects.filter(classroom=classroom).count() >= classroom.capacity:
                continue

            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)

            birth_date = today - timedelta(days=random.randint(3 * 365, 6 * 365))

            child = Child.objects.create(
                first_name=first_name,
                last_name=last_name,
                birth_date=birth_date,
                classroom=classroom,
                status=random.choice([ChildStatus.ACTIVE, ChildStatus.INACTIVE]),
            )

            email_base = f"{first_name}.{last_name}.{child.pk}".lower()
            primary_guardian = Guardian.objects.create(
                first_name=random.choice(FIRST_NAMES),
                last_name=last_name,
                phone=f"{random.choice(PHONE_PREFIXES)}{random.randint(100000000, 999999999)}",
                email=f"{email_base}@example.com",
                child=child,
                is_primary=True,
            )

            if random.random() < 0.5:
                Guardian.objects.create(
                    first_name=random.choice(FIRST_NAMES),
                    last_name=last_name,
                    phone=f"{random.choice(PHONE_PREFIXES)}{random.randint(100000000, 999999999)}",
                    email=f"{email_base}.alt@example.com",
                    child=child,
                    is_primary=False,
                )

            created += 1
