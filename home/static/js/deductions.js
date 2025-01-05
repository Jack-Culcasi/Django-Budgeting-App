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

document.addEventListener('DOMContentLoaded', () => {
    const deductionAmountInput = document.getElementById('deduction-amount');
    const checkboxes = document.querySelectorAll('.checkbox');
    const deductionsDisplay = document.getElementById('deductions-display');

    // Extract the currency symbol from the dataset
    const currencySymbol = deductionsDisplay.dataset.currencySymbol;

    function updateDeductions() {
        let totalDeductions = parseFloat(deductionAmountInput.value) || 0;

        checkboxes.forEach((checkbox) => {
            if (checkbox.checked) {
                const amount = parseFloat(checkbox.dataset.amount) || 0;

                // Add the full cost or half (split) based on checkbox class
                if (checkbox.classList.contains('full-cost')) {
                    totalDeductions += amount;
                } else if (checkbox.classList.contains('split-cost')) {
                    totalDeductions += amount / 2;
                }
            }
        });

        // Update the deductions display
        deductionsDisplay.textContent = `${currencySymbol} ${totalDeductions.toFixed(2)}`;
    }

    // Add event listeners
    deductionAmountInput.addEventListener('input', updateDeductions);
    checkboxes.forEach((checkbox) => checkbox.addEventListener('change', updateDeductions));
});