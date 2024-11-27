// Parse graph data passed from Django
const graphData = JSON.parse(document.getElementById('graph-data').textContent);

// Extract data for the fixed cost chart
const fixedCostDates = graphData.user_fixed_dates;  // X-axis (dates)
const fixedCostValues = graphData.user_fixed_values;  // Y-axis for fixed cost values
const fixedCostNotes = graphData.fixed_cost_notes;  // Notes for fixed costs
const utilitiesValues = graphData.utilities_values;  // Y-axis for utilities values
const expensesValue = graphData.expenses_value;  // Y-axis for expenses values
const expensesNotes = graphData.expenses_note;  // Notes for expenses
const fixedCostName = graphData.fixed_cost_name // Fixed cost name

// Create a chart for fixed costs
const ctxFixed = document.getElementById('fixedCostChart').getContext('2d');
const fixedCostChart = new Chart(ctxFixed, {
    type: 'line', // Line chart
    data: {
        labels: fixedCostDates,  // X-axis (dates)
        datasets: [
            {
                label: `${fixedCostName} Values (£)`,  
                data: fixedCostValues,  
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderWidth: 2,
                tooltip: {
                    callbacks: {
                        label: function(tooltipItem) {
                            const index = tooltipItem.dataIndex;
                            const fixedCostNotes = graphData.fixed_cost_notes ? graphData.fixed_cost_notes[index] : '';
                            return fixedCostNotes ? `${tooltipItem.raw} - ${fixedCostNotes}` : tooltipItem.raw;
                        }
                    }
                }
            },            
        ]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                display: true,
                position: 'top',
            },
        },
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Date',
                },
            },
            y: {
                title: {
                    display: true,
                    text: 'Amount (£)',
                },
                beginAtZero: true,
            },
        },
    }
});

// Create mixed chart
const ctx_1 = document.getElementById('mixedChart').getContext('2d');
const mixedChart = new Chart(ctx_1, {
    type: 'line', // Line chart
    data: {
        labels: fixedCostDates,  // X-axis (dates)
        datasets: [
            {
                label: 'Utilities Values (£)',  
                data: utilitiesValues,  
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderWidth: 2,
            },  
            {
                label: 'Monthly Expenses Values (£)',  
                data: expensesValue,  
                borderColor: 'rgba(153, 102, 255, 1)',
                backgroundColor: 'rgba(153, 102, 255, 0.2)',
                tooltip: {
                    callbacks: {
                        label: function(tooltipItem) {
                            const index = tooltipItem.dataIndex;
                            const expensesNotes = graphData.expenses_notes ? graphData.expenses_notes[index] : '';
                            return expensesNotes ? `${tooltipItem.raw} - ${expensesNotes}` : tooltipItem.raw;
                        }
                    }
                }
            },          
        ]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                display: true,
                position: 'top',
            },
        },
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Date',
                },
            },
            y: {
                title: {
                    display: true,
                    text: 'Amount (£)',
                },
                beginAtZero: true,
            },
        },
    }
});

// Button to show more rows
document.getElementById('showMoreButton').addEventListener('click', function() {
    // Select all hidden rows
    const hiddenRows = document.querySelectorAll('.hidden-row');
    
    // Show all hidden rows
    hiddenRows.forEach(row => {
        row.classList.remove('hidden-row');
    });

    // Hide the button after all rows are shown
    this.style.display = 'none';
});
