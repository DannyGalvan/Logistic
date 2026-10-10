// Comportamiento de StockFlow: tema claro/oscuro, toasts, mostrar
// contrasena y scroll al top tras navegacion HTMX.

(function () {
  function saveTheme(theme) {
    try { localStorage.setItem("sf-theme", theme); } catch (e) { /* sin storage */ }
  }

  document.addEventListener("DOMContentLoaded", function () {
    var toggle = document.getElementById("themeToggle");
    if (toggle) {
      toggle.addEventListener("click", function () {
        var root = document.documentElement;
        var next = root.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
        root.setAttribute("data-bs-theme", next);
        saveTheme(next);
      });
    }

    // Oculta los toasts de mensajes despues de unos segundos.
    if (window.bootstrap) {
      document.querySelectorAll(".toast.show").forEach(function (el) {
        bootstrap.Toast.getOrCreateInstance(el).show();
      });
    }

    // Acciones irreversibles: <button data-confirm-action="url" data-confirm-message="...">
    var confirmModal = document.getElementById("confirmModal");
    if (confirmModal && window.bootstrap) {
      var modal = new bootstrap.Modal(confirmModal);
      document.querySelectorAll("[data-confirm-action]").forEach(function (btn) {
        btn.addEventListener("click", function (event) {
          event.preventDefault();
          document.getElementById("confirmModalForm").action = btn.getAttribute("data-confirm-action");
          document.getElementById("confirmModalMessage").textContent =
            btn.getAttribute("data-confirm-message") || "¿Estas seguro?";
          var submit = document.getElementById("confirmModalSubmit");
          submit.className = "btn " + (btn.getAttribute("data-confirm-variant") || "btn-primary");
          modal.show();
        });
      });
    }

    document.querySelectorAll("[data-toggle-password]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var input = document.getElementById(btn.getAttribute("data-toggle-password"));
        if (!input) return;
        var visible = input.type === "text";
        input.type = visible ? "password" : "text";
        btn.innerHTML = visible ? '<i class="bi bi-eye"></i>' : '<i class="bi bi-eye-slash"></i>';
      });
    });
  });

  document.addEventListener("htmx:afterRequest", function (event) {
    if (event.detail.pathInfo && event.detail.pathInfo.requestPath) {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  });
})();
