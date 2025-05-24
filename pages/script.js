/*
© Copyrights 2025 Zeromi Studio. All Rights Reserved.

Author:Benxp
Date:2025/05/24
Time:20:42:19

==============================
前后端交互代码/页面数据分析代码
==============================

请严格遵循开源协议，严禁二次倒卖、贩卖
保留所有权利
*/


// DOM元素
const searchForm = document.getElementById('searchForm');
const bvidInput = document.getElementById('bvidInput');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const errorMessage = document.getElementById('errorMessage');
const result = document.getElementById('result');
const copyButton = document.getElementById('copyButton');
const copyToast = document.getElementById('copyToast');

// 获取单个视频分析页面元素
const singleVideoAnalysis = document.getElementById('singleVideoAnalysis');
const singleAnalysisContent = document.getElementById('singleAnalysisContent');

// 获取对比分析页面元素
const compareButton = document.getElementById('compareButton');
const compareResult = document.getElementById('compareResult');
const compareChart = document.getElementById('compareChart');
const compareConclusion = document.getElementById('compareConclusion');
let chartInstance = null;

// 表单提交（单稿）
searchForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const bvid = bvidInput.value.trim();
    
    if (!bvid) {
        showError('请输入有效的BV号');
        return;
    }

    // 验证BV号格式
    const bvidPattern = /^BV[A-Za-z0-9]{10}$/;
    if (!bvidPattern.test(bvid)) {
        showError('BV号格式不正确，应为"BV"开头，后面跟着10位字母和数字');
        return;
    }

    // 加载
    showLoading(true);
    showError(false);
    showResult(false);
    compareResult.style.display = 'none';
    
    if (singleVideoAnalysis) {
        singleVideoAnalysis.style.display = 'none';
    }

    try {
        const response = await fetch(`api/getData?bvid=${bvid}`);
        
        if (!response.ok) {
            throw new Error(`API请求失败，状态码: ${response.status}`);
        }

        const data = await response.json();
        
        if (!data) {
            throw new Error('获取数据失败，API返回格式不正确');
        }

        displayData(data);
        showResult(true);
        
        animateRateBars();
        
        if (singleVideoAnalysis && singleAnalysisContent) {
            singleVideoAnalysis.style.display = 'block';
            await fetchAndDisplaySingleVideoAnalysis(bvid);
        }
    } catch (err) {
        console.error('请求出错:', err);
        showError(err.message || '获取视频信息失败，请稍后再试');
    } finally {
        showLoading(false);
    }
});

// 初始化对比功能
compareButton.addEventListener('click', async () => {
    const bvids = [
        document.getElementById('bvid1').value.trim(),
        document.getElementById('bvid2').value.trim(),
        document.getElementById('bvid3').value.trim()
    ].filter(bvid => bvid);

    if (bvids.length < 2) {
        showError('至少需要输入2个BV号进行对比');
        return;
    }

    if (bvids.length > 3) {
        showError('最多支持3个视频对比');
        return;
    }

    // 验证BV号格式
    const invalidBvid = bvids.find(bvid => !/^BV[A-Za-z0-9]{10}$/.test(bvid));
    if (invalidBvid) {
        showError('BV号格式不正确：' + invalidBvid);
        return;
    }

    showLoading(true);
    showError(false);
    showResult(false);
    compareResult.style.display = 'none';
    
    if (singleVideoAnalysis) {
        singleVideoAnalysis.style.display = 'none';
    }

    try {
        // 并行获取多个视频数据
        const dataList = await Promise.all(
            bvids.map(async bvid => {
                const response = await fetch(`api/getData?bvid=${bvid}`);
                if (!response.ok) throw new Error(`获取${bvid}数据失败`);
                return await response.json();
            })
        );

        // 渲染对比结果
        renderCompareResult(dataList, bvids);
        compareResult.style.display = 'block';
    } catch (err) {
        console.error('对比出错:', err);
        showError(err.message || '对比失败，请检查BV号或网络');
    } finally {
        showLoading(false);
    }
});

// 显示/隐藏加载状态
function showLoading(show) {
    loading.style.display = show ? 'block' : 'none';
}

// 显示/隐藏错误信息
function showError(message) {
    if (typeof message === 'string') {
        errorMessage.textContent = message;
        error.style.display = 'block';
    } else {
        error.style.display = 'none';
    }
}

// 显示/隐藏结果
function showResult(show) {
    result.style.display = show ? 'block' : 'none';
}

