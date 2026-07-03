/**
 * KOYLAVAULT AI Enterprise Dynamic Toast Notification Engine
 */
class NotificationEngine {
    constructor() {
        this.container = document.createElement('div');
        this.container.className = 'toast-container-custom';
        document.body.appendChild(this.container);
    }

    show(message, type = 'info', duration = 4000) {
        const toast = document.createElement('div');
        toast.className = `glass-panel premium-card d-flex align-items-center mb-3 animate-fade-in`;
        toast.style.padding = '1rem 1.5rem';
        toast.style.minWidth = '300px';
        toast.style.borderLeft = `4px solid ${this.getTypeColor(type)}`;

        const icon = this.getTypeIcon(type);
        
        toast.innerHTML = `
            <div class="me-3" style="color: ${this.getTypeColor(type)}">${icon}</div>
            <div class="flex-grow-1 text-white font-weight-500">${message}</div>
            <button class="btn-close btn-close-white ms-2" style="font-size:0.75rem;" onclick="this.parentElement.remove()"></button>
        `;

        this.container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-10px)';
            toast.style.transition = 'all 0.4s ease';
            setTimeout(() => toast.remove(), 400);
        }, duration);
    }

    getTypeColor(type) {
        const mapping = {
            'success': '#10B981',
            'danger': '#EF4444',
            'warning': '#F59E0B',
            'info': '#3B82F6'
        };
        return mapping[type] || mapping['info'];
    }

    getTypeIcon(type) {
        const mapping = {
            'success': '<i class="fas fa-check-circle"></i>',
            'danger': '<i class="fas fa-exclamation-triangle"></i>',
            'warning': '<i class="fas fa-exclamation-circle"></i>',
            'info': '<i class="fas fa-info-circle"></i>'
        };
        return mapping[type] || mapping['info'];
    }
}

window.ToastEngine = new NotificationEngine();