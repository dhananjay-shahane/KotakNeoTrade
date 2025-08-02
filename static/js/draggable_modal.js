/**
 * Draggable and Resizable Modal Plugin
 * Makes Bootstrap modals draggable and resizable
 */

class DraggableModal {
    constructor(modalElement, options = {}) {
        this.modal = modalElement;
        this.modalDialog = modalElement.querySelector('.modal-dialog');
        this.modalContent = modalElement.querySelector('.modal-content');
        this.modalHeader = modalElement.querySelector('.modal-header');
        
        this.options = {
            draggable: true,
            resizable: true,
            minWidth: 300,
            minHeight: 200,
            maxWidth: window.innerWidth * 0.9,
            maxHeight: window.innerHeight * 0.9,
            ...options
        };
        
        this.isDragging = false;
        this.isResizing = false;
        this.currentHandle = null;
        this.startPos = { x: 0, y: 0 };
        this.startSize = { width: 0, height: 0 };
        this.startDialogPos = { x: 0, y: 0 };
        
        this.init();
    }
    
    init() {
        this.setupModal();
        if (this.options.draggable) {
            this.makeDraggable();
        }
        if (this.options.resizable) {
            this.makeResizable();
        }
        this.bindEvents();
    }
    
    setupModal() {
        // Add draggable classes
        this.modal.classList.add('modal-draggable');
        this.modalContent.classList.add('modal-resizable');
        
        // Center modal initially
        this.centerModal();
        
        // Prevent backdrop click from closing when interacting
        this.modal.addEventListener('mousedown', (e) => {
            if (e.target === this.modal) {
                e.stopPropagation();
            }
        });
    }
    
    centerModal() {
        const rect = this.modalDialog.getBoundingClientRect();
        const x = (window.innerWidth - rect.width) / 2;
        const y = (window.innerHeight - rect.height) / 2;
        
        this.modalDialog.style.left = Math.max(0, x) + 'px';
        this.modalDialog.style.top = Math.max(0, y) + 'px';
    }
    
    makeDraggable() {
        if (!this.modalHeader) return;
        
        this.modalHeader.style.cursor = 'move';
        
        this.modalHeader.addEventListener('mousedown', (e) => {
            if (e.target.closest('.btn-close') || e.target.closest('button')) {
                return;
            }
            
            this.startDragging(e);
        });
    }
    
    makeResizable() {
        const handles = [
            'resize-nw', 'resize-n', 'resize-ne',
            'resize-w', 'resize-e',
            'resize-sw', 'resize-s', 'resize-se'
        ];
        
        handles.forEach(handle => {
            const handleElement = document.createElement('div');
            handleElement.className = `resize-handle ${handle}`;
            handleElement.addEventListener('mousedown', (e) => {
                this.startResizing(e, handle);
            });
            this.modalContent.appendChild(handleElement);
        });
    }
    
    startDragging(e) {
        this.isDragging = true;
        this.modal.classList.add('modal-dragging');
        
        const rect = this.modalDialog.getBoundingClientRect();
        this.startPos = { x: e.clientX, y: e.clientY };
        this.startDialogPos = { x: rect.left, y: rect.top };
        
        e.preventDefault();
        document.addEventListener('mousemove', this.drag);
        document.addEventListener('mouseup', this.stopDragging);
    }
    
    startResizing(e, handle) {
        this.isResizing = true;
        this.currentHandle = handle;
        this.modal.classList.add('modal-resizing');
        
        const rect = this.modalDialog.getBoundingClientRect();
        this.startPos = { x: e.clientX, y: e.clientY };
        this.startSize = { width: rect.width, height: rect.height };
        this.startDialogPos = { x: rect.left, y: rect.top };
        
        e.preventDefault();
        e.stopPropagation();
        document.addEventListener('mousemove', this.resize);
        document.addEventListener('mouseup', this.stopResizing);
    }
    
    drag = (e) => {
        if (!this.isDragging) return;
        
        const deltaX = e.clientX - this.startPos.x;
        const deltaY = e.clientY - this.startPos.y;
        
        let newX = this.startDialogPos.x + deltaX;
        let newY = this.startDialogPos.y + deltaY;
        
        // Boundary constraints
        const rect = this.modalDialog.getBoundingClientRect();
        newX = Math.max(0, Math.min(newX, window.innerWidth - rect.width));
        newY = Math.max(0, Math.min(newY, window.innerHeight - rect.height));
        
        this.modalDialog.style.left = newX + 'px';
        this.modalDialog.style.top = newY + 'px';
    }
    