// 处理并显示数据
function displayData(data) {
    // 基本信息
    document.getElementById('videoTitle').textContent = data.title || '未知标题';
    document.getElementById('detailBvid').textContent = data.bvid || '未知';
    document.getElementById('viewCount').textContent = formatNumber(data.view) + ' 次播放';
    document.getElementById('danmakuCount').textContent = formatNumber(data.danmaku) + ' 条弹幕';
    document.getElementById('likeCount').textContent = formatNumber(data.like) + ' 点赞';
    document.getElementById('publishTime').textContent = formatDate(new Date(data.pubdate * 1000));
    
    // 视频简介
    document.getElementById('videoDesc').textContent = data.desc || '暂无简介';
    
    // 视频信息
    document.getElementById('aid').textContent = data.aid ? `av${data.aid}` : '未知';
    document.getElementById('pubdate').textContent = formatDateTime(new Date(data.pubdate * 1000));
    document.getElementById('ctime').textContent = formatDateTime(new Date(data.ctime * 1000));
    document.getElementById('duration').textContent = formatDuration(data.duration) || '未知时长';
    
    // 互动数据
    document.getElementById('coinCount').textContent = formatNumber(data.coin);
    document.getElementById('favoriteCount').textContent = formatNumber(data.favorite);
    document.getElementById('replyCount').textContent = formatNumber(data.reply);
    document.getElementById('shareCount').textContent = formatNumber(data.share);
    
    // B站链接
    document.getElementById('bilibiliLink').href = `https://www.bilibili.com/video/${data.bvid || ''}`;
    
    // 调用下方函数
    calculateAndDisplayRates(data);
}

// 计算并显示互动分析数据
function calculateAndDisplayRates(data) {
    const view = data.view || 0;
    const like = data.like || 0;
    const coin = data.coin || 0;
    const reply = data.reply || 0;
    const danmaku = data.danmaku || 0;
    
    // 计算比率
    const likeRate = view > 0 ? ((like / view) * 100).toFixed(2) : 0;
    const coinRate = view > 0 ? ((coin / view) * 100).toFixed(2) : 0;
    const interactionRate = view > 0 ? (((reply + danmaku) / view) * 100).toFixed(2) : 0;
    
    // 设置比率显示文本
    document.getElementById('likeRate').textContent = `${likeRate}%`;
    document.getElementById('coinRate').textContent = `${coinRate}%`;
    document.getElementById('interactionRate').textContent = `${interactionRate}%`;
    
    // 设置进度条颜色和最终宽度
    document.getElementById('likeRateBar').dataset.targetWidth = likeRate;
    document.getElementById('coinRateBar').dataset.targetWidth = coinRate;
    document.getElementById('interactionRateBar').dataset.targetWidth = interactionRate;
    
    // 根据比率设置颜色
    setRateColor('likeRate', likeRate);
    setRateColor('coinRate', coinRate);
    setRateColor('interactionRate', interactionRate);
}

// 根据比率设置颜色
function setRateColor(elementId, rate) {
    const element = document.getElementById(elementId);
    const rateValue = parseFloat(rate);
    
    if (rateValue >= 10) {
        element.className = 'font-medium text-rate-excellent';
    } else if (rateValue >= 5) {
        element.className = 'font-medium text-rate-good';
    } else if (rateValue >= 2) {
        element.className = 'font-medium text-rate-fair';
    } else {
        element.className = 'font-medium text-rate-poor';
    }
}

// 进度条
function animateRateBars() {
    const bars = document.querySelectorAll('.progress-value');
    bars.forEach(bar => {
        const targetWidth = bar.dataset.targetWidth || 0;
        setTimeout(() => {
            bar.style.width = `${targetWidth}%`;
        }, 300);
    });
}

// 渲染对比结果
function renderCompareResult(dataList, bvids) {
    // 处理数据
    const videos = dataList.map((data, index) => {
        const view = data.view || 0;
        const like = data.like || 0;
        const coin = data.coin || 0;
        const reply = data.reply || 0;
        const danmaku = data.danmaku || 0;
        
        return {
            title: data.title || `视频${index+1}`,
            bvid: data.bvid,
            view,
            like,
            coin,
            favorite: data.favorite || 0,
            reply,
            danmaku,
            likeRate: view > 0 ? (like / view * 100).toFixed(2) : 0,
            coinRate: view > 0 ? (coin / view * 100).toFixed(2) : 0,
            interactionRate: view > 0 ? ((reply + danmaku) / view * 100).toFixed(2) : 0,
            pubdate: new Date(data.pubdate * 1000)
        };
    });

    // 渲染
    renderChart(videos);
    renderCompareTable(videos);
    generateConclusion(videos);
}

