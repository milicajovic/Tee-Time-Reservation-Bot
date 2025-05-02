document.addEventListener('DOMContentLoaded', function() {
    // Tab switching functionality
    const tabs = document.querySelectorAll('.attempt-tab:not(.disabled)');
    const gridViews = document.querySelectorAll('.grid-view');
    const pagination = document.querySelector('.pagination');
    const galleryContainer = document.querySelector('.gallery-container');
    
    // Items per page functionality
    const itemsPerPageDropdown = document.querySelector('.items-per-page-dropdown');
    const itemsPerPageButton = document.querySelector('.items-per-page-button');
    const itemsPerPageOptions = document.querySelector('.items-per-page-options');
    const selectedValue = document.querySelector('.selected-value');
    let currentItemsPerPage = 10;
    
    // Toggle dropdown
    itemsPerPageButton.addEventListener('click', (e) => {
        e.stopPropagation();
        itemsPerPageDropdown.classList.toggle('active');
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', () => {
        itemsPerPageDropdown.classList.remove('active');
    });
    
    // Handle option selection
    itemsPerPageOptions.addEventListener('click', (e) => {
        const option = e.target.closest('.items-per-page-option');
        if (!option) return;
        
        const value = option.dataset.value;
        currentItemsPerPage = value === 'all' ? Infinity : parseInt(value);
        selectedValue.textContent = value === 'all' ? 'All' : value;
        
        // Update selected state
        itemsPerPageOptions.querySelectorAll('.items-per-page-option').forEach(opt => {
            opt.classList.toggle('selected', opt === option);
        });
        
        // Update pagination with new items per page
        const activeTab = document.querySelector('.attempt-tab.active');
        if (activeTab) {
            updatePagination(activeTab.dataset.attempt);
        }
        
        itemsPerPageDropdown.classList.remove('active');
    });
    
    // Screenshot Preview functionality
    const previewOverlay = document.querySelector('.screenshot-preview-overlay');
    const previewImage = document.querySelector('.preview-image');
    const previewClose = document.querySelector('.preview-close-btn');
    const previewPrev = document.querySelector('.preview-prev');
    const previewNext = document.querySelector('.preview-next');
    let currentPreviewIndex = 0;
    let currentPreviewImages = [];
    
    // Initialize the first view
    const activeTab = document.querySelector('.attempt-tab.active');
    if (activeTab) {
        initializeView(activeTab.dataset.attempt);
    }
    
    // Show the gallery container after initialization
    galleryContainer.classList.add('loaded');
    
    function initializeView(attempt) {
        // Show grid view
        gridViews.forEach(grid => {
            if (grid.dataset.attempt === attempt) {
                grid.style.display = 'grid';
            } else {
                grid.style.display = 'none';
            }
        });
        // Show pagination for grid view
        pagination.style.display = 'flex';
        updatePagination(attempt);
    }
    
    // Tab switching
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            if (!tab.classList.contains('disabled')) {
                // Remove active class from all tabs
                tabs.forEach(t => t.classList.remove('active'));
                
                // Add active class to clicked tab
                tab.classList.add('active');
                
                // Initialize the view for the new tab
                initializeView(tab.dataset.attempt);
            }
        });
    });
    
    // Function to update pagination
    function updatePagination(attempt) {
        const gridView = document.querySelector(`.grid-view[data-attempt="${attempt}"]`);
        if (!gridView) return;
        
        const screenshots = gridView.querySelectorAll('.screenshot-item');
        const totalScreenshots = screenshots.length;
        const totalPages = currentItemsPerPage === Infinity ? 1 : Math.ceil(totalScreenshots / currentItemsPerPage);
        
        // Clear existing pagination
        pagination.innerHTML = '';
        
        // Show/hide pagination based on whether we're showing all items
        pagination.style.display = currentItemsPerPage === Infinity ? 'none' : 'flex';
        
        if (currentItemsPerPage === Infinity) {
            // Show all screenshots
            screenshots.forEach(screenshot => {
                screenshot.style.display = 'block';
            });
            return;
        }
        
        // Add previous button
        const prevButton = document.createElement('a');
        prevButton.href = '#';
        prevButton.className = 'pagination-item' + (totalPages <= 1 ? ' disabled' : '');
        prevButton.innerHTML = '<i class="fas fa-chevron-left"></i>';
        pagination.appendChild(prevButton);
        
        // Add page numbers
        for (let i = 1; i <= totalPages; i++) {
            const pageButton = document.createElement('a');
            pageButton.href = '#';
            pageButton.className = 'pagination-item' + (i === 1 ? ' active' : '');
            pageButton.textContent = i;
            pagination.appendChild(pageButton);
        }
        
        // Add next button
        const nextButton = document.createElement('a');
        nextButton.href = '#';
        nextButton.className = 'pagination-item' + (totalPages <= 1 ? ' disabled' : '');
        nextButton.innerHTML = '<i class="fas fa-chevron-right"></i>';
        pagination.appendChild(nextButton);
        
        // Function to show specific page
        function showPage(pageNum) {
            const start = (pageNum - 1) * currentItemsPerPage;
            const end = start + currentItemsPerPage;
            
            screenshots.forEach((screenshot, index) => {
                screenshot.style.display = (index >= start && index < end) ? 'block' : 'none';
            });
            
            // Update active page button
            pagination.querySelectorAll('.pagination-item').forEach((item, index) => {
                if (index === 0) return; // Skip prev button
                if (index === pagination.children.length - 1) return; // Skip next button
                item.classList.toggle('active', index === pageNum);
            });
        }
        
        // Add click handlers
        pagination.querySelectorAll('.pagination-item').forEach((item, index) => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                if (item.classList.contains('disabled')) return;
                
                if (index === 0) { // Prev button
                    const currentPage = parseInt(pagination.querySelector('.pagination-item.active').textContent);
                    if (currentPage > 1) {
                        showPage(currentPage - 1);
                    }
                } else if (index === pagination.children.length - 1) { // Next button
                    const currentPage = parseInt(pagination.querySelector('.pagination-item.active').textContent);
                    if (currentPage < totalPages) {
                        showPage(currentPage + 1);
                    }
                } else { // Page number
                    showPage(index);
                }
            });
        });
        
        // Show first page initially
        showPage(1);
    }
       

    function openPreview(clickedImg, screenshots) {
        currentPreviewImages = screenshots;
        currentPreviewIndex = Array.from(screenshots).findIndex(img => img.src === clickedImg.src);
        updatePreviewImage();
        previewOverlay.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        // Add active class after a small delay to trigger animations
        setTimeout(() => {
            previewOverlay.classList.add('active');
        }, 10);
    }

    function updatePreviewImage() {
        previewImage.src = currentPreviewImages[currentPreviewIndex].src;
        // Update navigation buttons visibility
        previewPrev.style.display = currentPreviewIndex > 0 ? 'flex' : 'none';
        previewNext.style.display = currentPreviewIndex < currentPreviewImages.length - 1 ? 'flex' : 'none';
    }

    // Add click handlers for all screenshot items
    document.addEventListener('click', function(e) {
        const clickedItem = e.target.closest('.screenshot-item');
        if (clickedItem) {
            const clickedImg = clickedItem.querySelector('img');
            const container = clickedItem.closest('.grid-view');
            const allImages = Array.from(container.querySelectorAll('.screenshot-item img'));
            openPreview(clickedImg, allImages);
        }
    });

    // Close preview
    previewClose.addEventListener('click', () => {
        previewOverlay.classList.remove('active');
        // Wait for animations to finish before hiding
        setTimeout(() => {
            previewOverlay.style.display = 'none';
            document.body.style.overflow = '';
        }, 300);
    });

    // Navigation buttons click handlers
    previewPrev.addEventListener('click', () => {
        if (currentPreviewIndex > 0) {
            currentPreviewIndex--;
            updatePreviewImage();
        }
    });

    previewNext.addEventListener('click', () => {
        if (currentPreviewIndex < currentPreviewImages.length - 1) {
            currentPreviewIndex++;
            updatePreviewImage();
        }
    });

    // Close on overlay click
    previewOverlay.addEventListener('click', (e) => {
        if (e.target === previewOverlay) {
            previewOverlay.classList.remove('active');
            setTimeout(() => {
                previewOverlay.style.display = 'none';
                document.body.style.overflow = '';
            }, 300);
        }
    });

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (previewOverlay.style.display === 'flex') {
            if (e.key === 'Escape') {
                previewOverlay.classList.remove('active');
                setTimeout(() => {
                    previewOverlay.style.display = 'none';
                    document.body.style.overflow = '';
                }, 300);
            } else if (e.key === 'ArrowLeft' && currentPreviewIndex > 0) {
                currentPreviewIndex--;
                updatePreviewImage();
            } else if (e.key === 'ArrowRight' && currentPreviewIndex < currentPreviewImages.length - 1) {
                currentPreviewIndex++;
                updatePreviewImage();
            }
        }
    });
});

const backButton = document.querySelector('.back-button');
if (backButton) {
    backButton.addEventListener('click', function(event) {
        event.preventDefault();
        // Check if the referrer is from your own site
        const referrer = document.referrer;
        const isInternal = referrer && referrer.includes(window.location.hostname);
        if (isInternal) {
            window.history.back();
        } else {
            window.location.href = '/'; // Or '/?tab=2' for your second tab
        }
    });
}