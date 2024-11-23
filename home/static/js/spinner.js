document.addEventListener("DOMContentLoaded", function () {
    const uploadForm = document.getElementById("uploadForm");
    const loadingSpinner = document.getElementById("loadingSpinner");
    const uploadButton = uploadForm.querySelector("button[type='submit']");

    uploadForm.addEventListener("submit", function (e) {
        // Show the spinner
        loadingSpinner.classList.remove("hidden");

        // Optionally disable the button to prevent multiple submissions
        uploadButton.disabled = true;
    });
});