    resize = (e) => {
        if (!this.isResizing) return;
        
        const deltaX = e.clientX - this.startPos.x;
        const deltaY = e.clientY - this.startPos.y;
        
        let newWidth = this.startSize.width;
        let newHeight = this.startSize.height;
        let newX = this.startDialogPos.x;
        let newY = this.startDialogPos.y;
        
        // Calculate new dimensions based on handle
        if (this.currentHandle.includes('e')) {
            newWidth = this.startSize.width + deltaX;
        }
        if (this.currentHandle.includes('w')) {
            newWidth = this.startSize.width - deltaX;
            newX = this.startDialogPos.x + deltaX;
        }
        if (this.currentHandle.includes('s')) {
            newHeight = this.startSize.height + deltaY;
        }
        if (this.currentHandle.includes('n')) {
            newHeight = this.startSize.height - deltaY;
            newY = this.startDialogPos.y + deltaY;
        }
        
        // Apply constraints
        newWidth = Math.max(this.options.minWidth, Math.min(newWidth, this.options.maxWidth));
        newHeight = Math.max(this.options.minHeight, Math.min(newHeight, this.options.maxHeight));
        
        // Adjust position if we hit size constraints
        if (this.currentHandle.includes('w') && newWidth === this.options.minWidth) {
            newX = this.startDialogPos.x + (this.startSize.width - this.options.minWidth);
        }
        if (this.currentHandle.includes('n') && newHeight === this.options.minHeight) {
            newY = this.startDialogPos.y + (this.startSize.height - this.options.minHeight);
        }
        
        // Boundary constraints
        newX = Math.max(0, Math.min(newX, window.innerWidth - newWidth));
        newY = Math.max(0, Math.min(newY, window.innerHeight - newHeight));
        
        this.modalDialog.style.width = newWidth + 'px';
        this.modalDialog.style.height = newHeight + 'px';
        this.modalDialog.style.left = newX + 'px';
        this.modalDialog.style.top = newY + 'px';
        
        // Adjust modal body height
        this.adjustModalBodyHeight();
    }
    
    stopDragging = () => {
        this.isDragging = false;
        this.modal.classList.remove('modal-dragging');
        document.removeEventListener('mousemove', this.drag);
        document.removeEventListener('mouseup', this.stopDragging);
    }
    
    stopResizing = () => {
        this.isResizing = false;
        this.currentHandle = null;
        this.modal.classList.remove('modal-resizing');
        document.removeEventListener('mousemove', this.resize);
        document.removeEventListener('mouseup', this.stopResizing);
    }
    
    adjustModalBodyHeight() {
        const modalBody = this.modal.querySelector('.modal-body');
        if (!modalBody) return;
        
        const modalRect = this.modalDialog.getBoundingClientRect();
        const headerHeight = this.modalHeader ? this.modalHeader.offsetHeight : 0;
        const footerHeight = this.modal.querySelector('.modal-footer')?.offsetHeight || 0;
        const padding = 40; // Account for padding and borders
        
        const availableHeight = modalRect.height - headerHeight - footerHeight - padding;
        modalBody.style.maxHeight = Math.max(150, availableHeight) + 'px';
    }
    
    bindEvents() {
        // Reset position when modal is shown
        this.modal.addEventListener('shown.bs.modal', () => {
            this.centerModal();
            this.adjustModalBodyHeight();
        });
        
        // Handle window resize
        window.addEventListener('resize', () => {
            this.options.maxWidth = window.innerWidth * 0.9;
            this.options.maxHeight = window.innerHeight * 0.9;
            
            // Ensure modal stays within bounds
            const rect = this.modalDialog.getBoundingClientRect();
            if (rect.right > window.innerWidth || rect.bottom > window.innerHeight) {
                this.centerModal();
            }
        });
        
        // Prevent text selection during drag/resize
        document.addEventListener('selectstart', (e) => {
            if (this.isDragging || this.isResizing) {
                e.preventDefault();
            }
        });
    }
    
    // Public methods
    resetPosition() {
        this.modalDialog.style.left = '';
        this.modalDialog.style.top = '';
        this.modalDialog.style.width = '';
        this.modalDialog.style.height = '';
        this.centerModal();
    }
    
    setPosition(x, y) {
        this.modalDialog.style.left = x + 'px';
        this.modalDialog.style.top = y + 'px';
    }
    
    setSize(width, height) {
        this.modalDialog.style.width = width + 'px';
        this.modalDialog.style.height = height + 'px';
        this.adjustModalBodyHeight();
    }
}

// Auto-initialize for specific modals
document.addEventListener('DOMContentLoaded', function() {
    // Initialize draggable modals for edit and close deal modals
    const editDealModal = document.getElementById('editDealModal');
    const closeDealModal = document.getElementById('closeDealModal');
    const editExitDateModal = document.getElementById('editExitDateModal');
    
    if (editDealModal) {
        new DraggableModal(editDealModal, {
            minWidth: 400,
            minHeight: 300
        });
    }
    
    if (closeDealModal) {
        new DraggableModal(closeDealModal, {
            minWidth: 350,
            minHeight: 250
        });
    }
    
    if (editExitDateModal) {
        new DraggableModal(editExitDateModal, {
            minWidth: 350,
            minHeight: 250
        });
    }
});

// Export for use in other scripts
window.DraggableModal = DraggableModal;