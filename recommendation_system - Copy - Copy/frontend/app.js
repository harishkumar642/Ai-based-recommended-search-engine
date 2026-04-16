const API_BASE = 'http://localhost:8000';

// DOM Elements
const searchQuery = document.getElementById('searchQuery');
const searchBtn = document.getElementById('searchBtn');
const minPriceSlider = document.getElementById('minPriceSlider');
const maxPriceSlider = document.getElementById('maxPriceSlider');
const minPriceValue = document.getElementById('minPriceValue');
const maxPriceValue = document.getElementById('maxPriceValue');
const resultCountSelect = document.getElementById('resultCount');
const category = document.getElementById('category');
const sortBy = document.getElementById('sortBy');
const applyFilters = document.getElementById('applyFilters');
const clearFilters = document.getElementById('clearFilters');
const productsGrid = document.getElementById('productsGrid');
const loading = document.getElementById('loading');
const emptyState = document.getElementById('emptyState');
const resultCountDisplay = document.getElementById('resultCountDisplay');
const detailModal = document.getElementById('detailModal');
const closeDetailModal = document.querySelector('.close-detail');

// Price slider functionality
function updatePriceSliders() {
    let minVal = parseInt(minPriceSlider.value);
    let maxVal = parseInt(maxPriceSlider.value);
    
    if (minVal > maxVal - 1000) {
        minPriceSlider.value = maxVal - 1000;
        minVal = maxVal - 1000;
    }
    
    if (maxVal < minVal + 1000) {
        maxPriceSlider.value = minVal + 1000;
        maxVal = minVal + 1000;
    }
    
    minPriceValue.textContent = minVal.toLocaleString('en-IN');
    maxPriceValue.textContent = maxVal.toLocaleString('en-IN');
}

minPriceSlider.addEventListener('input', updatePriceSliders);
maxPriceSlider.addEventListener('input', updatePriceSliders);

// Initialize on load
window.addEventListener('DOMContentLoaded', () => {
    updatePriceSliders();
    fetchRecommendations();
});

// Search on Enter key
searchQuery.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        fetchRecommendations();
    }
});

// Search button
searchBtn.addEventListener('click', () => {
    fetchRecommendations();
});

// Apply filters
applyFilters.addEventListener('click', () => {
    fetchRecommendations();
});

// Result count dropdown
resultCountSelect.addEventListener('change', () => {
    fetchRecommendations();
});

// Clear filters
clearFilters.addEventListener('click', () => {
    searchQuery.value = '';
    minPriceSlider.value = 0;
    maxPriceSlider.value = 50000;
    updatePriceSliders();
    category.value = '';
    sortBy.value = 'score';
    resultCountSelect.value = '8';
    fetchRecommendations();
});

// Fetch recommendations
async function fetchRecommendations() {
    showLoading();
    
    const kValue = parseInt(resultCountSelect.value) || 8;
    
    const filters = {
        k: kValue,
        page: 1,
        sort_by: sortBy.value || 'score'
    };
    
    const minVal = parseInt(minPriceSlider.value);
    const maxVal = parseInt(maxPriceSlider.value);
    
    if (minVal > 0) filters.min_price = minVal;
    if (maxVal < 100000) filters.max_price = maxVal;
    
    const searchText = searchQuery.value.trim();
    if (searchText) {
        filters.search_query = searchText;
    } else if (category.value) {
        filters.category = category.value;
    }
    
    const params = new URLSearchParams(filters);
    
    try {
        const response = await fetch(`${API_BASE}/recommend?${params}`);
        const data = await response.json();
        
        hideLoading();
        
        if (data.items && data.items.length > 0) {
            renderProducts(data.items);
            resultCountDisplay.textContent = `Top ${data.items.length} products`;
            emptyState.style.display = 'none';
        } else {
            productsGrid.innerHTML = '';
            emptyState.style.display = 'block';
            resultCountDisplay.textContent = '0 products found';
        }
    } catch (error) {
        console.error('Fetch error:', error);
        hideLoading();
        productsGrid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; color: var(--text-primary); padding: 40px;">
                <p style="font-size: 1.2em; margin-bottom: 10px;">❌ Error loading recommendations</p>
                <p>Make sure the backend is running at ${API_BASE}</p>
            </div>
        `;
    }
}

// Render products with images
function renderProducts(products) {
    productsGrid.innerHTML = products.map(product => {
        const imageUrl = product.image_url || '';
        
        return `
            <div class="product-card" onclick='showProductDetail(${JSON.stringify(product).replace(/'/g, "&#39;")})'>
                ${imageUrl ? `
                    <img src="${imageUrl}" 
                         alt="${escapeHtml(product.product_name)}"
                         class="product-image"
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                    <div class="product-image-placeholder" style="display: none;">📦</div>
                ` : `
                    <div class="product-image-placeholder">📦</div>
                `}
                <h3>${escapeHtml(product.product_name)}</h3>
                <div class="category-tag">${escapeHtml(product.category)}</div>
                <div class="product-price">₹${product.price_num.toLocaleString('en-IN')}</div>
                <div class="product-meta">
                    <div class="product-rating">
                        ⭐ ${product.rating.toFixed(1)} <span style="opacity: 0.7;">(${product.rating_count.toLocaleString('en-IN')})</span>
                    </div>
                    <div class="product-score">
                        Score: ${product.final_score.toFixed(3)}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Show product detail with similar products
