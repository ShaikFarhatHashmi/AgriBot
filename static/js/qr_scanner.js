/**
 * static/js/qr_scanner.js — QR Code Scanner Interface
 * ========================================================
 * Handles QR code upload, camera scanning, and integration with chat.
 */

$(function () {
    
    // ── State ──────────────────────────────────────────────────
    let isScanning = false;
    let currentConvId = null;
    let cameraStream = null;
    let scanInterval = null;
    
    // ── DOM Elements ─────────────────────────────────────────────
    const $qrUploadSection = $("#qrUploadSection");
    const $qrCameraSection = $("#qrCameraSection");
    const $qrInput = $("#qrInput");
    const $qrUploadZone = $("#qrUploadZone");
    const $qrUploadPlaceholder = $("#qrUploadPlaceholder");
    const $qrUploadPreview = $("#qrUploadPreview");
    const $qrPreviewImg = $("#qrPreviewImg");
    const $qrPreviewName = $("#qrPreviewName");
    const $scanQrBtn = $("#scanQrBtn");
    const $startCameraBtn = $("#startCameraBtn");
    const $stopCameraBtn = $("#stopCameraBtn");
    const $captureQrBtn = $("#captureQrBtn");
    const $qrVideo = $("#qrVideo");
    const $qrCanvas = $("#qrCanvas");
    const $cameraPlaceholder = $("#cameraPlaceholder");
    const $qrResultWrap = $("#qrResultWrap");
    const $qrResultLoading = $("#qrResultLoading");
    const $qrResultSuccess = $("#qrResultSuccess");
    const $qrResultError = $("#qrResultError");
    
    // ── Tab Switching ───────────────────────────────────────────
    $("#uploadQrBtn").on("click", function () {
        showUploadSection();
    });
    
    $("#cameraQrBtn").on("click", function () {
        showCameraSection();
    });
    
    function showUploadSection() {
        $("#uploadQrBtn").addClass("active");
        $("#cameraQrBtn").removeClass("active");
        $qrUploadSection.show();
        $qrCameraSection.hide();
        stopCamera();
    }
    
    function showCameraSection() {
        $("#cameraQrBtn").addClass("active");
        $("#uploadQrBtn").removeClass("active");
        $qrUploadSection.hide();
        $qrCameraSection.show();
    }
    
    // ── Upload QR Code ───────────────────────────────────────────
    $qrUploadZone.on("click", function () {
        $qrInput.click();
    });
    
    $qrUploadZone.on("dragover dragenter", function (e) {
        e.preventDefault();
        $(this).addClass("dragover");
    });
    
    $qrUploadZone.on("dragleave dragend drop", function (e) {
        e.preventDefault();
        $(this).removeClass("dragover");
    });
    
    $qrUploadZone.on("drop", function (e) {
        e.preventDefault();
        const files = e.originalEvent.dataTransfer.files;
        if (files.length > 0) {
            handleQrFile(files[0]);
        }
    });
    
    $qrInput.on("change", function () {
        if (this.files.length > 0) {
            handleQrFile(this.files[0]);
        }
    });
    
    $("#removeQrImg").on("click", function () {
        resetQrUpload();
    });
    
    function handleQrFile(file) {
        // Validate file
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff', 'image/webp'];
        if (!validTypes.includes(file.type)) {
            alert("Please upload a valid image file (JPG, PNG, BMP, TIFF, WEBP)");
            return;
        }
        
        if (file.size > 10 * 1024 * 1024) { // 10MB
            alert("File too large. Maximum size: 10MB");
            return;
        }
        
        // Show preview
        const reader = new FileReader();
        reader.onload = function (e) {
            $qrPreviewImg.attr("src", e.target.result);
            $qrPreviewName.text(file.name);
            $qrUploadPlaceholder.hide();
            $qrUploadPreview.show();
            $scanQrBtn.prop("disabled", false);
        };
        reader.readAsDataURL(file);
    }
    
    function resetQrUpload() {
        $qrInput.val("");
        $qrPreviewImg.attr("src", "");
        $qrPreviewName.text("");
        $qrUploadPlaceholder.show();
        $qrUploadPreview.hide();
        $scanQrBtn.prop("disabled", true);
        $qrResultWrap.hide();
    }
    
    // ── Scan QR Code ─────────────────────────────────────────────
    $scanQrBtn.on("click", function () {
        const fileInput = $qrInput[0];
        if (fileInput.files.length > 0) {
            scanQrFromUpload(fileInput.files[0]);
        }
    });
    
    function scanQrFromUpload(file) {
        if (isScanning) return;
        
        isScanning = true;
        $scanQrBtn.prop("disabled", true);
        showQrLoading();
        
        const formData = new FormData();
        formData.append("image", file);
        formData.append("lang", $("#langSelect").val() || "en");
        formData.append("conv_id", currentConvId || "");
        
        $.ajax({
            type: "POST",
            url: "/qr/upload",
            data: formData,
            processData: false,
            contentType: false,
            timeout: 30000,
            success: function (response) {
                if (response.success) {
                    showQrResult(response);
                    if (response.conv_id) {
                        currentConvId = response.conv_id;
                        loadSidebar(); // Update chat history
                    }
                } else {
                    showQrError(response.error || "QR scanning failed");
                }
            },
            error: function (xhr, status, error) {
                let errorMsg = "QR scanning failed. Please try again.";
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                }
                showQrError(errorMsg);
            },
            complete: function () {
                isScanning = false;
                $scanQrBtn.prop("disabled", false);
            }
        });
    }
    
    // ── Camera QR Scanning ───────────────────────────────────────
    $startCameraBtn.on("click", startCamera);
    $stopCameraBtn.on("click", stopCamera);
    $captureQrBtn.on("click", captureFromCamera);
    
    function startCamera() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            alert("Camera not supported in this browser");
            return;
        }
        
        navigator.mediaDevices.getUserMedia({ 
            video: { facingMode: "environment" } 
        })
        .then(function (stream) {
            cameraStream = stream;
            $qrVideo[0].srcObject = stream;
            $qrVideo[0].play();
            
            $cameraPlaceholder.hide();
            $qrVideo.show();
            $startCameraBtn.hide();
            $stopCameraBtn.show();
            $captureQrBtn.show();
            
            // Start scanning for QR codes
            startContinuousScanning();
        })
        .catch(function (error) {
            console.error("Camera error:", error);
            alert("Failed to access camera. Please check permissions.");
        });
    }
    
    function stopCamera() {
        if (scanInterval) {
            clearInterval(scanInterval);
            scanInterval = null;
        }
        
        if (cameraStream) {
            cameraStream.getTracks().forEach(track => track.stop());
            cameraStream = null;
        }
        
        $qrVideo.hide();
        $cameraPlaceholder.show();
        $startCameraBtn.show();
        $stopCameraBtn.hide();
        $captureQrBtn.hide();
    }
    
    function startContinuousScanning() {
        scanInterval = setInterval(function () {
            scanFromVideo();
        }, 1000); // Scan every second
    }
    
    function scanFromVideo() {
        if (!$qrVideo[0] || $qrVideo[0].paused || $qrVideo[0].ended) return;
        
        const canvas = $qrCanvas[0];
        const context = canvas.getContext('2d');
        canvas.width = $qrVideo[0].videoWidth;
        canvas.height = $qrVideo[0].videoHeight;
        context.drawImage($qrVideo[0], 0, 0, canvas.width, canvas.height);
        
        canvas.toBlob(function (blob) {
            scanQrFromCamera(blob);
        }, 'image/jpeg');
    }
    
    function captureFromCamera() {
        if (!$qrVideo[0] || $qrVideo[0].paused || $qrVideo[0].ended) return;
        
        const canvas = $qrCanvas[0];
        const context = canvas.getContext('2d');
        canvas.width = $qrVideo[0].videoWidth;
        canvas.height = $qrVideo[0].videoHeight;
        context.drawImage($qrVideo[0], 0, 0, canvas.width, canvas.height);
        
        canvas.toBlob(function (blob) {
            scanQrFromCamera(blob);
        }, 'image/jpeg');
    }
    
    function scanQrFromCamera(blob) {
        if (isScanning) return;
        
        const formData = new FormData();
        formData.append("image", blob, "qr_camera.jpg");
        formData.append("lang", $("#langSelect").val() || "en");
        formData.append("conv_id", currentConvId || "");
        
        $.ajax({
            type: "POST",
            url: "/qr/camera",
            data: formData,
            processData: false,
            contentType: false,
            timeout: 10000,
            success: function (response) {
                if (response.success) {
                    stopCamera();
                    showQrResult(response);
                    if (response.conv_id) {
                        currentConvId = response.conv_id;
                        loadSidebar(); // Update chat history
                    }
                }
            },
            error: function () {
                // Silent fail for continuous scanning
            }
        });
    }
    
    // ── Result Display ───────────────────────────────────────────
    function showQrLoading() {
        $qrResultWrap.show();
        $qrResultLoading.show();
        $qrResultSuccess.hide();
        $qrResultError.hide();
    }
    
    function showQrResult(response) {
        $qrResultLoading.hide();
        $qrResultError.hide();
        $qrResultSuccess.show();
        
        // Display QR data
        const qrData = response.qr_data;
        const truncated = qrData.length > 100 ? qrData.substring(0, 100) + "..." : qrData;
        $("#qrDataTitle").text("QR Data: " + truncated);
        $("#qrDataDisplay").text(qrData);
        
        // Display confidence
        $("#qrConfBadge").text(Math.round(response.confidence * 100) + "%");
        
        // Display product information
        const productInfo = response.product_info;
        let productHtml = "";
        
        if (productInfo) {
            if (productInfo.type === "url") {
                productHtml = `<strong>URL:</strong> <a href="${productInfo.url}" target="_blank">${productInfo.url}</a><br>`;
                if (productInfo.product_name) {
                    productHtml += `<strong>Product:</strong> ${productInfo.product_name}<br>`;
                }
                if (productInfo.price) {
                    productHtml += `<strong>Price:</strong> ${productInfo.price}<br>`;
                }
                if (productInfo.description) {
                    productHtml += `<strong>Description:</strong> ${productInfo.description}`;
                }
            } else if (productInfo.type === "product_id") {
                productHtml = `<strong>Product ID:</strong> ${productInfo.product_id}<br>`;
                if (productInfo.description) {
                    productHtml += `<strong>Description:</strong> ${productInfo.description}`;
                }
            } else {
                productHtml = `<strong>Type:</strong> ${productInfo.type}<br>`;
                if (productInfo.description) {
                    productHtml += `<strong>Description:</strong> ${productInfo.description}`;
                }
            }
        } else {
            productHtml = "No additional product information available.";
        }
        
        $("#qrProductInfo").html(productHtml);
        
        // Display AI response
        $("#qrChatResponse").text(response.chat_response);
    }
    
    function showQrError(message) {
        $qrResultLoading.hide();
        $qrResultSuccess.hide();
        $qrResultError.show();
        $("#qrErrorMsg").text(message);
    }
    
    // ── Follow-up to Chat ─────────────────────────────────────────
    $("#qrFollowupBtn").on("click", function () {
        // Switch to chat tab
        $("#tab-qr").removeClass("active");
        $("#tab-chat").addClass("active");
        $("#panel-qr").hide();
        $("#panel-chat").show();
        
        // Add a message about the QR scan
        const qrData = $("#qrDataDisplay").text();
        const message = `I just scanned a QR code with data: ${qrData.substring(0, 50)}${qrData.length > 50 ? "..." : ""}. Can you tell me more about this?`;
        
        $("#messageText").val(message);
        $("#messageText").focus();
    });
    
    // ── Helper Functions ─────────────────────────────────────────
    function loadSidebar() {
        // This function should be available from chat.js
        if (typeof window.loadSidebarFromChat === "function") {
            window.loadSidebarFromChat();
        }
    }
    
    // ── Cleanup ─────────────────────────────────────────────────
    $(window).on("beforeunload", function () {
        stopCamera();
    });
    
});
