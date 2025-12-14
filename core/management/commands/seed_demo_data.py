from __future__ import annotations

import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import Attendance, AttendanceStatus, Child, ChildStatus, Classroom, Guardian


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
        self._create_today_attendance()

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