async function showProductDetail(product) {
    const detailContent = document.getElementById('detailContent');
    const detailSimilarGrid = document.getElementById('detailSimilarGrid');
    
    const imageUrl = product.image_url || '';
    
    detailContent.innerHTML = `
        <div class="detail-header">
            ${imageUrl ? `
                <img src="${imageUrl}" 
                     alt="${escapeHtml(product.product_name)}"
                     class="detail-image"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                <div class="detail-image-placeholder" style="display: none;">📦</div>
            ` : `
                <div class="detail-image-placeholder">📦</div>
            `}
            <div class="detail-text">
                <h2 style="color: var(--text-primary); margin-bottom: 16px; line-height: 1.4;">
                    ${escapeHtml(product.product_name)}
                </h2>
                <div class="category-tag" style="margin-bottom: 20px;">
                    ${escapeHtml(product.category)}
                </div>
                <div class="detail-info">
                    <div class="detail-price">₹${product.price_num.toLocaleString('en-IN')}</div>
                    <div class="detail-rating">
                        ⭐ ${product.rating.toFixed(1)} / 5.0 
                        <span style="opacity: 0.7;">(${product.rating_count.toLocaleString('en-IN')} reviews)</span>
                    </div>
                    <div class="detail-score">
                        <strong>Recommendation Score:</strong> ${product.final_score.toFixed(3)}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    detailSimilarGrid.innerHTML = '<p style="text-align: center; padding: 40px; color: var(--text-secondary);">Loading similar products...</p>';
    detailModal.style.display = 'block';
    
    try {
        const response = await fetch(`${API_BASE}/similar/${product.product_id}?k=6`);
        const data = await response.json();
        
        if (data.items && data.items.length > 0) {
            detailSimilarGrid.innerHTML = `
                <h3 style="color: var(--text-primary); margin: 30px 0 20px;">Similar Products</h3>
                <div class="similar-grid">
                    ${data.items.map(p => {
                        const pImageUrl = p.image_url || '';
                        return `
                            <div class="product-card" style="padding: 16px; cursor: default;">
                                ${pImageUrl ? `
                                    <img src="${pImageUrl}" 
                                         alt="${escapeHtml(p.product_name)}"
                                         class="product-image"
                                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                                    <div class="product-image-placeholder" style="display: none;">📦</div>
                                ` : `
                                    <div class="product-image-placeholder">📦</div>
                                `}
                                <h3 style="font-size: 0.95em; min-height: 44px;">${escapeHtml(p.product_name)}</h3>
                                <div class="category-tag">${escapeHtml(p.category)}</div>
                                <div class="product-price" style="font-size: 1.3em;">₹${p.price_num.toLocaleString('en-IN')}</div>
                                <div class="product-rating" style="margin-top: 10px;">
                                    ⭐ ${p.rating.toFixed(1)} (${p.rating_count.toLocaleString('en-IN')})
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
        } else {
            detailSimilarGrid.innerHTML = '<p style="text-align: center; padding: 20px; color: var(--text-secondary);">No similar products found.</p>';
        }
    } catch (error) {
        console.error('Similar products error:', error);
        detailSimilarGrid.innerHTML = '<p style="text-align: center; padding: 20px; color: var(--text-secondary);">Error loading similar products.</p>';
    }
}

// Close modal
closeDetailModal.addEventListener('click', () => {
    detailModal.style.display = 'none';
});

window.addEventListener('click', (e) => {
    if (e.target === detailModal) {
        detailModal.style.display = 'none';
    }
});

// Loading states
function showLoading() {
    loading.style.display = 'block';
    productsGrid.innerHTML = '';
    emptyState.style.display = 'none';
}

function hideLoading() {
    loading.style.display = 'none';
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
