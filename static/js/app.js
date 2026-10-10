// Comportamiento minimo de StockFlow: confirma acciones destructivas
// y refresca badges HTMX tras cada respuesta.

document.addEventListener("htmx:afterRequest", function (event) {
  if (event.detail.pathInfo && event.detail.pathInfo.requestPath) {
    // Ancla al top tras navegacion HTMX para evitar scroll lateral.
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
});