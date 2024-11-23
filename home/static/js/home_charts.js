// Get the data passed from Django
const graphData = JSON.parse(document.getElementById('graph-data').textContent);

// Extract data for net_worth chart
const labels = graphData.dates;  // X-axis (dates)
const dataValues = graphData.net_worth_values;  // Y-axis (net worth values)
// Extract data for savings chart
const savingsValues = graphData.savings_values;  // Y-axis (savings values)
// Extract data for savings chart
const investmentsValues = graphData.investments_values;  // Y-axis (investments values)
// Extract data for savings chart
const expensesValues = graphData.expenses_values;  // Y-axis (expenses values)  
// Extract data for pie chart
const savings = graphData.savings; 
const investments = graphData.investments;
const pension = graphData.pensions;
const pac = graphData.pac;
const net_worth_note = graphData.net_worth_notes; 
const monthly_expenses_note = graphData.monthly_expenses_notes;

// Create net_worth chart
const ctx = document.getElementById('netWorthChart').getContext('2d');
const netWorthChart = new Chart(ctx, {
    type: 'line', // Line chart
    data: {
        labels: labels,  
        datasets: [{
            label: 'Net Worth (£)',
            data: dataValues,  
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

  // Create net_worth chart
  const ctx_1 = document.getElementById('savingsChart').getContext('2d');
  const savingsChart = new Chart(ctx_1, {
      type: 'line', // Line chart
      data: {
          labels: labels,
          datasets: [{
              label: 'Savings (£)',
              data: savingsValues,
              borderColor: 'rgba(255, 159, 64, 1)',
              backgroundColor: 'rgba(255, 159, 64, 0.2)',
              borderWidth: 2,
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
                      text: 'Savings (£)',
                  },
                  beginAtZero: true,
              },
          },
      }
  });

  // Create net_worth chart
  const ctx_2 = document.getElementById('investmentsChart').getContext('2d');
  const investmentsChart = new Chart(ctx_2, {
      type: 'line', // Line chart
      data: {
          labels: labels,
          datasets: [{
              label: 'Investments (£)',
              data: investmentsValues,
              borderColor: 'rgba(153, 102, 255, 1)',
              backgroundColor: 'rgba(153, 102, 255, 0.2)',
              borderWidth: 2,
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
                      text: 'Investments (£)',
                  },
                  beginAtZero: true,
              },
          },
      }
  });

  // Create net_worth chart
  const ctx_3 = document.getElementById('expensesChart').getContext('2d');
  const expensesChart = new Chart(ctx_3, {
      type: 'line', // Line chart
      data: {
          labels: labels,
          datasets: [{
              label: 'Expenses (£)',
              data: expensesValues,
              borderColor: 'rgba(255, 99, 132, 1)',
              backgroundColor: 'rgba(255, 99, 132, 0.2)',
              borderWidth: 2,
              tooltip: {
                callbacks: {
                    label: function(tooltipItem) {
                        const index = tooltipItem.dataIndex;
                        const monthly_expenses_note = graphData.monthly_expenses_notes ? graphData.monthly_expenses_notes[index] : '';
                        return monthly_expenses_note ? `${tooltipItem.raw} - ${monthly_expenses_note}` : tooltipItem.raw;
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
                      text: 'Expenses (£)',
                  },
                  beginAtZero: true,
              },
          },
      }
  });

// Pie chart
const ctx_4 = document.getElementById('myPieChart').getContext('2d');
const myPieChart = new Chart(ctx_4, {
    type: 'pie',
    data: {
        labels: ['Savings', 'Investments', 'PAC', 'Pension'],
        datasets: [{
            label: 'Amount',
            data: [savings, investments, pac, pension],
            backgroundColor: ['#003366', '#5C6BC0', '#388E3C', '#FFB300'],
            borderColor: ['black', 'black', 'black', 'black'],
            borderWidth: 1
        }]
    },
    options: {
        responsive: true
    }
});
