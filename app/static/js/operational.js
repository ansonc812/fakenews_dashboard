// Operational Dashboard JavaScript

let refreshInterval;
let charts = {};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializeFilters();
    loadDashboardData();
    setupAutoRefresh();
});

// Initialize filters and event listeners
function initializeFilters() {
    document.getElementById('refreshBtn').addEventListener('click', loadDashboardData);
    document.getElementById('timeRange').addEventListener('change', loadDashboardData);
    document.getElementById('newsType').addEventListener('change', loadDashboardData);
    document.getElementById('autoRefresh').addEventListener('change', setupAutoRefresh);
}

// Setup auto-refresh
function setupAutoRefresh() {
    const interval = parseInt(document.getElementById('autoRefresh').value) * 1000;
    
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    if (interval > 0) {
        refreshInterval = setInterval(loadDashboardData, interval);
    }
}

// Load all dashboard data
async function loadDashboardData() {
    const hours = document.getElementById('timeRange').value;
    const newsType = document.getElementById('newsType').value;
    
    try {
        // Load all data in parallel
        const [stats, viralContent, influencers, sources, categories] = await Promise.all([
            apiRequest('/api/stats/overview'),
            apiRequest(`/operational/viral-content?hours=${hours}`),
            apiRequest(`/operational/influencers${newsType ? '?label=' + newsType : ''}`),
            apiRequest('/operational/source-credibility'),
            apiRequest(`/operational/category-distribution?hours=${hours}`)
        ]);
        
        updateOverviewMetrics(stats);
        updateViralContent(viralContent);
        updateInfluencers(influencers);
        updateSourceCredibility(sources);
        updateCategoryDistribution(categories);
        updateEngagementTable();
        
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
        showError('viralContentList', 'Failed to load dashboard data. Please try again.');
    }
}

// Update overview metrics
function updateOverviewMetrics(stats) {
    document.getElementById('totalArticles').textContent = formatNumber(stats.articles.total);
    document.getElementById('fakeNews').textContent = formatNumber(stats.articles.fake);
    document.getElementById('realNews').textContent = formatNumber(stats.articles.real);
    document.getElementById('fakePercentage').textContent = stats.articles.fake_percentage;
    document.getElementById('realPercentage').textContent = (100 - stats.articles.fake_percentage).toFixed(2);
}

// Update viral content list
function updateViralContent(articles) {
    const container = document.getElementById('viralContentList');
    
    if (!articles || articles.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">No viral content detected in the selected time range.</p>';
        return;
    }
    
    // Update viral count in metrics
    document.getElementById('viralCount').textContent = articles.length;
    
    const html = articles.map(article => `
        <div class="viral-article">
            <h6 class="mb-2">
                ${article.title}
                <span class="${article.label === 'fake' ? 'fake-label' : 'real-label'} float-end">
                    ${article.label.toUpperCase()}
                </span>
            </h6>
            <div class="d-flex justify-content-between mb-2">
                <small class="text-muted">
                    <i class="fas fa-retweet"></i> ${formatNumber(article.retweet_count)} retweets
                </small>
                <small class="text-muted">
                    <i class="fas fa-heart"></i> ${formatNumber(article.favorite_count)} likes
                </small>
                <small class="text-muted">
                    <i class="fas fa-comment"></i> ${formatNumber(article.tweet_count)} tweets
                </small>
            </div>
            <div class="progress" style="height: 10px;">
                <div class="progress-bar bg-warning" 
                     style="width: ${Math.min(100, article.engagement_score / 100)}%"
                     title="Engagement Score: ${article.engagement_score.toFixed(0)}">
                </div>
            </div>
            <a href="${article.url}" target="_blank" class="btn btn-sm btn-outline-primary mt-2">
                <i class="fas fa-external-link-alt"></i> View Article
            </a>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

// Update influencers list
function updateInfluencers(users) {
    const container = document.getElementById('influencersList');
    
    if (!users || users.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">No influencer data available.</p>';
        return;
    }
    
    const html = users.slice(0, 10).map((user, index) => `
        <div class="influencer-card">
            <div class="influencer-avatar">
                ${user.username.charAt(0).toUpperCase()}
            </div>
            <div class="flex-grow-1">
                <h6 class="mb-1">
                    ${user.display_name || user.username}
                    ${user.verified ? '<i class="fas fa-check-circle verified-badge"></i>' : ''}
                </h6>
                <small class="text-muted">
                    @${user.username} • ${formatNumber(user.followers_count)} followers
                </small>
                <div class="mt-1">
                    <span class="badge bg-secondary">
                        ${user.tweet_count} articles shared
                    </span>
                    <span class="badge bg-info">
                        Impact: ${formatNumber(user.impact_score)}
                    </span>
                </div>
            </div>
            <div class="text-end">
                <h5 class="mb-0">#${index + 1}</h5>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

// Update source credibility chart
function updateSourceCredibility(sources) {
    const ctx = document.getElementById('sourceCredibilityChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (charts.sourceCredibility) {
        charts.sourceCredibility.destroy();
    }
    
    // Sort sources by fake percentage
    sources.sort((a, b) => b.fake_percentage - a.fake_percentage);
    
    charts.sourceCredibility = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sources.map(s => s.source_name),
            datasets: [{
                label: 'Fake News %',
                data: sources.map(s => s.fake_percentage),
                backgroundColor: sources.map(s => 
                    s.fake_percentage > 50 ? 'rgba(220, 53, 69, 0.8)' : 
                    s.fake_percentage > 25 ? 'rgba(255, 193, 7, 0.8)' : 
                    'rgba(40, 167, 69, 0.8)'
                ),
                borderColor: sources.map(s => 
                    s.fake_percentage > 50 ? 'rgb(220, 53, 69)' : 
                    s.fake_percentage > 25 ? 'rgb(255, 193, 7)' : 
                    'rgb(40, 167, 69)'
                ),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            const source = sources[context.dataIndex];
                            return [
                                `Total Articles: ${source.article_count}`,
                                `Fake: ${source.fake_count} | Real: ${source.real_count}`,
                                `Credibility Rating: ${source.credibility_rating || 'N/A'}`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                },
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            }
        }
    });
}

