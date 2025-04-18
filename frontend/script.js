document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const fileInfo = document.getElementById('fileInfo');
    const calculateBtn = document.getElementById('calculateBtn');
    const resultsSection = document.getElementById('resultsSection');
    const totalProfit = document.getElementById('totalProfit');
    const dailyResults = document.getElementById('dailyResults').getElementsByTagName('tbody')[0];

    let currentFile = null;

    // Drag and drop handlers
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        dropZone.classList.add('drag-over');
    }

    function unhighlight() {
        dropZone.classList.remove('drag-over');
    }

    dropZone.addEventListener('drop', handleDrop, false);
    fileInput.addEventListener('change', handleFileSelect, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    function handleFileSelect(e) {
        const files = e.target.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        if (files.length > 0) {
            currentFile = files[0];
            fileInfo.textContent = `已选择文件: ${currentFile.name} (${formatFileSize(currentFile.size)})`;
            calculateBtn.disabled = false;
        }
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    calculateBtn.addEventListener('click', () => {
        if (!currentFile) return;

        const formData = new FormData();
        formData.append('file', currentFile);
        formData.append('strategy', document.querySelector('input[name="strategy"]:checked').value);

        calculateBtn.disabled = true;
        calculateBtn.textContent = '计算中...';

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            displayResults(data);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('处理文件时出错。');
        })
        .finally(() => {
            calculateBtn.disabled = false;
            calculateBtn.textContent = '计算收益';
        });
    });

    function displayResults(data) {
        resultsSection.style.display = 'block';
        totalProfit.textContent = `$${data.total_profit.toFixed(2)} AUD`;

        // Clear previous results
        dailyResults.innerHTML = '';

        // Populate daily results table
        data.daily_profits.forEach(day => {
            const row = dailyResults.insertRow();
            row.insertCell(0).textContent = day.date;
            row.insertCell(1).textContent = `${day.charge_start} - ${day.charge_end}`;
            row.insertCell(2).textContent = `$${day.charge_price.toFixed(2)}`;
            row.insertCell(3).textContent = `${day.discharge_start} - ${day.discharge_end}`;
            row.insertCell(4).textContent = `$${day.discharge_price.toFixed(2)}`;
            row.insertCell(5).textContent = `$${day.profit.toFixed(2)}`;
        });

        // Create charts
        createPriceChart(data.chart_data);
        createProfitChart(data.chart_data);
    }

    function createPriceChart(chartData) {
        const trace = {
            x: chartData.dates,
            y: chartData.price_diffs,
            type: 'bar',
            name: '价差',
            marker: {
                color: '#3498db'
            }
        };

        const layout = {
            title: '每日充放电价差',
            xaxis: { 
                title: '日期',
                tickangle: -45
            },
            yaxis: { 
                title: '价差 (AUD/MWh)',
                zeroline: true
            },
            margin: {
                b: 100  // 增加底部边距以显示完整的日期
            }
        };

        Plotly.newPlot('priceChart', [trace], layout);
    }

    function createProfitChart(chartData) {
        // 每日收益柱状图
        const dailyProfitTrace = {
            x: chartData.dates,
            y: chartData.daily_profits,
            type: 'bar',
            name: '日收益',
            marker: {
                color: '#e74c3c'
            }
        };

        // 累计收益折线图
        const cumulativeProfitTrace = {
            x: chartData.dates,
            y: chartData.cumulative_profits,
            type: 'scatter',
            mode: 'lines+markers',
            name: '累计收益',
            line: {
                color: '#2ecc71',
                width: 2
            },
            marker: {
                size: 6
            },
            yaxis: 'y2'  // 使用第二个y轴
        };

        const layout = {
            title: '收益分布',
            xaxis: { 
                title: '日期',
                tickangle: -45
            },
            yaxis: { 
                title: '日收益 (AUD)',
                zeroline: true
            },
            yaxis2: {
                title: '累计收益 (AUD)',
                overlaying: 'y',
                side: 'right',
                zeroline: true
            },
            margin: {
                b: 100  // 增加底部边距以显示完整的日期
            },
            legend: {
                x: 1.1,
                y: 1
            },
            showlegend: true
        };

        Plotly.newPlot('profitChart', [dailyProfitTrace, cumulativeProfitTrace], layout);
    }
}); 