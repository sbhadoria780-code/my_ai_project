// Minor UX polish -- no scoring/business logic lives on the client side,
// so the model/scoring behavior is never bypassable via devtools.

document.addEventListener("DOMContentLoaded", () => {
  const menuToggle = document.getElementById("menuToggle");
  const sidebar = document.getElementById("sidebar");
  if (menuToggle && sidebar) {
    menuToggle.addEventListener("click", () => sidebar.classList.toggle("open"));
    document.addEventListener("click", (e) => {
      if (sidebar.classList.contains("open") && !sidebar.contains(e.target) && e.target !== menuToggle && !menuToggle.contains(e.target)) {
        sidebar.classList.remove("open");
      }
    });
  }

  const fileInput = document.getElementById("resumes");
  const fileLabel = document.getElementById("file-count-label");

  if (fileInput && fileLabel) {
    fileInput.addEventListener("change", () => {
      const n = fileInput.files.length;
      fileLabel.textContent = n === 0
        ? "No files selected"
        : `${n} file${n > 1 ? "s" : ""} selected`;
    });
  }

  const rejectButtons = document.querySelectorAll("[data-confirm-reject]");
  rejectButtons.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const ok = confirm(
        "Confirm: record a 'Reject' decision for this candidate? " +
        "This will be permanently logged in the audit trail."
      );
      if (!ok) e.preventDefault();
    });
  });
});
