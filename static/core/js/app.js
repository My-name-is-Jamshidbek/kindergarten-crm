(function () {
  const body = document.body;
  const sidebar = document.querySelector("[data-sidebar]");
  const backdrop = document.querySelector("[data-sidebar-backdrop]");
  const openButton = document.querySelector("[data-sidebar-open]");
  const closeButton = document.querySelector("[data-sidebar-close]");
  const topbar = document.querySelector("[data-topbar]");

  function openSidebar() {
    if (!sidebar || !backdrop) return;
    sidebar.classList.add("is-open");
    backdrop.classList.add("is-open");
    body.classList.add("overflow-hidden");
  }

  function closeSidebar() {
    if (!sidebar || !backdrop) return;
    sidebar.classList.remove("is-open");
    backdrop.classList.remove("is-open");
    body.classList.remove("overflow-hidden");
  }

  openButton?.addEventListener("click", openSidebar);
  closeButton?.addEventListener("click", closeSidebar);
  backdrop?.addEventListener("click", closeSidebar);

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeSidebar();
  });

  document.querySelectorAll("[data-sidebar] a").forEach(function (link) {
    link.addEventListener("click", function () {
      if (window.matchMedia("(max-width: 991.98px)").matches) closeSidebar();
    });
  });

  function syncTopbar() {
    if (!topbar) return;
    topbar.classList.toggle("is-scrolled", window.scrollY > 8);
  }

  syncTopbar();
  window.addEventListener("scroll", syncTopbar, { passive: true });

  document.querySelectorAll(".alert-dismissible").forEach(function (alert) {
    window.setTimeout(function () {
      const instance = window.bootstrap?.Alert?.getOrCreateInstance(alert);
      if (instance) instance.close();
    }, 5200);
  });

  document.querySelectorAll("[data-filter-toggle]").forEach(function (button) {
    button.addEventListener("click", function () {
      const target = document.querySelector(button.getAttribute("data-filter-toggle"));
      if (!target) return;
      target.classList.toggle("is-collapsed");
      button.setAttribute("aria-expanded", String(!target.classList.contains("is-collapsed")));
    });
  });

  if (window.lucide) {
    window.lucide.createIcons();
  }

  const locationMap = document.getElementById("locationMap");
  if (locationMap && window.L) {
    const latitudeInput = document.getElementById("id_latitude");
    const longitudeInput = document.getElementById("id_longitude");
    const coordinatesLabel = document.querySelector("[data-location-coordinates]");
    const savedLat = parseFloat(locationMap.dataset.lat || "");
    const savedLng = parseFloat(locationMap.dataset.lng || "");
    const defaultLat = parseFloat(locationMap.dataset.defaultLat || "39.6542");
    const defaultLng = parseFloat(locationMap.dataset.defaultLng || "66.9597");
    const hasSavedCoordinates = Number.isFinite(savedLat) && Number.isFinite(savedLng);
    const start = hasSavedCoordinates ? [savedLat, savedLng] : [defaultLat, defaultLng];

    const map = window.L.map(locationMap, {
      scrollWheelZoom: false,
    }).setView(start, hasSavedCoordinates ? 16 : 12);
    window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap",
    }).addTo(map);

    const markerIcon = window.L.divIcon({
      className: "location-map-marker",
      html: "<span></span>",
      iconSize: [32, 32],
      iconAnchor: [16, 30],
    });
    const marker = window.L.marker(start, { draggable: true, icon: markerIcon }).addTo(map);

    function setCoordinates(latlng) {
      const lat = Number(latlng.lat).toFixed(6);
      const lng = Number(latlng.lng).toFixed(6);
      if (latitudeInput) latitudeInput.value = lat;
      if (longitudeInput) longitudeInput.value = lng;
      if (coordinatesLabel) coordinatesLabel.textContent = `${lat}, ${lng}`;
      marker.setLatLng(latlng);
    }

    if (hasSavedCoordinates) {
      setCoordinates({ lat: savedLat, lng: savedLng });
    }

    map.on("click", function (event) {
      setCoordinates(event.latlng);
    });

    marker.on("dragend", function () {
      setCoordinates(marker.getLatLng());
    });

    function refreshMap() {
      map.invalidateSize();
      map.setView(marker.getLatLng(), map.getZoom(), { animate: false });
    }

    window.requestAnimationFrame(refreshMap);
    window.setTimeout(refreshMap, 250);
    window.setTimeout(refreshMap, 700);
  }
})();
