// Get the data passed from Django
const graphData = JSON.parse(document.getElementById('graph-data').textContent);

// Extract data for net_worth chart
const categoriesDates = graphData.categories_dates;  // X-axis (dates)
const categoriesValues = graphData.categories_values;  // Y-axis for category values
const categoriesNotes = graphData.categories_notes;
const utilitiesValues = graphData.utilities_values;  // Y-axis for utilities values
const expensesValue = graphData.expenses_value;  // Y-axis for expenses values
const expensesNotes = graphData.expenses_notes;

// Create net_worth chart
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

// Create net_worth chart
const ctx = document.getElementById('categoryChart').getContext('2d');
const categoryChart = new Chart(ctx, {
    type: 'line', // Line chart
    data: {
        labels: categoriesDates,  // X-axis (dates)
        datasets: [
            {
                label: 'Category Values (£)',  // First line
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
