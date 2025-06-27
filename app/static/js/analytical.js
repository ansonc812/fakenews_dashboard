// Analytical Dashboard JavaScript

let charts = {};
let networkVisualization = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializeControls();
    loadAnalyticalData();
});

// Initialize controls and event listeners
function initializeControls() {
    document.getElementById('updateAnalysis').addEventListener('click', loadAnalyticalData);
    document.getElementById('dateRange').addEventListener('change', loadAnalyticalData);
    document.getElementById('categoryFilter').addEventListener('change', loadAnalyticalData);
    document.getElementById('analysisType').addEventListener('change', updateAnalysisType);
}

// Load all analytical data
async function loadAnalyticalData() {
    const days = document.getElementById('dateRange').value;
    const category = document.getElementById('categoryFilter').value;
    
    try {
        // Load all data in parallel
        const [
            temporalTrends,
            networkData,
            categoryPerformance,
            userBehavior,
            sourceTimeline,
            overviewStats
        ] = await Promise.all([
            apiRequest(`/analytical/temporal-trends?days=${days}`),
            apiRequest('/analytical/network-analysis?limit=50'),
            apiRequest('/analytical/category-performance?months=6'),
            apiRequest('/analytical/user-behavior'),
            apiRequest('/analytical/source-timeline?months=12'),
            apiRequest('/api/stats/overview')
        ]);
        
        updateSummaryMetrics(overviewStats, temporalTrends);
        updateTemporalTrends(temporalTrends);
        updateNetworkVisualization(networkData);
        updateCategoryDistribution(categoryPerformance);
        updateUserBehaviorChart(userBehavior);
        updateSourceTimeline(sourceTimeline);
        generateAnalysisResults();
        
    } catch (error) {
        console.error('Failed to load analytical data:', error);
        showError('analysisResults', 'Failed to load analytical data. Please try again.');
    }
}

// Update summary metrics
function updateSummaryMetrics(stats, trends) {
    document.getElementById('totalAnalyzed').textContent = formatNumber(stats.articles.total);
    
    // Calculate average spread time (simulated)
    const avgSpreadHours = Math.floor(Math.random() * 12 + 6);
    document.getElementById('avgSpreadTime').textContent = avgSpreadHours;
    
    // Calculate verified user impact
    const verifiedImpact = (stats.users.verified_percentage * 1.5).toFixed(1);
    document.getElementById('verifiedImpact').textContent = verifiedImpact + '%';
    
    // Calculate fake news growth rate
    if (trends && trends.length > 1) {
        const firstWeek = trends.slice(0, 7).reduce((sum, day) => sum + day.fake, 0);
        const lastWeek = trends.slice(-7).reduce((sum, day) => sum + day.fake, 0);
        const growthRate = ((lastWeek - firstWeek) / firstWeek * 100).toFixed(1);
        document.getElementById('fakeNewsGrowth').textContent = 
            (growthRate > 0 ? '+' : '') + growthRate + '%';
    }
}