// 绘制对比图表
function renderChart(videos) {
    if (chartInstance) {
        chartInstance.destroy();
    }
    
    const labels = videos.map(video => video.title);
    const datasets = [
        {
            label: '播放量',
            data: videos.map(video => video.view),
            backgroundColor: 'rgba(251, 114, 153, 0.6)',
            borderColor: '#FB7299',
            borderWidth: 1,
            yAxisID: 'y'
        },
        {
            label: '点赞数',
            data: videos.map(video => video.like),
            backgroundColor: 'rgba(35, 173, 229, 0.6)',
            borderColor: '#23ADE5',
            borderWidth: 1,
            yAxisID: 'y'
        },
        {
            label: '互动率(%)',
            data: videos.map(video => video.interactionRate),
            backgroundColor: 'rgba(54, 211, 153, 0.6)',
            borderColor: '#36D399',
            borderWidth: 1,
            type: 'line',
            yAxisID: 'y1'
        }
    ];

    const config = {
        type: 'bar',
        data: {
            labels,
            datasets
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    type: 'logarithmic',
                    display: true,
                    title: {
                        display: true,
                        text: '数值(对数刻度)'
                    },
                    min: 1
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: '互动率(%)'
                    },
                    min: 0,
                    max: 100,
                    grid: {
                        drawOnChartArea: false,
                    }
                }
            },
            animation: {
                duration: 2000,
                easing: 'easeOutQuart'
            }
        }
    };

    chartInstance = new Chart(compareChart, config);
}

// 渲染对比表格
function renderCompareTable(videos) {
    const tableBody = document.getElementById('compareTableBody');
    tableBody.innerHTML = '';

    // 设置表头
    document.getElementById('video1Header').textContent = videos[0].title;
    document.getElementById('video2Header').textContent = videos[1]?.title || '';
    document.getElementById('video3Header').textContent = videos[2]?.title || '';
    
    // 隐藏空列
    document.querySelectorAll('th.md\\:table-cell, th.lg\\:table-cell').forEach((th, index) => {
        th.style.display = videos[index] ? 'table-cell' : 'none';
    });

    // 定义要比较的指标
    const metrics = [
        { key: 'bvid', label: 'BV号', format: (v) => v },
        { key: 'view', label: '播放量', format: (v) => formatNumber(v) },
        { key: 'like', label: '点赞数', format: (v) => formatNumber(v) },
        { key: 'likeRate', label: '点赞率', format: (v) => `${v}%` },
        { key: 'coin', label: '硬币数', format: (v) => formatNumber(v) },
        { key: 'coinRate', label: '投币率', format: (v) => `${v}%` },
        { key: 'favorite', label: '收藏数', format: (v) => formatNumber(v) },
        { key: 'reply', label: '评论数', format: (v) => formatNumber(v) },
        { key: 'danmaku', label: '弹幕数', format: (v) => formatNumber(v) },
        { key: 'interactionRate', label: '互动率', format: (v) => `${v}%` },
        { key: 'pubdate', label: '发布时间', format: (v) => formatDate(v) }
    ];

    // 为每个指标创建表格行
    metrics.forEach(({ key, label, format }) => {
        const tr = document.createElement('tr');
        tr.className = 'compare-row';
        
        // 添加指标名称单元格
        const th = document.createElement('th');
        th.className = 'compare-cell compare-header';
        th.textContent = label;
        th.scope = 'row';
        tr.appendChild(th);
        
        // 添加视频数据单元格
        const values = videos.map(video => video[key]);
        const maxValue = Math.max(...values);
        
        videos.forEach(video => {
            const td = document.createElement('td');
            td.className = 'compare-cell compare-value';
            
            // 高亮最大值
            if (video[key] === maxValue && maxValue > 0) {
                td.classList.add('compare-highlight');
            }
            
            td.textContent = format(video[key]);
            tr.appendChild(td);
        });
        
        tableBody.appendChild(tr);
    });
}

