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
    AuthorizedPickup,
    Child,
    ChildStatus,
    Classroom,
    Guardian,
    MonthlyBilling,
    MonthlyBillingStatus,
    Tariff,
)


FIRST_NAMES = [
    "Aziz",
    "Sardor",
    "Jasur",
    "Bekzod",
    "Ibrohim",
    "Muhammad",
    "Ziyod",
    "Shahzod",
    "Malika",
    "Zuhra",
    "Madina",
    "Diyora",
    "Shahnoza",
    "Sabina",
    "Aziza",
    "Munisa",
]
LAST_NAMES = [
    "Karimov",
    "Toshmatov",
    "Rahmonov",
    "Abdullayev",
    "Saidov",
    "Qodirov",
    "Ismoilov",
    "Yusupov",
    "Nazarov",
    "Mirzayev",
]
PHONE_PREFIXES = ["+998"]


class Command(BaseCommand):
    help = "Demo maʼlumotlar (guruhlar, bolalar, vasiylar, tariflar, davomat, oylik to‘lovlar) yaratish."

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
        self._create_authorized_pickups()
        self._create_attendance_seed(days=7)
        self._create_monthly_billing_seed(months=2)

        self.stdout.write(self.style.SUCCESS("Demo maʼlumotlar yaratildi."))

    def _create_attendance_seed(self, *, days: int) -> None:
        """Oxirgi `days` kun uchun davomat yozuvlarini yaratadi (kutilmoqda holati bilan)."""
        today = timezone.localdate()
        active_children = Child.objects.filter(status=ChildStatus.ACTIVE)
        if not active_children.exists():
            self.stdout.write(self.style.WARNING("Faol bolalar topilmadi; davomat yaratilmadi."))
            return

        created = 0
        for offset in range(days):
            d = today - timedelta(days=offset)
            for child in active_children:
                _, was_created = Attendance.objects.get_or_create(
                    child=child,
                    attendance_date=d,
                    defaults={"status": AttendanceStatus.EXPECTED},
                )
                if was_created:
                    created += 1

        self.stdout.write(self.style.SUCCESS(f"Davomat yaratildi: {created} ta yozuv (oxirgi {days} kun)."))

    def _create_monthly_billing_seed(self, *, months: int) -> None:
        """Joriy oy va oldingi oylar uchun oylik to'lov yozuvlarini yaratadi."""
        today = timezone.localdate()
        active_children = list(Child.objects.filter(status=ChildStatus.ACTIVE).select_related("tariff"))
        if not active_children:
            self.stdout.write(self.style.WARNING("Faol bolalar topilmadi; oylik to‘lovlar yaratilmadi."))
            return

        created_rows = 0
        months_seeded: list[str] = []

        for m in range(months):
            # Build YYYY-MM going backwards.
            y = today.year
            mo = today.month - m
            while mo <= 0:
                mo += 12
                y -= 1
            billing_month = f"{y:04d}-{mo:02d}"
            months_seeded.append(billing_month)

            for child in active_children:
                default_amount = child.tariff.amount if child.tariff else Decimal("500")
                _, created = MonthlyBilling.objects.get_or_create(
                    child=child,
                    billing_month=billing_month,
                    defaults={"amount": default_amount, "status": MonthlyBillingStatus.UNPAID},
                )
                if created:
                    created_rows += 1

        # Demo uchun bir nechta yozuvni "To‘langan" qilib belgilab qo'yamiz.
        if created_rows:
            to_mark = max(1, created_rows // 4)
            ids = list(
                MonthlyBilling.objects.filter(billing_month=months_seeded[0])
                .order_by("id")
                .values_list("id", flat=True)[:to_mark]
            )
            if ids:
                MonthlyBilling.objects.filter(id__in=ids).update(
                    status=MonthlyBillingStatus.PAID,
                    paid_at=timezone.now(),
                )

        months_text = ", ".join(months_seeded)
        self.stdout.write(
            self.style.SUCCESS(
                f"Oylik to‘lovlar yaratildi: {created_rows} ta yozuv ({months_text})."
            )
        )

    def _create_authorized_pickups(self) -> None:
        """Har bir bola uchun kamida 1 ta ruxsat etilgan olib ketuvchi shaxsni yaratadi."""
        children = list(Child.objects.all())
        if not children:
            self.stdout.write(self.style.WARNING("Bolalar topilmadi; ruxsat etilgan olib ketuvchilar yaratilmadi."))
            return

        defaults = [
            ("Oybek Karimov", "Amaki", "+998901234567"),
            ("Dilnoza Rahmonova", "Xola", "+998931112233"),
            ("Javohir Saidov", "Bobo", "+998991234321"),
        ]

        created = 0
        for child in children:
            if AuthorizedPickup.objects.filter(child=child).exists():
                continue
            full_name, relationship, phone = random.choice(defaults)
            AuthorizedPickup.objects.create(
                child=child,
                full_name=full_name,
                relationship=relationship,
                phone=phone,
                id_document_number="AA1234567",
                is_active=True,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Olib ketuvchilar yaratildi: {created} ta."))

    def _create_tariffs(self) -> list[Tariff]:
        defaults = [
            ("Standart", Decimal("500.00"), True, "Bolalar bog‘chasi uchun oylik standart to‘lov"),
            ("Chegirma", Decimal("450.00"), True, "Oylik to‘lovga chegirma (imtiyozli tarif)"),
            ("Premium", Decimal("600.00"), True, "Qo‘shimcha xizmatlar bilan premium tarif"),
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
        self.stdout.write(self.style.SUCCESS(f"Tariflar yaratildi: {len(tariffs)} ta."))
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

        self.stdout.write(self.style.SUCCESS(f"Tarif biriktirildi: {assigned} ta faol bola (tarifi bo‘lmaganlariga)."))

    def _create_classrooms(self, count: int) -> list[Classroom]:
        defaults = [
            ("Quyoshgullar", "3-4 yosh", 10),
            ("Kamalak", "4-5 yosh", 12),
            ("Yulduzlar", "5-6 yosh", 14),
            ("Kashfiyotchilar", "6-7 yosh", 16),
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
        existing_children = Child.objects.count()
        to_create = max(0, count - existing_children)
        created = 0
        attempts = 0

        if to_create == 0:
            self.stdout.write(self.style.SUCCESS(f"Bolalar allaqachon yetarli: {existing_children} ta. Yangi bola qo‘shilmadi."))
            self._ensure_guardians_for_children()
            return

        while created < to_create and attempts < to_create * 10:
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

        self.stdout.write(self.style.SUCCESS(f"Bolalar qo‘shildi: {created} ta."))
        self._ensure_guardians_for_children()

    def _ensure_guardians_for_children(self) -> None:
        """Har bir bola uchun kamida 1 ta asosiy vasiy borligini taʼminlaydi."""
        children = list(Child.objects.all())
        created = 0
        for child in children:
            if Guardian.objects.filter(child=child, is_primary=True).exists():
                continue
            last_name = child.last_name
            email_base = f"{child.first_name}.{last_name}.{child.pk}".lower()
            Guardian.objects.create(
                first_name=random.choice(FIRST_NAMES),
                last_name=last_name,
                phone=f"{random.choice(PHONE_PREFIXES)}{random.randint(100000000, 999999999)}",
                email=f"{email_base}.primary@example.com",
                child=child,
                is_primary=True,
            )
            created += 1

        if created:
            self.stdout.write(self.style.SUCCESS(f"Asosiy vasiylar qo‘shildi: {created} ta."))