// Update category distribution chart
function updateCategoryDistribution(categories) {
    const ctx = document.getElementById('categoryDistributionChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (charts.categoryDistribution) {
        charts.categoryDistribution.destroy();
    }
    
    charts.categoryDistribution = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: categories.map(c => c.category),
            datasets: [{
                label: 'Articles by Category',
                data: categories.map(c => c.total_articles),
                backgroundColor: [
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 206, 86, 0.8)',
                    'rgba(75, 192, 192, 0.8)',
                    'rgba(153, 102, 255, 0.8)'
                ],
                borderColor: [
                    'rgb(255, 99, 132)',
                    'rgb(54, 162, 235)',
                    'rgb(255, 206, 86)',
                    'rgb(75, 192, 192)',
                    'rgb(153, 102, 255)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        generateLabels: function(chart) {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                return data.labels.map((label, i) => {
                                    const dataset = data.datasets[0];
                                    const value = dataset.data[i];
                                    const category = categories[i];
                                    return {
                                        text: `${label} (${category.fake_percentage}% fake)`,
                                        fillStyle: dataset.backgroundColor[i],
                                        strokeStyle: dataset.borderColor[i],
                                        lineWidth: dataset.borderWidth,
                                        hidden: false,
                                        index: i
                                    };
                                });
                            }
                            return [];
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const category = categories[context.dataIndex];
                            return [
                                `${context.label}: ${category.total_articles} articles`,
                                `Fake: ${category.fake_articles} (${category.fake_percentage}%)`,
                                `Real: ${category.real_articles}`
                            ];
                        }
                    }
                }
            }
        }
    });
}

