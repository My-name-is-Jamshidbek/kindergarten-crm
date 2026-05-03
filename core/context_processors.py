from __future__ import annotations

from django.http import HttpRequest

from django.urls import reverse

from .roles import ROLE_LABELS, default_url_for_user, nav_items_for_request, primary_role


def role_context(request: HttpRequest) -> dict[str, object]:
	role = primary_role(request.user)
	return {
		"current_role": role,
		"current_role_label": ROLE_LABELS.get(role, ""),
		"current_role_default_url": reverse(default_url_for_user(request.user)),
		"role_nav_items": nav_items_for_request(request),
	}
