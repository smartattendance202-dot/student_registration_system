// JavaScript مخصص لنظام تسجيل الطلاب

document.addEventListener('DOMContentLoaded', function () {
    // تحسين تجربة المستخدم
    initializeApp();
});

function initializeApp() {
    // إضافة تأثيرات التحميل
    addLoadingEffects();

    // تحسين رفع الملفات
    enhanceFileUploads();

    // إضافة تأكيدات الحذف
    addDeleteConfirmations();

    // تحسين النماذج
    enhanceForms();

    // إضافة تأثيرات بصرية
    addVisualEffects();
}

function addLoadingEffects() {
    // إضافة مؤشر تحميل للنماذج
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            const submitBtn = form.querySelector('input[type="submit"], button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="loading-spinner me-2"></span>جاري المعالجة...';
            }
        });
    });
}

function enhanceFileUploads() {
    const fileInputs = document.querySelectorAll('input[type="file"]');

    fileInputs.forEach(input => {
        // إضافة معاينة للصور
        input.addEventListener('change', function (e) {
            const file = e.target.files[0];
            const uploadCard = input.closest('.upload-card');

            if (file && file.type.startsWith('image/')) {
                // فحص أولي للصورة
                validateImageFile(file, uploadCard, input);
            } else if (file) {
                updateUploadCardState(uploadCard, 'error');
                showUploadError(uploadCard, 'يرجى اختيار ملف صورة صحيح');
            } else {
                updateUploadCardState(uploadCard, 'default');
            }
        });

        // إضافة drag and drop للبطاقات الجديدة
        const uploadCard = input.closest('.upload-card');
        if (uploadCard) {
            addDragAndDropToCard(uploadCard, input);
        } else {
            // للبطاقات القديمة
            const container = input.closest('.mb-3');
            if (container) {
                addDragAndDrop(container, input);
            }
        }
    });
}

function previewImage(file, input) {
    const reader = new FileReader();
    reader.onload = function (e) {
        // إزالة المعاينة السابقة
        const existingPreview = input.parentNode.querySelector('.file-preview');
        if (existingPreview) {
            existingPreview.remove();
        }

        // إنشاء معاينة جديدة (للمعاينة فقط أثناء الرفع - لا يؤثر على الحفظ)
        const preview = document.createElement('img');
        preview.src = e.target.result;
        preview.className = 'file-preview mt-2';
        preview.style.maxWidth = '200px';  // حد المعاينة فقط
        preview.style.maxHeight = '200px'; // حد المعاينة فقط
        preview.style.borderRadius = '8px';
        preview.style.border = '2px solid #dee2e6';

        input.parentNode.appendChild(preview);
    };
    reader.readAsDataURL(file);
}

// دالة معاينة الصور في البطاقات الجديدة
function previewImageInCard(file, input, uploadCard) {
    if (!uploadCard) {
        // استخدام الدالة القديمة للبطاقات القديمة
        previewImage(file, input);
        return;
    }

    const reader = new FileReader();
    reader.onload = function (e) {
        // إزالة المعاينة السابقة
        const existingPreview = uploadCard.querySelector('.image-preview');
        if (existingPreview) {
            existingPreview.remove();
        }

        // إنشاء معاينة جديدة
        const preview = document.createElement('div');
        preview.className = 'image-preview';
        preview.innerHTML = `
            <img src="${e.target.result}" alt="معاينة الصورة" style="
                width: 100%;
                height: 80px;
                object-fit: cover;
                border-radius: 8px;
                border: 2px solid #198754;
                margin-top: 0.5rem;
            ">
            <div class="mt-2 text-center">
                <small class="text-success">
                    <i class="fas fa-check-circle me-1"></i>
                    تم اختيار الصورة - ${formatFileSize(file.size)}
                </small>
            </div>
        `;

        // إخفاء placeholder وإظهار المعاينة
        const placeholder = uploadCard.querySelector('.upload-placeholder');
        if (placeholder) {
            placeholder.style.display = 'none';
        }

        uploadCard.querySelector('.upload-body').appendChild(preview);
    };
    reader.readAsDataURL(file);
}