// Update temporal trends chart
function updateTemporalTrends(data) {
    const ctx = document.getElementById('temporalTrendsChart').getContext('2d');
    
    if (charts.temporalTrends) {
        charts.temporalTrends.destroy();
    }
    
    // Prepare data for chart
    const dates = data.map(d => d.date);
    const fakeData = data.map(d => d.fake);
    const realData = data.map(d => d.real);
    
    charts.temporalTrends = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Fake News',
                    data: fakeData,
                    borderColor: 'rgb(139, 0, 0)',
                    backgroundColor: 'rgba(139, 0, 0, 0.2)',
                    tension: 0.4,
                    fill: true,
                    borderWidth: 3
                },
                {
                    label: 'Real News',
                    data: realData,
                    borderColor: 'rgb(0, 100, 0)',
                    backgroundColor: 'rgba(0, 100, 0, 0.2)',
                    tension: 0.4,
                    fill: true,
                    borderWidth: 3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        title: function(tooltipItems) {
                            return new Date(tooltipItems[0].label).toLocaleDateString('en-GB', {
                                weekday: 'short',
                                year: 'numeric',
                                month: 'short',
                                day: 'numeric'
                            });
                        },
                        afterBody: function(tooltipItems) {
                            const total = tooltipItems.reduce((sum, item) => sum + item.parsed.y, 0);
                            const fakePercentage = (tooltipItems[0].parsed.y / total * 100).toFixed(1);
                            return `\nTotal: ${total}\nFake %: ${fakePercentage}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        parser: 'yyyy-MM-dd',
                        tooltipFormat: 'MMM dd',
                        displayFormats: {
                            day: 'MMM dd'
                        }
                    },
                    ticks: {
                        maxRotation: 0,
                        autoSkip: true,
                        maxTicksLimit: 10
                    }
                },
                y: {
                    beginAtZero: true,
                    stacked: false
                }
            }
        }
    });
}

// Update network visualization using D3.js
function updateNetworkVisualization(data) {
    const container = d3.select('#networkVisualization');
    container.selectAll('*').remove();
    
    const width = container.node().getBoundingClientRect().width;
    const height = 600;
    
    const svg = container.append('svg')
        .attr('width', width)
        .attr('height', height);
    
    // Create force simulation
    const simulation = d3.forceSimulation(data.nodes)
        .force('link', d3.forceLink(data.edges)
            .id(d => d.id)
            .distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => d.size + 5));
    
    // Create links
    const link = svg.append('g')
        .selectAll('line')
        .data(data.edges)
        .enter().append('line')
        .attr('class', 'link')
        .style('stroke-width', d => Math.sqrt(d.weight));
    
    // Create nodes
    const node = svg.append('g')
        .selectAll('circle')
        .data(data.nodes)
        .enter().append('circle')
        .attr('class', 'node')
        .attr('r', d => d.size)
        .style('fill', d => {
            if (d.verified) return '#1da1f2';
            if (d.reach > 10000) return '#ff6b6b';
            return '#657786';
        })
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));
    
    // Add labels
    const label = svg.append('g')
        .selectAll('text')
        .data(data.nodes)
        .enter().append('text')
        .attr('class', 'node-label')
        .text(d => d.label)
        .style('font-size', d => Math.max(10, d.size / 3) + 'px');
    
    // Add tooltips
    const tooltip = d3.select('#tooltip');
    
    node.on('mouseover', function(event, d) {
        tooltip.transition().duration(200).style('opacity', .9);
        tooltip.html(`
            <strong>@${d.label}</strong><br/>
            ${d.verified ? '<i class="fas fa-check-circle"></i> Verified' : 'Unverified'}<br/>
            Articles Shared: ${d.articles_shared}<br/>
            Total Reach: ${formatNumber(d.reach)}
        `)
        .style('left', (event.pageX + 10) + 'px')
        .style('top', (event.pageY - 28) + 'px');
    })
    .on('mouseout', function(d) {
        tooltip.transition().duration(500).style('opacity', 0);
    });
    
    // Update positions on tick
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        node
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);
        
        label
            .attr('x', d => d.x)
            .attr('y', d => d.y)
            .attr('text-anchor', 'middle')
            .attr('dy', '.35em');
    });
    
    // Drag functions
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
    
    networkVisualization = { simulation, svg };
}

// Reset network view
function resetNetwork() {
    if (networkVisualization && networkVisualization.simulation) {
        networkVisualization.simulation.alpha(1).restart();
    }
}

// Update category distribution chart
function updateCategoryDistribution(data) {
    const ctx = document.getElementById('categoryDistributionChart').getContext('2d');
    
    if (charts.categoryDistribution) {
        charts.categoryDistribution.destroy();
    }
    
    // Process data for chart
    const categories = [...new Set(data.map(d => d.category))];
    const fakeData = [];
    const realData = [];
    
    categories.forEach(category => {
        const fakeItem = data.find(d => d.category === category && d.label === 'fake');
        const realItem = data.find(d => d.category === category && d.label === 'real');
        
        // Sum up all counts across months for each category
        fakeData.push(fakeItem ? Object.values(fakeItem.data).reduce((sum, v) => sum + v.count, 0) : 0);
        realData.push(realItem ? Object.values(realItem.data).reduce((sum, v) => sum + v.count, 0) : 0);
    });
    
    charts.categoryDistribution = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categories.map(cat => cat.charAt(0).toUpperCase() + cat.slice(1)),
            datasets: [
                {
                    label: 'Fake News',
                    data: fakeData,
                    backgroundColor: 'rgba(220, 53, 69, 0.8)',
                    borderColor: 'rgb(220, 53, 69)',
                    borderWidth: 1
                },
                {
                    label: 'Real News',
                    data: realData,
                    backgroundColor: 'rgba(40, 167, 69, 0.8)',
                    borderColor: 'rgb(40, 167, 69)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            const total = fakeData[context.dataIndex] + realData[context.dataIndex];
                            const percentage = ((context.parsed.y / total) * 100).toFixed(1);
                            return `${percentage}% of total in this category`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'News Categories'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Articles'
                    }
                }
            }
        }
    });
}

// Update user behavior chart
function updateUserBehaviorChart(data) {
    const ctx = document.getElementById('userBehaviorChart').getContext('2d');
    
    if (charts.userBehavior) {
        charts.userBehavior.destroy();
    }
    
    // Group data by user type
    const verifiedData = data.filter(d => d.user_type === 'Verified');
    const unverifiedData = data.filter(d => d.user_type === 'Unverified');
    
    // Prepare data for grouped bar chart
    const verifiedFakeTweets = verifiedData.find(d => d.news_type === 'fake')?.total_tweets || 0;
    const verifiedRealTweets = verifiedData.find(d => d.news_type === 'real')?.total_tweets || 0;
    const unverifiedFakeTweets = unverifiedData.find(d => d.news_type === 'fake')?.total_tweets || 0;
    const unverifiedRealTweets = unverifiedData.find(d => d.news_type === 'real')?.total_tweets || 0;
    
    const verifiedAvgFollowers = verifiedData[0]?.avg_followers || 0;
    const unverifiedAvgFollowers = unverifiedData[0]?.avg_followers || 0;
    
    charts.userBehavior = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Fake News Tweets', 'Real News Tweets', 'Avg Followers (thousands)'],
            datasets: [
                {
                    label: 'Verified Users',
                    data: [
                        verifiedFakeTweets,
                        verifiedRealTweets,
                        Math.round(verifiedAvgFollowers / 1000)
                    ],
                    backgroundColor: 'rgba(29, 161, 242, 0.8)',
                    borderColor: 'rgb(29, 161, 242)',
                    borderWidth: 2
                },
                {
                    label: 'Unverified Users',
                    data: [
                        unverifiedFakeTweets,
                        unverifiedRealTweets,
                        Math.round(unverifiedAvgFollowers / 1000)
                    ],
                    backgroundColor: 'rgba(101, 119, 134, 0.8)',
                    borderColor: 'rgb(101, 119, 134)',
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label;
                            const value = context.parsed.y;
                            const dataLabel = context.label;
                            
                            if (dataLabel.includes('Followers')) {
                                return `${label}: ${(value * 1000).toLocaleString()} avg followers`;
                            }
                            return `${label}: ${value.toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Behaviour Metrics'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Count'
                    }
                }
            }
        }
    });
}

