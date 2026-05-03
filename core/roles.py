from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpRequest
from django.urls import reverse


ROLE_ADMIN = "admin"
ROLE_EDUCATOR = "educator"
ROLE_ACCOUNTANT = "accountant"


ROLE_LABELS = {
	ROLE_ADMIN: "Admin",
	ROLE_EDUCATOR: "Educator",
	ROLE_ACCOUNTANT: "Accountant",
}


@dataclass(frozen=True)
class NavItem:
	label: str
	url_name: str
	icon: str
	active_prefixes: tuple[str, ...]


ROLE_NAV_ITEMS = {
	ROLE_ADMIN: (
		NavItem("Dashboard", "core:dashboard", "layout-dashboard", ("dashboard",)),
		NavItem("Davomat", "core:attendance_list", "clipboard-check", ("attendance",)),
		NavItem("To'lovlar", "core:billing_monthly_list", "wallet-cards", ("billing",)),
		NavItem("Tariflar", "core:tariff_list", "badge-dollar-sign", ("tariff",)),
		NavItem("Guruhlar", "core:classroom_list", "school", ("classroom",)),
		NavItem("Bolalar", "core:child_list", "users-round", ("child",)),
		NavItem("Vasiylar", "core:guardian_list", "contact-round", ("guardian",)),
	),
	ROLE_EDUCATOR: (
		NavItem("Dashboard", "core:dashboard", "layout-dashboard", ("dashboard",)),
		NavItem("Davomat", "core:attendance_list", "clipboard-check", ("attendance",)),
		NavItem("Vasiylar", "core:guardian_list", "contact-round", ("guardian",)),
	),
	ROLE_ACCOUNTANT: (
		NavItem("Dashboard", "core:dashboard", "layout-dashboard", ("dashboard",)),
		NavItem("To'lovlar", "core:billing_monthly_list", "wallet-cards", ("billing",)),
		NavItem("Tariflar", "core:tariff_list", "badge-dollar-sign", ("tariff",)),
	),
}


ROLE_DEFAULT_URLS = {
	ROLE_ADMIN: "core:dashboard",
	ROLE_EDUCATOR: "core:dashboard",
	ROLE_ACCOUNTANT: "core:dashboard",
}


def user_roles(user: object) -> set[str]:
	if not getattr(user, "is_authenticated", False):
		return set()
	if getattr(user, "is_superuser", False):
		return {ROLE_ADMIN, ROLE_EDUCATOR, ROLE_ACCOUNTANT}
	return set(user.groups.filter(name__in=ROLE_LABELS.keys()).values_list("name", flat=True))


def user_has_role(user: object, allowed_roles: Iterable[str]) -> bool:
	allowed = set(allowed_roles)
	if getattr(user, "is_superuser", False):
		return True
	return bool(user_roles(user) & allowed)


def primary_role(user: object) -> str:
	roles = user_roles(user)
	for role in (ROLE_ADMIN, ROLE_EDUCATOR, ROLE_ACCOUNTANT):
		if role in roles:
			return role
	return ""


def default_url_for_user(user: object) -> str:
	role = primary_role(user)
	if not role:
		return "core:home"
	return ROLE_DEFAULT_URLS[role]


def nav_items_for_request(request: HttpRequest) -> list[dict[str, str | bool]]:
	role = primary_role(request.user)
	if not role:
		return []
	current_name = request.resolver_match.url_name if request.resolver_match else ""
	items: list[dict[str, str | bool]] = []
	for item in ROLE_NAV_ITEMS[role]:
		items.append(
			{
				"label": item.label,
				"url": reverse(item.url_name),
				"icon": item.icon,
				"active": any(current_name.startswith(prefix) for prefix in item.active_prefixes),
			}
		)
	if getattr(request.user, "is_superuser", False):
		item = NavItem("Joylashuv", "core:kindergarten_location", "map-pin", ("kindergarten_location",))
		items.append(
			{
				"label": item.label,
				"url": reverse(item.url_name),
				"icon": item.icon,
				"active": any(current_name.startswith(prefix) for prefix in item.active_prefixes),
			}
		)
	return items


class RoleRequiredMixin(UserPassesTestMixin):
	allowed_roles: tuple[str, ...] = ()
	permission_denied_message = "Bu sahifaga kirish uchun ruxsat yo'q."

	def test_func(self) -> bool:
		return user_has_role(self.request.user, self.allowed_roles)


class SuperuserRequiredMixin(UserPassesTestMixin):
	permission_denied_message = "Bu sahifaga faqat superadmin kira oladi."

	def test_func(self) -> bool:
		return bool(getattr(self.request.user, "is_superuser", False))
