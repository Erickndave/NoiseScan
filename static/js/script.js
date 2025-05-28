// Configuração do Gráfico
const ctx = document.getElementById('ruidoChart').getContext('2d');
const chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'Nível de Ruído (dB)',
            data: [],
            borderColor: 'rgba(78, 115, 223, 1)',
            backgroundColor: 'rgba(78, 115, 223, 0.05)',
            borderWidth: 2,
            pointRadius: 3,
            fill: true
        }]
    },
    options: {
        responsive: true,
        scales: {
            y: {
                beginAtZero: false,
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
        },
        plugins: {
            tooltip: {
                mode: 'index',
                intersect: false
            }
        }
    }
});

// Atualização Automática
function atualizarDashboard() {
    fetch('/api/dados')
        .then(response => response.json())
        .then(data => {
            // Atualiza gráfico
            const now = new Date();
            const timeString = now.toLocaleTimeString();
            
            chart.data.labels.push(timeString);
            chart.data.datasets[0].data.push(data.nivel_ruido);
            
            // Mantém apenas os últimos 20 pontos
            if (chart.data.labels.length > 20) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
            }
            
            chart.update();
            
            // Atualiza cards
            document.getElementById('mediaAtual').textContent = 
                data.nivel_ruido.toFixed(1) + ' dB';
            
            // Calcula mínimo/máximo (simulação)
            const valores = chart.data.datasets[0].data;
            document.getElementById('minimo').textContent = 
                Math.min(...valores).toFixed(1) + ' dB';
            document.getElementById('maximo').textContent = 
                Math.max(...valores).toFixed(1) + ' dB';
        });
}

// Atualização a cada 5 segundos
setInterval(atualizarDashboard, 5000);

// Botão manual
document.getElementById('atualizarBtn').addEventListener('click', atualizarDashboard);

// Inicialização
window.onload = atualizarDashboard;