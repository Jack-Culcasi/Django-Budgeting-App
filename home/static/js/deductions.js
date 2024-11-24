// Add event listeners to all checkboxes
document.querySelectorAll('.checkbox').forEach(checkbox => {
    checkbox.addEventListener('change', function () {
        const row = this.getAttribute('data-row'); // Get the row ID
        const isFullCost = this.classList.contains('full-cost');
        
        if (this.checked) {
            // Uncheck the other checkbox in the same row
            const otherCheckbox = document.querySelector(`input.checkbox.${isFullCost ? 'split-cost' : 'full-cost'}[data-row="${row}"]`);
            if (otherCheckbox) {
                otherCheckbox.checked = false;
            }
        }
    });
});