// Update source timeline chart
function updateSourceTimeline(data) {
    const ctx = document.getElementById('sourceTimelineChart').getContext('2d');
    
    if (charts.sourceTimeline) {
        charts.sourceTimeline.destroy();
    }
    
    // Prepare datasets for each source
    const datasets = data.map((source, index) => ({
        label: source.source_name,
        data: source.timeline.map(t => ({
            x: t.month,
            y: t.reliability_score
        })),
        borderColor: getRandomColor(1),
        backgroundColor: getRandomColor(0.1),
        tension: 0.4,
        fill: false
    }));
    
    charts.sourceTimeline = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        usePointStyle: true,
                        padding: 10
                    }
                },
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            const source = data[context.datasetIndex];
                            if (source && source.timeline) {
                                const monthData = source.timeline.find(t => t.month === context.parsed.x);
                                if (monthData) {
                                    return [
                                        `Total Articles: ${monthData.total_articles}`,
                                        `Fake Articles: ${monthData.fake_articles}`
                                    ];
                                }
                            }
                            return [];
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        parser: 'yyyy-MM',
                        tooltipFormat: 'MMM yyyy',
                        displayFormats: {
                            month: 'MMM yyyy'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Month'
                    }
                },
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Reliability Score (%)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

// Update analysis type
function updateAnalysisType() {
    generateAnalysisResults();
}

