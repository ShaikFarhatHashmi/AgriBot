/**
 * Plant Disease Camera Functionality
 * Handles camera capture for plant disease detection
 */

$(function () {
    
    // Camera state variables
    let imageStream = null;
    let currentImageFile = null;
    
    // DOM elements
    const uploadImageBtn = $('#uploadImageBtn');
    const cameraImageBtn = $('#cameraImageBtn');
    const imageUploadSection = $('#imageUploadSection');
    const imageCameraSection = $('#imageCameraSection');
    const imageVideo = $('#imageVideo')[0];
    const imageCanvas = $('#imageCanvas')[0];
    const startImageCameraBtn = $('#startImageCameraBtn');
    const stopImageCameraBtn = $('#stopImageCameraBtn');
    const captureImageBtn = $('#captureImageBtn');
    const imageInput = $('#imageInput');
    const imageUploadZone = $('#imageUploadZone');
    const uploadPreview = $('#uploadPreview');
    const previewImg = $('#previewImg');
    const removeImg = $('#removeImg');
    const previewName = $('#previewName');
    const analyseBtn = $('#analyseBtn');
    
    // Tab switching functionality
    uploadImageBtn.on('click', function () {
        uploadImageBtn.addClass('active');
        cameraImageBtn.removeClass('active');
        imageUploadSection.show();
        imageCameraSection.hide();
        stopImageCamera();
    });
    
    cameraImageBtn.on('click', function () {
        cameraImageBtn.addClass('active');
        uploadImageBtn.removeClass('active');
        imageUploadSection.hide();
        imageCameraSection.show();
    });
    
    // Upload zone click handler
    imageUploadZone.on('click', function () {
        imageInput.click();
    });
    
    // File input change handler
    imageInput.on('change', function (e) {
        const file = e.target.files[0];
        if (file) {
            handleImageFile(file);
        }
    });
    
    // Drag and drop handlers
    imageUploadZone.on('dragover', function (e) {
        e.preventDefault();
        imageUploadZone.addClass('dragover');
    });
    
    imageUploadZone.on('dragleave', function (e) {
        e.preventDefault();
        imageUploadZone.removeClass('dragover');
    });
    
    imageUploadZone.on('drop', function (e) {
        e.preventDefault();
        imageUploadZone.removeClass('dragover');
        
        const files = e.originalEvent.dataTransfer.files;
        if (files.length > 0) {
            handleImageFile(files[0]);
        }
    });
    
    // Camera control handlers
    startImageCameraBtn.on('click', startImageCamera);
    stopImageCameraBtn.on('click', stopImageCamera);
    captureImageBtn.on('click', captureImage);
    
    // Remove image handler
    removeImg.on('click', function () {
        clearImage();
    });
    
    // Analyse button handler
    analyseBtn.on('click', function () {
        if (!currentImageFile) {
            alert('Please select or capture an image first');
            return;
        }
        analyzePlantImage(currentImageFile);
    });
    
    // Functions
    function handleImageFile(file) {
        // Validate file type
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
        if (!validTypes.includes(file.type)) {
            alert('Please select a valid image file (JPG, PNG, or WebP)');
            return;
        }
        
        // Validate file size (5MB max)
        const maxSize = 5 * 1024 * 1024; // 5MB
        if (file.size > maxSize) {
            alert('File size must be less than 5MB');
            return;
        }
        
        currentImageFile = file;
        displayImagePreview(file);
        analyseBtn.prop('disabled', false);
    }
    
    function displayImagePreview(file) {
        const reader = new FileReader();
        reader.onload = function (e) {
            previewImg.attr('src', e.target.result);
            previewName.text(file.name);
            uploadPreview.show();
            imageUploadZone.hide();
        };
        reader.readAsDataURL(file);
    }
    
    function analyzePlantImage(file) {
        const resultWrap = $('#resultWrap');
        const resultLoading = $('#resultLoading');
        const resultSuccess = $('#resultSuccess');
        const resultError = $('#resultError');
        const diseaseName = $('#diseaseName');
        const confBadge = $('#confBadge');
        const warnBox = $('#warnBox');
        const warnText = $('#warnText');
        const ragBody = $('#ragBody');
        const errorMsg = $('#errorMsg');
        
        // Show loading
        resultWrap.show();
        resultLoading.show();
        resultSuccess.hide();
        resultError.hide();
        analyseBtn.prop('disabled', true);
        
        // Get language selection
        const selectedLang = $('#langSelect').val() || 'en';
        
        // Create FormData for file upload
        const formData = new FormData();
        formData.append('image', file);
        formData.append('lang', selectedLang);
        
        // Get conversation ID if available
        const currentConvId = window.currentConvId || null;
        if (currentConvId) {
            formData.append('conv_id', currentConvId);
        }
        
        // Send to backend for analysis
        $.ajax({
            url: '/image/predict',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            timeout: 60000, // 60 seconds timeout
            success: function(response) {
                resultLoading.hide();
                
                if (response.success) {
                    // Show successful result
                    diseaseName.text(response.disease);
                    confBadge.text(response.confidence + '%');
                    
                    // Set confidence badge color
                    if (response.confidence >= 70) {
                        confBadge.css('background-color', '#28a745');
                    } else if (response.confidence >= 50) {
                        confBadge.css('background-color', '#ffc107');
                    } else {
                        confBadge.css('background-color', '#dc3545');
                    }
                    
                    // Show warning if not reliable
                    if (response.warning) {
                        warnText.text(response.warning);
                        warnBox.show();
                    } else {
                        warnBox.hide();
                    }
                    
                    // Show RAG answer
                    ragBody.html(response.rag_answer.replace(/\n/g, '<br>'));
                    
                    // Update conversation ID if provided
                    if (response.conv_id) {
                        window.currentConvId = response.conv_id;
                    }
                    
                    resultSuccess.show();
                    
                    // Enable follow-up button
                    $('#followupBtn').off('click').on('click', function() {
                        // Switch to chat tab
                        $('#tab-chat').click();
                        // Focus on message input
                        $('#messageText').focus();
                    });
                    
                } else {
                    // Show error
                    errorMsg.text(response.error || 'Analysis failed. Please try again.');
                    resultError.show();
                }
            },
            error: function(xhr, status, error) {
                resultLoading.hide();
                
                let errorMessage = 'Analysis failed. Please try again.';
                if (status === 'timeout') {
                    errorMessage = 'Analysis timed out. Please try again.';
                } else if (xhr.status === 400) {
                    errorMessage = 'Invalid image file. Please upload a clear plant photo.';
                } else if (xhr.status === 500) {
                    errorMessage = 'Server error during analysis. Please try again later.';
                }
                
                errorMsg.text(errorMessage);
                resultError.show();
            },
            complete: function() {
                analyseBtn.prop('disabled', false);
            }
        });
    }
    
    function clearImage() {
        currentImageFile = null;
        uploadPreview.hide();
        imageUploadZone.show();
        previewImg.attr('src', '');
        previewName.text('');
        imageInput.val('');
        analyseBtn.prop('disabled', true);
    }
    
    async function startImageCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    facingMode: 'environment',
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                } 
            });
            
            imageStream = stream;
            imageVideo.srcObject = stream;
            imageVideo.style.display = 'block';
            $('#imageCameraPlaceholder').hide();
            
            startImageCameraBtn.hide();
            stopImageCameraBtn.show();
            captureImageBtn.show();
            
        } catch (error) {
            console.error('Error accessing camera:', error);
            alert('Unable to access camera. Please ensure you have granted camera permissions.');
        }
    }
    
    function stopImageCamera() {
        if (imageStream) {
            imageStream.getTracks().forEach(track => track.stop());
            imageStream = null;
        }
        
        imageVideo.srcObject = null;
        imageVideo.style.display = 'none';
        $('#imageCameraPlaceholder').show();
        
        startImageCameraBtn.show();
        stopImageCameraBtn.hide();
        captureImageBtn.hide();
    }
    
    function captureImage() {
        const context = imageCanvas.getContext('2d');
        imageCanvas.width = imageVideo.videoWidth;
        imageCanvas.height = imageVideo.videoHeight;
        context.drawImage(imageVideo, 0, 0);
        
        imageCanvas.toBlob(function (blob) {
            const file = new File([blob], 'plant_photo_' + Date.now() + '.jpg', {
                type: 'image/jpeg',
                lastModified: Date.now()
            });
            
            handleImageFile(file);
            stopImageCamera();
            
            // Switch back to upload view to show preview
            uploadImageBtn.click();
        }, 'image/jpeg', 0.9);
    }
    
    // Cleanup on page unload
    $(window).on('beforeunload', function () {
        stopImageCamera();
    });
    
});