// تحديث حالة بطاقة الرفع
function updateUploadCardState(uploadCard, state) {
    if (!uploadCard) return;

    // إزالة جميع الحالات السابقة
    uploadCard.classList.remove('has-image', 'has-error');

    const badge = uploadCard.querySelector('.badge');
    const placeholder = uploadCard.querySelector('.upload-placeholder');

    switch (state) {
        case 'success':
            uploadCard.classList.add('has-image');
            if (badge) {
                badge.textContent = 'تم الرفع';
                badge.className = 'badge bg-success ms-auto';
            }
            break;
        case 'error':
            uploadCard.classList.add('has-error');
            if (badge) {
                badge.textContent = 'خطأ';
                badge.className = 'badge bg-danger ms-auto';
            }
            if (placeholder) {
                placeholder.style.display = 'block';
            }
            break;
        case 'loading':
            if (badge) {
                badge.textContent = 'جاري الفحص...';
                badge.className = 'badge bg-warning ms-auto';
            }
            if (placeholder) {
                placeholder.innerHTML = `
                    <div class="spinner-border spinner-border-sm text-primary mb-2" role="status">
                        <span class="visually-hidden">جاري التحميل...</span>
                    </div>
                    <p class="text-muted mb-0">جاري فحص الصورة...</p>
                `;
            }
            break;
        default:
            if (badge) {
                badge.textContent = 'مطلوبة';
                badge.className = 'badge bg-danger ms-auto';
            }
            if (placeholder) {
                placeholder.style.display = 'block';
                placeholder.innerHTML = `
                    <i class="fas fa-cloud-upload-alt fa-2x text-muted mb-2"></i>
                    <p class="text-muted mb-0">اضغط لاختيار الصورة</p>
                    <small class="text-muted">أو اسحب الملف هنا</small>
                `;
            }
            // إزالة المعاينة
            const preview = uploadCard.querySelector('.image-preview');
            if (preview) {
                preview.remove();
            }
    }
}

// إضافة drag and drop للبطاقات الجديدة
function addDragAndDropToCard(uploadCard, input) {
    uploadCard.addEventListener('dragover', function (e) {
        e.preventDefault();
        uploadCard.classList.add('dragover');
        uploadCard.style.borderColor = '#0d6efd';
        uploadCard.style.background = '#e7f3ff';
    });

    uploadCard.addEventListener('dragleave', function (e) {
        e.preventDefault();
        uploadCard.classList.remove('dragover');
        uploadCard.style.borderColor = '';
        uploadCard.style.background = '';
    });

    uploadCard.addEventListener('drop', function (e) {
        e.preventDefault();
        uploadCard.classList.remove('dragover');
        uploadCard.style.borderColor = '';
        uploadCard.style.background = '';

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            input.files = files;
            input.dispatchEvent(new Event('change'));
        }
    });
}

// الدالة القديمة للبطاقات القديمة
function addDragAndDrop(container, input) {
    container.addEventListener('dragover', function (e) {
        e.preventDefault();
        container.classList.add('dragover');
    });

    container.addEventListener('dragleave', function (e) {
        e.preventDefault();
        container.classList.remove('dragover');
    });

    container.addEventListener('drop', function (e) {
        e.preventDefault();
        container.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            input.files = files;
            input.dispatchEvent(new Event('change'));
        }
    });
}

function addDeleteConfirmations() {
    const deleteButtons = document.querySelectorAll('[data-confirm]');

    deleteButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            const message = button.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
}

function enhanceForms() {
    // تحسين التحقق من صحة النماذج
    const forms = document.querySelectorAll('form');

    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');

        inputs.forEach(input => {
            input.addEventListener('blur', function () {
                validateField(input);
            });

            input.addEventListener('input', function () {
                clearFieldError(input);
            });
        });
    });
}

function validateField(field) {
    // التحقق من الحقول المطلوبة
    if (field.hasAttribute('required') && !field.value.trim()) {
        showFieldError(field, 'هذا الحقل مطلوب');
        return false;
    }

    // التحقق من البريد الإلكتروني
    if (field.type === 'email' && field.value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(field.value)) {
            showFieldError(field, 'يرجى إدخال بريد إلكتروني صحيح');
            return false;
        }
    }

    // تم إزالة التحقق من رقم الجوال من JavaScript
    // التحقق يتم في الخادم (Python) فقط لتجنب التضارب

    clearFieldError(field);
    return true;
}

function showFieldError(field, message) {
    field.classList.add('is-invalid');

    // إزالة رسالة الخطأ السابقة
    const existingError = field.parentNode.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.textContent = message;
    } else {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }
}

function clearFieldError(field) {
    field.classList.remove('is-invalid');
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

function addVisualEffects() {
    // إضافة تأثير fade-in للبطاقات
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in');
    });

    // تحسين الجداول
    const tables = document.querySelectorAll('.table');
    tables.forEach(table => {
        // إضافة hover effect للصفوف
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            row.addEventListener('mouseenter', function () {
                this.style.backgroundColor = '#f8f9fa';
            });

            row.addEventListener('mouseleave', function () {
                this.style.backgroundColor = '';
            });
        });
    });
}

