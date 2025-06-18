document.addEventListener('DOMContentLoaded', function() {
    initializeChart();
    fetchData();
    setInterval(fetchData, 30000); // Atualiza a cada 30 segundos
});

let noiseChart;

function initializeChart() {
    const ctx = document.getElementById('ruidoChart').getContext('2d');
    noiseChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Nível de Ruído (dB)',
                data: [],
                borderColor: '#4e73df',
                backgroundColor: 'rgba(78, 115, 223, 0.1)',
                borderWidth: 2,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    min: 30,
                    max: 120,
                    title: {
                        display: true,
                        text: 'Decibéis (dB)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Horário'
                    }
                }
            }
        }
    });
}

// Função para ajustar o horário (subtrai 3 horas)
function adjustTime(dateTimeString) {
    const date = new Date(dateTimeString);
    date.setHours(date.getHours() - 3);  // Subtrai 3 horas
    return date.toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

async function fetchData() {
    try {
        const response = await fetch('/api/ultimos-dados?t=' + Date.now());
        const result = await response.json();
        
        if (result.status === "success") {
            updateChart(result.data);
            updateStatus(result.data);
            updateTable(result.data);
            updateTimestamp();
        }
    } catch (error) {
        console.error("Erro:", error);
    }
}

function updateChart(data) {
    const labels = data.map(item => adjustTime(item.data_hora));
    const levels = data.map(item => item.nivel_ruido);

    noiseChart.data.labels = labels;
    noiseChart.data.datasets[0].data = levels;
    noiseChart.update();
}

function updateTable(data) {
    const tbody = document.querySelector('#dados-table tbody');
    tbody.innerHTML = '';
    
    data.slice(0, 20).forEach(item => {
        const row = document.createElement('tr');
        const level = item.nivel_ruido;
        
        row.className = level > 80 ? 'table-danger' : 
                       level > 40 ? 'table-warning' : '';
        
        row.innerHTML = `
            <td>${adjustTime(item.data_hora)}</td>
            <td>${level.toFixed(1)}</td>
            <td>
                ${level > 80 ? '<span class="badge bg-danger">Alto</span>' : 
                 level > 40 ? '<span class="badge bg-warning">Moderado</span>' : 
                 '<span class="badge bg-success">Normal</span>'}
            </td>
            <td>Área de Pacientes</td>
        `;
        
        tbody.appendChild(row);
    });
}

function updateStatus(data) {
    if (!data || data.length === 0) return;
    
    const latest = data[data.length - 1];
    const level = latest.nivel_ruido;
    const statusElement = document.getElementById('status-ruido');
    const textElement = document.getElementById('status-texto');
    const iconElement = document.getElementById('status-icon');
    
    document.getElementById('current-level').textContent = level.toFixed(1) + ' dB';
    
    if (level > 80) {
        statusElement.style.backgroundColor = '#e74a3b';
        textElement.textContent = 'Nível Crítico!';
        iconElement.className = 'fas fa-exclamation-triangle';
    } else if (level > 40) {
        statusElement.style.backgroundColor = '#f6c23e';
        textElement.textContent = 'Nível Moderado';
        iconElement.className = 'fas fa-exclamation-circle';
    } else {
        statusElement.style.backgroundColor = '#1cc88a';
        textElement.textContent = 'Nível Normal';
        iconElement.className = 'fas fa-check-circle';
    }
}

function updateTimestamp() {
    // Remove a linha que subtrai 3 horas
    const now = new Date();
    document.getElementById('last-update').textContent =   
        'Última atualização: ' + now.toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
}