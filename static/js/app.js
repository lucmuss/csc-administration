(function () {
  function toggleMobileNav() {
    var button = document.querySelector("[data-mobile-nav-toggle]");
    var nav = document.querySelector("[data-mobile-nav]");

    if (!button || !nav) {
      return;
    }

    function setOpenState(isOpen) {
      nav.classList.toggle("is-open", isOpen);
      button.setAttribute("aria-expanded", isOpen ? "true" : "false");
    }

    button.addEventListener("click", function () {
      var isOpen = !nav.classList.contains("is-open");
      setOpenState(isOpen);
    });

    nav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        setOpenState(false);
      });
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        setOpenState(false);
      }
    });

    document.addEventListener("click", function (event) {
      if (!nav.classList.contains("is-open")) {
        return;
      }
      if (nav.contains(event.target) || button.contains(event.target)) {
        return;
      }
      setOpenState(false);
    });
  }

  function handleCookieConsent() {
    var banner = document.querySelector("[data-cookie-banner]");
    if (!banner) {
      return;
    }

    var consent = window.localStorage.getItem("cookie_consent_analytics");
    if (consent === null) {
      banner.classList.remove("hidden");
    }

    var accept = banner.querySelector("[data-cookie-accept]");
    var decline = banner.querySelector("[data-cookie-decline]");

    function hideBanner(value) {
      window.localStorage.setItem("cookie_consent_analytics", value);
      banner.classList.add("hidden");
      if (value === "true") {
        loadAnalytics();
      }
    }

    if (accept) {
      accept.addEventListener("click", function () {
        hideBanner("true");
      });
    }

    if (decline) {
      decline.addEventListener("click", function () {
        hideBanner("false");
      });
    }
  }

  function loadAnalytics() {
    var trackingId = document.body.dataset.gaTrackingId;
    if (!trackingId || window.__cscGaLoaded) {
      return;
    }

    window.__cscGaLoaded = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function () {
      window.dataLayer.push(arguments);
    };

    var script = document.createElement("script");
    script.async = true;
    script.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(trackingId);
    script.onload = function () {
      window.gtag("js", new Date());
      window.gtag("config", trackingId, {
        anonymize_ip: true,
        cookie_flags: "SameSite=None;Secure",
      });
    };
    document.head.appendChild(script);
  }

  function maybeLoadAnalytics() {
    if (window.localStorage.getItem("cookie_consent_analytics") === "true") {
      loadAnalytics();
    }
  }

  function wireGovernanceRecordForm() {
    var recordType = document.querySelector("select[name='record_type']");
    if (!recordType) {
      return;
    }

    function toggleField(name, visible) {
      var input = document.querySelector("[name='" + name + "']");
      if (!input) {
        return;
      }

      var field = input.closest(".field");
      if (field) {
        field.classList.toggle("hidden", !visible);
      }
      input.disabled = !visible;
    }

    function syncRecordForm() {
      var isTransport = recordType.value === "transport";
      toggleField("destination", isTransport);
      toggleField("vehicle_identifier", isTransport);
      toggleField("destruction_method", !isTransport);
    }

    recordType.addEventListener("change", syncRecordForm);
    syncRecordForm();
  }

  function wirePasswordToggles() {
    document.querySelectorAll("[data-password-toggle]").forEach(function (button) {
      var targetId = button.getAttribute("data-password-target");
      if (!targetId) {
        return;
      }
      var input = document.getElementById(targetId);
      if (!input) {
        return;
      }

      button.addEventListener("click", function () {
        var show = input.type === "password";
        input.type = show ? "text" : "password";
        button.textContent = show ? "Verbergen" : "Anzeigen";
        button.setAttribute("aria-label", show ? "Passwort verbergen" : "Passwort anzeigen");
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    toggleMobileNav();
    handleCookieConsent();
    maybeLoadAnalytics();
    wireGovernanceRecordForm();
    wirePasswordToggles();
  });
})();
