document.querySelectorAll(".openResetPasswordModal").forEach(el => {
  el.addEventListener("click", function (e) {
    e.preventDefault();

    const url = el.getAttribute("data-url");

    // If dropdown is open, close it
const dropdown = document.getElementById("profileDropdown");
if (dropdown) {
  dropdown.style.visibility = "hidden";
  dropdown.style.opacity = "0";
  dropdown.style.display = "none";

  // Reset the icon state
  const profileButton = document.querySelector(".action-buttons .push.primary");
  if (profileButton) {
    profileButton.dataset.state = "List-Default";
    profileButton.style.color = getComputedStyle(document.documentElement).getPropertyValue('--theme-color-gray3').trim();
    profileButton.style.backgroundColor = "transparent";
  }
}

    fetch(url)
      .then(response => response.text())
      .then(html => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const modal = doc.querySelector('#resetPasswordModal');

        if (modal) {
          document.body.appendChild(modal);
          const bsModal = new bootstrap.Modal(modal);
          bsModal.show();

          modal.querySelector('form').addEventListener('submit', function (e) {
            e.preventDefault();

            const formData = new FormData(this);

            fetch(url, {
              method: "POST",
              headers: {
                "X-Requested-With": "XMLHttpRequest",
              },
              body: formData
            })
              .then(res => res.json())
              .then(() => {
                document.body.innerHTML = "";
                document.body.style.backgroundColor = "white";
                document.body.style.transition = "none";

                setTimeout(() => {
                  alert("If your email is valid, you’ll receive a reset link shortly.");
                  location.reload();
                }, 50);
              });
          });
        }
      });
  });
});