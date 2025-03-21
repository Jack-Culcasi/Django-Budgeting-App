// Get the data passed from Django
const graphData = JSON.parse(document.getElementById('graph-data').textContent);

// Extract data for net_worth chart
const categoriesDates = graphData.categories_dates;  // X-axis (dates)
const categoriesValues = graphData.categories_values;  // Y-axis for category values
const categoriesNotes = graphData.categories_notes;
const utilitiesValues = graphData.utilities_values;  // Y-axis for utilities values
const expensesValue = graphData.expenses_value;  // Y-axis for expenses values
const expensesNotes = graphData.expenses_notes;
const categoryName = graphData.category_name;

// Create mixed chart
const ctx_1 = document.getElementById('mixedChart').getContext('2d');
const mixedChart = new Chart(ctx_1, {
    type: 'line', // Line chart
    data: {
        labels: categoriesDates,  // X-axis (dates)
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

// Create category chart
const ctx = document.getElementById('categoryChart').getContext('2d');
const categoryChart = new Chart(ctx, {
    type: 'line', // Line chart
    data: {
        labels: categoriesDates,  // X-axis (dates)
        datasets: [
            {
                label: `${categoryName} Values (£)`,  // First line
                data: categoriesValues,  
                borderColor: 'rgba(255, 159, 64, 1)',
                backgroundColor: 'rgba(255, 159, 64, 0.2)',
                borderWidth: 2,
                tooltip: {
                    callbacks: {
                        label: function(tooltipItem) {
                            const index = tooltipItem.dataIndex;
                            const categoriesNotes = graphData.categories_notes ? graphData.categories_notes[index] : '';
                            return categoriesNotes ? `${tooltipItem.raw} - ${categoriesNotes}` : tooltipItem.raw;
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