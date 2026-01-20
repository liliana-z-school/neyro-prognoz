const companyInput = document.getElementById("company");
const periodSelect = document.getElementById("period");
const forecastBtn = document.getElementById("forecast-btn");
let chart;

const defaultCompany = "Apple";

const periodMap = {
    "1 день": "1d",
    "1 неделя": "5d",
    "1 месяц": "1mo"
};

const forecastResultDiv = document.createElement('div');
forecastResultDiv.id = 'forecast-result';
forecastResultDiv.style.cssText = `
    margin: 20px 0;
    padding: 20px;
    background-color: rgba(232, 220, 194, 0.15);
    border-radius: 10px;
    text-align: center;
    display: none;
    border: 2px solid rgba(232, 220, 194, 0.3);
    animation: fadeInScale 0.5s ease-out;
`;

const style = document.createElement('style');
style.textContent = `
    @keyframes fadeInScale {
        from {
            opacity: 0;
            transform: scale(0.95) translateY(-10px);
        }
        to {
            opacity: 1;
            transform: scale(1) translateY(0);
        }
    }
    
    #forecast-result {
        transition: all 0.3s ease;
    }
`;
document.head.appendChild(style);
document.getElementById('controls').appendChild(forecastResultDiv);

async function loadChart(company = defaultCompany) {
    const periodText = periodSelect.value;
    const period = periodMap[periodText] || "1mo";
    const selectedCompany = companyInput.value.trim() || company;

    console.log(`🔄 Загрузка: ${selectedCompany}, период=${period}`);

    const welcomeMsg = document.getElementById('welcome-message');
    const chartCanvas = document.getElementById('chart');
    if (welcomeMsg) welcomeMsg.style.display = 'none';
    if (chartCanvas) chartCanvas.style.display = 'block';

    forecastBtn.disabled = true;
    forecastBtn.textContent = "Загрузка...";
    forecastResultDiv.style.display = 'none';

    // Уничтожаем график ДО запроса
    if (chart) {
        chart.destroy();
        chart = null;
    }

    try {
        // Добавляем timestamp для избежания кэширования
        const timestamp = new Date().getTime();
        const response = await fetch(`/get_data?company=${encodeURIComponent(selectedCompany)}&period=${encodeURIComponent(period)}&_t=${timestamp}`);
        const data = await response.json();

        if (data.error || !data.time || data.time.length === 0) {
            alert(data.error || "Не удалось загрузить данные. Попробуйте позже.");
            return;
        }

        console.log(`✅ Получено ${data.time.length} точек, тренд: ${data.trend}, уверенность: ${data.confidence}%`);

        const priceData = data.time.map((t, i) => ({
            x: new Date(t),
            y: data.close[i]
        }));

        const forecastLine = data.forecast_line.map((v, i) => ({
            x: new Date(data.time[i]),
            y: v
        })).filter(item => item.y !== null);

        const firstPrice = data.close[0];
        const lastPrice = data.close[data.close.length - 1];
        const priceChange = lastPrice - firstPrice;
        const priceChangePct = ((lastPrice / firstPrice - 1) * 100).toFixed(2);
        const changeColor = priceChange >= 0 ? "#00b06b" : "#c00000";
        const changeSign = priceChange >= 0 ? "+" : "";

        const trendColor = data.trend === "вверх" ? "#00b06b" : data.trend === "вниз" ? "#c00000" : "#ffa500";

        if (data.trend && data.confidence) {
            const trendIcon = data.trend === "вверх" ? "📈" : data.trend === "вниз" ? "📉" : "↔️";
            
            forecastResultDiv.innerHTML = `
                <div style="font-size: 32px; margin-bottom: 15px;">${trendIcon}</div>
                <div style="color: ${trendColor}; font-weight: bold; font-size: 26px; margin-bottom: 15px;">
                    Прогноз AI: ${data.trend.toUpperCase()}
                </div>
                <div style="margin-top: 15px; font-size: 18px; color: #e8dcca; margin-bottom: 10px;">
                    Уверенность: <span style="font-weight: bold; font-size: 22px;">${data.confidence}%</span>
                </div>
                <div style="border-top: 1px solid rgba(232, 220, 194, 0.3); padding-top: 15px; margin-top: 15px;">
                    <div style="font-size: 16px; color: #e8dcca; margin-bottom: 8px;">
                        Цена: <span style="font-weight: bold;">$${firstPrice.toFixed(2)}</span> → <span style="font-weight: bold;">$${lastPrice.toFixed(2)}</span>
                    </div>
                    <div style="font-size: 18px; color: ${changeColor}; font-weight: bold;">
                        Изменение: ${changeSign}$${Math.abs(priceChange).toFixed(2)} (${changeSign}${priceChangePct}%)
                    </div>
                </div>
            `;
            forecastResultDiv.style.display = 'block';
        }

        const ctx = document.getElementById("chart").getContext("2d");

        const russianMonths = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];

        chart = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: `${selectedCompany} - Реальная цена`,
                        data: priceData,
                        borderColor: trendColor,
                        backgroundColor: `${trendColor}33`,
                        borderWidth: 3,
                        pointRadius: 2,
                        pointHoverRadius: 5,
                        pointBackgroundColor: trendColor,
                        fill: true,
                        tension: 0.1
                    },
                    {
                        label: "Прогноз AI", // Убрали EMA
                        data: forecastLine,
                        borderColor: "#E8DCC2",
                        backgroundColor: "rgba(232, 220, 194, 0.05)",
                        borderWidth: 4,
                        borderDash: [10, 5],
                        pointRadius: 0,
                        fill: false,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: { 
                    legend: { 
                        display: true,
                        position: 'top',
                        labels: {
                            color: "#1a1a1a",
                            font: {
                                size: 14,
                                family: "Arial",
                                weight: "bold"
                            },
                            usePointStyle: true,
                            padding: 15
                        }
                    },
                    tooltip: {
                        enabled: false // ПОЛНОСТЬЮ ОТКЛЮЧИЛИ ВСПЛЫВАЮЩЕЕ ОКНО
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: { 
                            unit: period === '1d' ? 'hour' : 'day',
                            displayFormats: {
                                hour: 'HH:mm',
                                day: 'd MMM'
                            }
                        },
                        ticks: { 
                            color: "#1a1a1a", 
                            font: { 
                                family: "Arial", 
                                size: 11,
                                weight: "600"
                            },
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 10,
                            callback: function(value, index, ticks) {
                                const date = new Date(value);
                                const day = date.getDate();
                                const monthIndex = date.getMonth();
                                
                                if (period === '1d') {
                                    return String(date.getHours()).padStart(2, '0') + ':' + String(date.getMinutes()).padStart(2, '0');
                                } else {
                                    return day + ' ' + russianMonths[monthIndex];
                                }
                            }
                        },
                        grid: { 
                            color: "#e5e5e5",
                            drawBorder: true
                        }
                    },
                    y: {
                        position: 'right',
                        ticks: { 
                            color: "#1a1a1a", 
                            font: { 
                                family: "Arial", 
                                size: 12,
                                weight: "600"
                            },
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        },
                        grid: { 
                            color: "#e5e5e5",
                            drawBorder: true
                        }
                    }
                }
            }
        });

        console.log("✅ График создан");

    } catch (error) {
        console.error("❌ Ошибка:", error);
        alert("Произошла ошибка при загрузке данных: " + error.message);
    } finally {
        forecastBtn.disabled = false;
        forecastBtn.textContent = "Прогноз";
    }
}

forecastBtn.addEventListener("click", () => {
    const selectedCompany = companyInput.value.trim() || defaultCompany;
    loadChart(selectedCompany);
});

window.addEventListener("load", () => {
    companyInput.value = "";
});

console.log("📊 Скрипт загружен v15 (Без тултипа)");