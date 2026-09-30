/* CAMPUS ISSUE REPORTING & TRACKING SYSTEM - JAVASCRIPT */

document.addEventListener('DOMContentLoaded', function() {
    // 1. Mobile Sidebar Toggle
    const toggleBtn = document.getElementById('mobileSidebarToggle');
    const sidebar = document.getElementById('appSidebar');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
    }

    // 2. Image Upload Preview
    const imageInput = document.getElementById('imageInput');
    const imagePreview = document.getElementById('imagePreview');

    if (imageInput && imagePreview) {
        imageInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                    imagePreview.style.display = 'block';
                };
                reader.readAsDataURL(file);
            } else {
                imagePreview.src = '';
                imagePreview.style.display = 'none';
            }
        });
    }

    // 3. Auto-dismiss flash alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s ease';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
});

/**
 * Clean Canvas-based Donut Chart Renderer (Offline Capable)
 */
function renderStatusChart(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2 - 15;
    const outerRadius = Math.min(width, height) / 2 - 35;
    const innerRadius = outerRadius * 0.55;

    ctx.clearRect(0, 0, width, height);

    const total = data.reduce((sum, item) => sum + item.value, 0);

    if (total === 0) {
        // Draw empty state
        ctx.beginPath();
        ctx.arc(centerX, centerY, outerRadius, 0, 2 * Math.PI);
        ctx.fillStyle = '#e2e8f0';
        ctx.fill();

        ctx.beginPath();
        ctx.arc(centerX, centerY, innerRadius, 0, 2 * Math.PI);
        ctx.fillStyle = '#ffffff';
        ctx.fill();

        ctx.font = '14px sans-serif';
        ctx.fillStyle = '#7f8c8d';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('No Data', centerX, centerY);
        return;
    }

    let startAngle = -0.5 * Math.PI;

    // Draw chart segments
    data.forEach(item => {
        if (item.value <= 0) return;
        const sliceAngle = (item.value / total) * 2 * Math.PI;
        const endAngle = startAngle + sliceAngle;

        ctx.beginPath();
        ctx.arc(centerX, centerY, outerRadius, startAngle, endAngle);
        ctx.arc(centerX, centerY, innerRadius, endAngle, startAngle, true);
        ctx.closePath();
        ctx.fillStyle = item.color;
        ctx.fill();

        startAngle = endAngle;
    });

    // Center count text
    ctx.font = 'bold 22px sans-serif';
    ctx.fillStyle = '#2c3e50';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(total.toString(), centerX, centerY - 6);

    ctx.font = '11px sans-serif';
    ctx.fillStyle = '#7f8c8d';
    ctx.fillText('TOTAL', centerX, centerY + 14);

    // Draw Legend below chart
    const legendY = height - 25;
    const legendWidth = width / data.length;

    data.forEach((item, index) => {
        const legendX = index * legendWidth + 10;
        
        // Color box
        ctx.fillStyle = item.color;
        ctx.fillRect(legendX, legendY, 10, 10);

        // Label text
        ctx.font = '11px sans-serif';
        ctx.fillStyle = '#2c3e50';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        ctx.fillText(`${item.label}: ${item.value}`, legendX + 14, legendY + 5);
    });
}
