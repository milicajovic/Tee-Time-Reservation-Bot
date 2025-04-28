document.addEventListener('DOMContentLoaded', function() {
    // Tab switching functionality
    const tabs = document.querySelectorAll('.attempt-tab:not(.disabled)');
    const sliders = document.querySelectorAll('.slider-container');
    const gridViews = document.querySelectorAll('.grid-view');
    const pagination = document.querySelector('.pagination');
    const galleryContainer = document.querySelector('.gallery-container');
    
    // Initialize the correct view on page load
    const isGridView = document.querySelector('.view-toggle-btn .fa-th').parentElement.classList.contains('active');
    const activeTab = document.querySelector('.attempt-tab.active');
    
    function initializeView(attempt, isGridView) {
        if (isGridView) {
            // Show grid view and hide slider view
            gridViews.forEach(grid => {
                if (grid.dataset.attempt === attempt) {
                    grid.style.display = 'grid';
                    grid.classList.add('visible');
                } else {
                    grid.style.display = 'none';
                    grid.classList.remove('visible');
                }
            });
            sliders.forEach(container => {
                container.style.display = 'none';
            });
            // Show pagination for grid view
            pagination.style.display = 'flex';
            updatePagination(attempt);
        } else {
            // Show slider view and hide grid view
            sliders.forEach(container => {
                container.style.display = container.dataset.attempt === attempt ? 'block' : 'none';
            });
            gridViews.forEach(grid => {
                grid.style.display = 'none';
                grid.classList.remove('visible');
            });
            // Hide pagination for slider view
            pagination.style.display = 'none';
            // Initialize the active slider
            const activeSlider = document.querySelector(`.slider-container[data-attempt="${attempt}"]`);
            if (activeSlider) {
                initializeSlider(activeSlider);
            }
        }
    }
    
    // Initialize the first view
    if (activeTab) {
        initializeView(activeTab.dataset.attempt, isGridView);
    }
    
    // Show the gallery container after initialization
    galleryContainer.classList.add('loaded');
    
    // Initialize slider function
    function initializeSlider(slider) {
        const track = slider.querySelector('.slider-track');
        const items = track.querySelectorAll('.screenshot-item');
        const prevBtn = slider.querySelector('.slider-prev');
        const nextBtn = slider.querySelector('.slider-next');
        let currentIndex = 0;
        const itemsPerView = 5;

        // Reset transform and state
        track.style.transform = 'translateX(0)';
        
        function updateSliderPosition() {
            track.style.transform = `translateX(-${currentIndex * (items[0].offsetWidth + 16)}px)`;
            
            // Update button states
            if (currentIndex === 0) {
                prevBtn.classList.add('disabled');
            } else {
                prevBtn.classList.remove('disabled');
            }
            
            if (currentIndex >= items.length - itemsPerView) {
                nextBtn.classList.add('disabled');
            } else {
                nextBtn.classList.remove('disabled');
            }
        }
        
        // Initial button states
        updateSliderPosition();
        
        // Add click handlers for navigation buttons
        prevBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (currentIndex > 0) {
                currentIndex--;
                updateSliderPosition();
            }
        });
        
        nextBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (currentIndex < items.length - itemsPerView) {
                currentIndex++;
                updateSliderPosition();
            }
        });
    }
    
    // Screenshot Preview functionality
    const previewOverlay = document.querySelector('.screenshot-preview-overlay');
    const previewImage = document.querySelector('.preview-image');
    const previewClose = document.querySelector('.preview-close-btn');
    const previewPrev = document.querySelector('.preview-prev');
    const previewNext = document.querySelector('.preview-next');
    let currentPreviewIndex = 0;
    let currentPreviewImages = [];

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
            const container = clickedItem.closest('.slider-container, .grid-view');
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
    
    // Tab switching
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            if (!tab.classList.contains('disabled')) {
                // Remove active class from all tabs
                tabs.forEach(t => t.classList.remove('active'));
                
                // Add active class to clicked tab
                tab.classList.add('active');
                
                // Get the current view mode
                const isGridView = document.querySelector('.view-toggle-btn .fa-th').parentElement.classList.contains('active');
                const attempt = tab.dataset.attempt;
                
                // Initialize the view for the new tab
                initializeView(attempt, isGridView);
            }
        });
    });
    
    // View switching functionality
    const viewButtons = document.querySelectorAll('.view-toggle-btn');
    
    // Function to update pagination
    function updatePagination(attempt) {
        const gridView = document.querySelector(`.grid-view[data-attempt="${attempt}"]`);
        if (!gridView) return;
        
        const screenshots = gridView.querySelectorAll('.screenshot-item');
        const totalScreenshots = screenshots.length;
        const screenshotsPerPage = 10;
        const totalPages = Math.ceil(totalScreenshots / screenshotsPerPage);
        
        // Clear existing pagination
        pagination.innerHTML = '';
        
        // Always show pagination
        pagination.style.display = 'flex';
        
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
            const start = (pageNum - 1) * screenshotsPerPage;
            const end = start + screenshotsPerPage;
            
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
    
    viewButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            viewButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Get the current active tab
            const activeTab = document.querySelector('.attempt-tab.active');
            if (activeTab) {
                const attempt = activeTab.dataset.attempt;
                const isGridView = this.querySelector('.fa-th') !== null;
                
                // Initialize the view for the current tab
                initializeView(attempt, isGridView);
            }
        });
    });
});