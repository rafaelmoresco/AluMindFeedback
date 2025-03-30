// Dashboard chart initialization
function initializeSentimentChart(sentimentData) {
    const labels = sentimentData.map(item => item.sentiment);
    const counts = sentimentData.map(item => item.count);
    const percentages = sentimentData.map(item => item.percentage);

    const ctx = document.getElementById('sentimentChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Feedbacks',
                data: counts,
                backgroundColor: labels.map(label => {
                    switch(label) {
                        case 'POSITIVO': return 'rgba(75, 192, 192, 0.2)';
                        case 'NEGATIVO': return 'rgba(255, 99, 132, 0.2)';
                        default: return 'rgba(108, 117, 125, 0.2)';  // Grey for INCONCLUSIVO
                    }
                }),
                borderColor: labels.map(label => {
                    switch(label) {
                        case 'POSITIVO': return 'rgba(75, 192, 192, 1)';
                        case 'NEGATIVO': return 'rgba(255, 99, 132, 1)';
                        default: return 'rgba(108, 117, 125, 1)';  // Grey for INCONCLUSIVO
                    }
                }),
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const percentage = percentages[context.dataIndex];
                            if (percentage !== null) {
                                return `Count: ${context.raw} (${percentage}%)`;
                            }
                            return `Count: ${context.raw}`;
                        }
                    }
                }
            }
        }
    });
}

// Feedback form submission handler
function initializeFeedbackForm() {
    const form = document.getElementById('feedbackForm');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const feedbackData = {
                id: document.getElementById('feedbackId').value,
                feedback: document.getElementById('feedbackText').value
            };
            
            try {
                const response = await fetch('/feedbacks', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(feedbackData)
                });
                
                const result = await response.json();
                const messageDiv = document.getElementById('responseMessage');
                
                if (response.ok) {
                    messageDiv.className = 'alert alert-success';
                    messageDiv.textContent = result.message;
                    form.reset();
                } else {
                    messageDiv.className = 'alert alert-danger';
                    messageDiv.textContent = result.error;
                }
                
                messageDiv.style.display = 'block';
            } catch (error) {
                console.error('Error:', error);
                const messageDiv = document.getElementById('responseMessage');
                messageDiv.className = 'alert alert-danger';
                messageDiv.textContent = 'An error occurred while submitting feedback';
                messageDiv.style.display = 'block';
            }
        });
    }
}

// Initialize all scripts
document.addEventListener('DOMContentLoaded', function() {
    // Initialize feedback form if it exists
    initializeFeedbackForm();
    
    // Initialize sentiment chart if we're on the dashboard page
    const sentimentData = window.sentimentData;
    if (sentimentData) {
        initializeSentimentChart(sentimentData);
    }
});