// دوال مساعدة
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);

        // إزالة التنبيه تلقائياً بعد 5 ثوان
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 بايت';

    const k = 1024;
    const sizes = ['بايت', 'كيلوبايت', 'ميجابايت', 'جيجابايت'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// فحص الصورة للتأكد من وجود وجوه
function validateImageFile(file, uploadCard, input) {
    // إظهار حالة التحميل
    updateUploadCardState(uploadCard, 'loading');

    // فحص حجم الملف أولاً
    const maxSize = 15 * 1024 * 1024; // 15MB
    if (file.size > maxSize) {
        updateUploadCardState(uploadCard, 'error');
        showUploadError(uploadCard, 'حجم الملف كبير جداً. الحد الأقصى: 15MB');
        return;
    }

    // فحص نوع الملف
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/bmp', 'image/tiff'];
    if (!allowedTypes.includes(file.type)) {
        updateUploadCardState(uploadCard, 'error');
        showUploadError(uploadCard, 'نوع الملف غير مدعوم. استخدم: JPG, PNG, WebP, BMP, TIFF');
        return;
    }

    // فحص أبعاد الصورة
    const img = new Image();
    img.onload = function () {
        // فحص الحد الأدنى للأبعاد
        if (this.width < 200 || this.height < 200) {
            updateUploadCardState(uploadCard, 'error');
            showUploadError(uploadCard, 'الصورة صغيرة جداً. الحد الأدنى: 200×200 بكسل');
            return;
        }

        // فحص نسبة الأبعاد
        const aspectRatio = this.width / this.height;
        if (aspectRatio < 0.5 || aspectRatio > 2.0) {
            updateUploadCardState(uploadCard, 'error');
            showUploadError(uploadCard, 'نسبة أبعاد الصورة غير مناسبة');
            return;
        }

        // إذا نجحت الفحوصات الأولية، أرسل للخادم للفحص المتقدم
        validateImageOnServer(file, uploadCard, input);
    };

    img.onerror = function () {
        updateUploadCardState(uploadCard, 'error');
        showUploadError(uploadCard, 'ملف الصورة تالف أو غير صحيح');
    };

    img.src = URL.createObjectURL(file);
}

// فحص الصورة على الخادم (فحص الوجوه والتكرار)
function validateImageOnServer(file, uploadCard, input) {
    // تحديث حالة التحميل
    updateUploadCardState(uploadCard, 'loading');

    // الحصول على اسم الصورة من البطاقة
    const imageLabel = uploadCard.querySelector('.upload-header span').textContent.trim();

    // إنشاء FormData لإرسال الصورة
    const formData = new FormData();
    formData.append('image', file);
    formData.append('image_name', imageLabel);

    // إرسال الطلب للخادم
    fetch('/student/validate-image', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || ''
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.valid) {
                // الصورة مقبولة
                previewImageInCard(file, input, uploadCard);
                updateUploadCardState(uploadCard, 'success');
                showUploadSuccess(uploadCard, data.message || 'تم قبول الصورة بنجاح');
            } else {
                // الصورة مرفوضة
                updateUploadCardState(uploadCard, 'error');
                showUploadError(uploadCard, data.message || 'تم رفض الصورة');

                // مسح اختيار الملف
                input.value = '';
            }
        })
        .catch(error => {
            console.error('خطأ في فحص الصورة:', error);
            updateUploadCardState(uploadCard, 'error');
            showUploadError(uploadCard, 'خطأ في الاتصال بالخادم. يرجى المحاولة مرة أخرى.');

            // مسح اختيار الملف
            input.value = '';
        });
}

// إظهار رسالة خطأ في البطاقة
function showUploadError(uploadCard, message) {
    if (!uploadCard) return;

    const errorDiv = uploadCard.querySelector('.upload-error') || document.createElement('div');
    errorDiv.className = 'upload-error alert alert-danger alert-sm mt-2 mb-0';
    errorDiv.innerHTML = `<i class="fas fa-exclamation-triangle me-1"></i>${message}`;

    // إزالة الرسائل السابقة
    const existingError = uploadCard.querySelector('.upload-error');
    if (existingError && existingError !== errorDiv) {
        existingError.remove();
    }

    const existingSuccess = uploadCard.querySelector('.upload-success');
    if (existingSuccess) {
        existingSuccess.remove();
    }

    if (!uploadCard.querySelector('.upload-error')) {
        uploadCard.querySelector('.upload-body').appendChild(errorDiv);
    }
}

// إظهار رسالة نجاح في البطاقة
function showUploadSuccess(uploadCard, message) {
    if (!uploadCard) return;

    const successDiv = uploadCard.querySelector('.upload-success') || document.createElement('div');
    successDiv.className = 'upload-success alert alert-success alert-sm mt-2 mb-0';
    successDiv.innerHTML = `<i class="fas fa-check-circle me-1"></i>${message}`;

    // إزالة الرسائل السابقة
    const existingSuccess = uploadCard.querySelector('.upload-success');
    if (existingSuccess && existingSuccess !== successDiv) {
        existingSuccess.remove();
    }

    const existingError = uploadCard.querySelector('.upload-error');
    if (existingError) {
        existingError.remove();
    }

    if (!uploadCard.querySelector('.upload-success')) {
        uploadCard.querySelector('.upload-body').appendChild(successDiv);
    }
}

// تصدير الدوال للاستخدام العام
window.StudentRegistrationApp = {
    showAlert,
    formatFileSize,
    validateField,
    previewImage,
    validateImageFile
};