// Generate dynamic analysis results based on current data and filters
async function generateAnalysisResults() {
    const analysisType = document.getElementById('analysisType').value;
    const dateRange = document.getElementById('dateRange').value;
    const category = document.getElementById('categoryFilter').value;
    const resultsDiv = document.getElementById('analysisResults');
    
    try {
        // Get current data for analysis
        const [stats, temporalData, userBehavior] = await Promise.all([
            apiRequest('/api/stats/overview'),
            apiRequest(`/analytical/temporal-trends?days=${dateRange}`),
            apiRequest('/analytical/user-behavior')
        ]);
        
        // Calculate metrics from current data
        const totalArticles = stats.articles.total;
        const fakePercentage = ((stats.articles.fake / totalArticles) * 100).toFixed(1);
        const realPercentage = ((stats.articles.real / totalArticles) * 100).toFixed(1);
        
        // Calculate verified user impact
        const verifiedUsers = userBehavior.filter(d => d.user_type === 'Verified');
        const unverifiedUsers = userBehavior.filter(d => d.user_type === 'Unverified');
        const verifiedFakeShare = verifiedUsers.find(d => d.news_type === 'fake')?.total_tweets || 0;
        const verifiedRealShare = verifiedUsers.find(d => d.news_type === 'real')?.total_tweets || 0;
        const verifiedTotal = verifiedFakeShare + verifiedRealShare;
        const verifiedFakePercentage = verifiedTotal > 0 ? ((verifiedFakeShare / verifiedTotal) * 100).toFixed(1) : 0;
        
        // Calculate temporal trends
        let trendAnalysis = 'stable';
        if (temporalData.length > 7) {
            const firstWeek = temporalData.slice(0, 7).reduce((sum, day) => sum + day.fake, 0);
            const lastWeek = temporalData.slice(-7).reduce((sum, day) => sum + day.fake, 0);
            const growthRate = ((lastWeek - firstWeek) / firstWeek * 100);
            if (growthRate > 10) trendAnalysis = 'increasing';
            else if (growthRate < -10) trendAnalysis = 'decreasing';
        }
        
        const categoryText = category ? ` in ${category}` : '';
        const timeText = dateRange == 7 ? 'week' : dateRange == 30 ? 'month' : dateRange == 90 ? '3 months' : dateRange == 180 ? '6 months' : 'year';
        
        switch(analysisType) {
            case 'trends':
                resultsDiv.innerHTML = `
                    <div class="alert alert-info">
                        <h5><i class="fas fa-chart-line"></i> Temporal Trend Analysis</h5>
                        <p><strong>Analysis Period:</strong> Last ${timeText}${categoryText}</p>
                        <div class="row">
                            <div class="col-md-6">
                                <h6>Key Findings:</h6>
                                <ul>
                                    <li><strong>Total Articles Analysed:</strong> ${totalArticles.toLocaleString()}</li>
                                    <li><strong>Fake News Distribution:</strong> ${fakePercentage}% (${stats.articles.fake.toLocaleString()} articles)</li>
                                    <li><strong>Real News Distribution:</strong> ${realPercentage}% (${stats.articles.real.toLocaleString()} articles)</li>
                                    <li><strong>Trend Direction:</strong> Fake news is ${trendAnalysis} over the analysis period</li>
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <h6>Pattern Insights:</h6>
                                <ul>
                                    <li>Peak spreading typically occurs during major events</li>
                                    <li>Weekend activity shows different engagement patterns</li>
                                    <li>Real news maintains more consistent distribution</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                `;
                break;
                
            case 'patterns':
                resultsDiv.innerHTML = `
                    <div class="alert alert-warning">
                        <h5><i class="fas fa-network-wired"></i> Spread Pattern Analysis</h5>
                        <p><strong>Analysis Period:</strong> Last ${timeText}${categoryText}</p>
                        <div class="row">
                            <div class="col-md-6">
                                <h6>Verified User Behaviour:</h6>
                                <ul>
                                    <li><strong>Verified Users:</strong> ${stats.users.verified.toLocaleString()} (${stats.users.verified_percentage.toFixed(1)}%)</li>
                                    <li><strong>Fake News Share:</strong> ${verifiedFakePercentage}% of verified user content</li>
                                    <li><strong>Role:</strong> Act as fact-checkers and amplifiers of credible content</li>
                                    <li><strong>Influence:</strong> Higher follower counts provide greater reach</li>
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <h6>Network Characteristics:</h6>
                                <ul>
                                    <li>Information spreads through interconnected user networks</li>
                                    <li>Verified users create more reliable information paths</li>
                                    <li>Unverified accounts can form echo chambers</li>
                                    <li>Fake news often spreads faster initially</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                `;
                break;
                
            case 'comparative':
                const unverifiedFakeShare = unverifiedUsers.find(d => d.news_type === 'fake')?.total_tweets || 0;
                const unverifiedRealShare = unverifiedUsers.find(d => d.news_type === 'real')?.total_tweets || 0;
                const unverifiedTotal = unverifiedFakeShare + unverifiedRealShare;
                const unverifiedFakePercentage = unverifiedTotal > 0 ? ((unverifiedFakeShare / unverifiedTotal) * 100).toFixed(1) : 0;
                
                resultsDiv.innerHTML = `
                    <div class="alert alert-success">
                        <h5><i class="fas fa-balance-scale"></i> Comparative Analysis</h5>
                        <p><strong>Analysis Period:</strong> Last ${timeText}${categoryText}</p>
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Metric</th>
                                        <th>Fake News</th>
                                        <th>Real News</th>
                                        <th>Insights</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td><strong>Overall Distribution</strong></td>
                                        <td>${fakePercentage}%</td>
                                        <td>${realPercentage}%</td>
                                        <td>${fakePercentage > realPercentage ? 'More fake news detected' : 'More real news verified'}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Verified User Share</strong></td>
                                        <td>${verifiedFakePercentage}%</td>
                                        <td>${(100 - verifiedFakePercentage).toFixed(1)}%</td>
                                        <td>Verified users prefer sharing credible content</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Unverified User Share</strong></td>
                                        <td>${unverifiedFakePercentage}%</td>
                                        <td>${(100 - unverifiedFakePercentage).toFixed(1)}%</td>
                                        <td>Higher risk of misinformation spread</td>
                                    </tr>
                                    <tr>
                                        <td><strong>User Verification Rate</strong></td>
                                        <td colspan="2">${stats.users.verified_percentage.toFixed(1)}%</td>
                                        <td>Platform verification coverage</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                `;
                break;
        }
    } catch (error) {
        console.error('Error generating analysis results:', error);
        resultsDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i> Unable to generate analysis results. Please try refreshing the data.
            </div>
        `;
    }
}