// 生成对比结论
function generateConclusion(videos) {
    const conclusionElement = document.getElementById('compareConclusion');
    let conclusion = '';
    
    // 播放量
    const viewMax = Math.max(...videos.map(v => v.view));
    const viewWinners = videos.filter(v => v.view === viewMax);
    conclusion += `播放量最高的视频是：${viewWinners.map(v => v.title).join('、')}（${formatNumber(viewMax)}）。`;
    
    // 互动率
    const interactionMax = Math.max(...videos.map(v => v.interactionRate));
    const interactionWinners = videos.filter(v => v.interactionRate === interactionMax);
    conclusion += `互动率最高的视频是：${interactionWinners.map(v => v.title).join('、')}（${interactionMax}%）。`;
    
    // 发布时间
    const oldestVideo = videos.reduce((prev, curr) => prev.pubdate < curr.pubdate ? prev : curr);
    const newestVideo = videos.reduce((prev, curr) => prev.pubdate > curr.pubdate ? prev : curr);
    conclusion += `${oldestVideo.title} 发布最早（${formatDate(oldestVideo.pubdate)}），${newestVideo.title} 发布最晚（${formatDate(newestVideo.pubdate)}）。`;
    
    conclusionElement.textContent = conclusion;
}

// 获取并显示评论动向分析
async function fetchAndDisplaySingleVideoAnalysis(bvid) {
    if (!singleAnalysisContent) return;
    
    try {
        // 加载
        singleAnalysisContent.innerHTML = '<div class="text-center py-4">正在生成评论动向分析数据...</div>';
        
        const response = await fetch(`api/getComment?bvid=${bvid}`);
        if (!response.ok) throw new Error(`获取评论分析失败，状态码: ${response.status}`);
        
        const rawContent = await response.text();
        
        if (rawContent) {
            // 处理Unicode
            const decodedContent = decodeUnicode(rawContent);
            
            // 替换换行符
            const formattedContent = decodedContent.replace(/\\n/g, '<br>');
            
            singleAnalysisContent.innerHTML = `
                <div class="p-3 bg-white rounded-lg shadow-sm">
                    <h5 class="font-semibold text-dark mb-2">
                        <i class="fa fa-file-text-o mr-2"></i>
                        视频分析数据
                    </h5>
                    <div class="text-gray-700 whitespace-pre-wrap">${formattedContent}</div>
                </div>
            `;
        } else {
            // 没有分析数据
            singleAnalysisContent.innerHTML = '<div class="text-center py-4 text-gray-500">暂无评论动向分析数据</div>';
        }
    } catch (err) {
        console.error('获取评论动向分析出错:', err);
        singleAnalysisContent.innerHTML = `<div class="text-center py-4 text-red-500">获取评论动向分析失败: ${err.message}</div>`;
    }
}

// 解码Unicode
function decodeUnicode(str) {
    return str.replace(/\\u([0-9a-fA-F]{4})/g, function(match, grp) {
        return String.fromCodePoint(parseInt(grp, 16));
    });
}

// 格式化数字
function formatNumber(num) {
    if (typeof num !== 'number') {
        return '0';
    }
    
    if (num >= 10000) {
        return (num / 10000).toFixed(1) + '万';
    }
    
    return num.toLocaleString();
}

// 格式化日期
function formatDate(date) {
    if (!(date instanceof Date)) {
        return '未知时间';
    }
    
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// 格式化日期时间
function formatDateTime(date) {
    if (!(date instanceof Date)) {
        return '未知时间';
    }
    
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// 格式化视频时长
function formatDuration(seconds) {
    if (typeof seconds !== 'number' || isNaN(seconds)) {
        return '未知时长';
    }
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}小时${minutes}分${secs}秒`;
    } else if (minutes > 0) {
        return `${minutes}分${secs}秒`;
    } else {
        return `${secs}秒`;
    }
}

/*
什么？你问这里是什么？这里是计划做黑夜模式和白天模式的切换的，但是后来放弃了（我太菜了qaq），要是你是大佬的话，你可以自己试试看，代码我给你留下来了（虽然是屎山）
*/
const themeToggle = document.getElementById('themeToggle');
const themeIcon = document.getElementById('themeIcon');

const isDarkMode = localStorage.getItem('theme') === 'dark';
if (isDarkMode) {
    document.body.classList.add('dark-mode');
    themeIcon.className = 'fa fa-sun';
} else {
    document.body.classList.remove('dark-mode');
    themeIcon.className = 'fa fa-moon';
}

themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
    const newMode = document.body.classList.contains('dark-mode');
    localStorage.setItem('theme', newMode ? 'dark' : 'light');
    
    themeIcon.className = newMode ? 'fa fa-sun' : 'fa fa-moon';
});