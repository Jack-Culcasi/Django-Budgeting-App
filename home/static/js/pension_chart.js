// Parse graph data passed from Django
const graphData = JSON.parse(document.getElementById('graph-data').textContent);

// Extract data for the fixed cost chart
const dates = graphData.dates;  // X-axis (dates)
const pensionValue = graphData.pension_values;  // Y-axis for fixed cost values

// Create mixed chart
const ctx_1 = document.getElementById('pensionChart').getContext('2d');
const pensionChart = new Chart(ctx_1, {
    type: 'line', // Line chart
    data: {
        labels: dates,  // X-axis (dates)
        datasets: [
            {
                label: 'Pension Values (£)',  
                data: pensionValue,  
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderWidth: 2,
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

// Extract data for net_worth chart
const net_worth_values = graphData.net_worth_values;  // Y-axis (net worth values)
const net_worth_note = graphData.net_worth_notes; 

// Create net_worth chart
const ctx = document.getElementById('netWorthChart').getContext('2d');
const netWorthChart = new Chart(ctx, {
    type: 'line', // Line chart
    data: {
        labels: dates,  
        datasets: [{
            label: 'Net Worth (£)',
            data: net_worth_values,  
            borderColor: 'rgba(75, 192, 192, 1)',
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            borderWidth: 2,
            tooltip: {
                callbacks: {
                    label: function(tooltipItem) {
                        const index = tooltipItem.dataIndex;
                        const net_worth_note = graphData.net_worth_notes ? graphData.net_worth_notes[index] : '';
                        return net_worth_note ? `${tooltipItem.raw} - ${net_worth_note}` : tooltipItem.raw;
                    }
                }
            }
        }]
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
                    text: 'Net Worth (£)',
                },
                beginAtZero: true,
            },
        },
    }
});