// Update engagement table
async function updateEngagementTable() {
    const tbody = document.getElementById('engagementTableBody');
    const newsType = document.getElementById('newsType').value;
    
    try {
        const response = await apiRequest(`/api/articles?per_page=10${newsType ? '&label=' + newsType : ''}`);
        const articles = response.articles;
        
        if (!articles || articles.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">No articles found.</td></tr>';
            return;
        }
        
        // Fetch engagement data for each article
        const articlesWithEngagement = await Promise.all(
            articles.map(async (article) => {
                const detail = await apiRequest(`/api/articles/${article.article_id}`);
                return {
                    ...article,
                    engagement: detail.engagement
                };
            })
        );
        
        const html = articlesWithEngagement.map(article => `
            <tr>
                <td>
                    <a href="${article.url}" target="_blank" class="text-decoration-none">
                        ${article.title}
                    </a>
                </td>
                <td>
                    <span class="${article.label === 'fake' ? 'fake-label' : 'real-label'}">
                        ${article.label.toUpperCase()}
                    </span>
                </td>
                <td>${article.source || 'Unknown'}</td>
                <td>${formatNumber(article.engagement.tweet_count)}</td>
                <td>${formatNumber(article.engagement.total_retweets)}</td>
                <td>
                    <span class="engagement-badge">
                        ${((article.engagement.total_retweets * 2 + article.engagement.total_favorites) / 1000).toFixed(1)}K
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewArticleDetails(${article.article_id})">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-secondary" onclick="exportArticleData(${article.article_id})">
                        <i class="fas fa-download"></i>
                    </button>
                </td>
            </tr>
        `).join('');
        
        tbody.innerHTML = html;
        
    } catch (error) {
        console.error('Failed to load engagement table:', error);
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger">Failed to load data.</td></tr>';
    }
}

// View article details
async function viewArticleDetails(articleId) {
    try {
        const article = await apiRequest(`/api/articles/${articleId}`);
        
        // Create modal content
        const modalHtml = `
            <div class="modal fade" id="articleModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${article.title}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6>Article Information</h6>
                                    <p><strong>Label:</strong> <span class="${article.label === 'fake' ? 'fake-label' : 'real-label'}">${article.label.toUpperCase()}</span></p>
                                    <p><strong>Source:</strong> ${article.source?.source_name || 'Unknown'}</p>
                                    <p><strong>Published:</strong> ${article.content?.publish_date ? formatDate(article.content.publish_date) : 'N/A'}</p>
                                    <p><strong>Author:</strong> ${article.content?.author || 'Unknown'}</p>
                                    <p><strong>Categories:</strong> ${article.categories.map(c => c.name).join(', ') || 'None'}</p>
                                </div>
                                <div class="col-md-6">
                                    <h6>Engagement Metrics</h6>
                                    <p><strong>Total Tweets:</strong> ${formatNumber(article.engagement.tweet_count)}</p>
                                    <p><strong>Total Retweets:</strong> ${formatNumber(article.engagement.total_retweets)}</p>
                                    <p><strong>Total Favorites:</strong> ${formatNumber(article.engagement.total_favorites)}</p>
                                </div>
                            </div>
                            <hr>
                            <h6>Top Tweets</h6>
                            <div class="list-group">
                                ${article.top_tweets.map(tweet => `
                                    <div class="list-group-item">
                                        <div class="d-flex justify-content-between">
                                            <strong>@${tweet.username} ${tweet.verified ? '<i class="fas fa-check-circle verified-badge"></i>' : ''}</strong>
                                            <small><i class="fas fa-retweet"></i> ${tweet.retweet_count} | <i class="fas fa-heart"></i> ${tweet.favorite_count}</small>
                                        </div>
                                        <p class="mb-0 mt-2">${tweet.content}</p>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        <div class="modal-footer">
                            <a href="${article.url}" target="_blank" class="btn btn-primary">
                                <i class="fas fa-external-link-alt"></i> View Original Article
                            </a>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('articleModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('articleModal'));
        modal.show();
        
    } catch (error) {
        console.error('Failed to load article details:', error);
        alert('Failed to load article details. Please try again.');
    }
}

// Export article data
async function exportArticleData(articleId) {
    try {
        const article = await apiRequest(`/api/articles/${articleId}`);
        const data = [{
            article_id: article.article_id,
            title: article.title,
            url: article.url,
            label: article.label,
            source: article.source?.source_name || 'Unknown',
            publish_date: article.content?.publish_date || 'N/A',
            author: article.content?.author || 'Unknown',
            categories: article.categories.map(c => c.name).join(', '),
            tweet_count: article.engagement.tweet_count,
            retweet_count: article.engagement.total_retweets,
            favorite_count: article.engagement.total_favorites
        }];
        
        exportToCSV(data, `article_${articleId}_data.csv`);
        
    } catch (error) {
        console.error('Failed to export article data:', error);
        alert('Failed to export article data. Please try again.');
    }
}