/**
 * static/js/qr_scanner_simple.js — Simple QR Code Scanner
 * ========================================================
 * Frontend-only QR scanner using JavaScript libraries.
 * No backend dependencies required.
 */

$(function () {
    
    // ── Debug: Log that QR scanner is loading ─────────────────────
    console.log("QR Scanner Simple JavaScript loaded!");
    
    // ── State ──────────────────────────────────────────────────
    let isScanning = false;
    let currentConvId = null;
    
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
        console.log("Showing upload section");
        $("#uploadQrBtn").addClass("active");
        $("#cameraQrBtn").removeClass("active");
        $qrUploadSection.show();
        $qrCameraSection.hide();
        stopCamera();
    }
    
    function showCameraSection() {
        console.log("Showing camera section");
        $("#cameraQrBtn").addClass("active");
        $("#uploadQrBtn").removeClass("active");
        $qrUploadSection.hide();
        $qrCameraSection.show();
    }
    
    // ── Upload QR Code ───────────────────────────────────────────
    // Use a flag to prevent infinite loops
    let isFileDialogOpen = false;
    
    $qrUploadZone.on("click", function (e) {
        if (isFileDialogOpen) return;
        isFileDialogOpen = true;
        console.log("Upload zone clicked");
        
        // Use timeout to break the event loop
        setTimeout(function() {
            $qrInput[0].click();
            isFileDialogOpen = false;
        }, 10);
    });
    
    // Direct file input change handler
    $qrInput.on("change", function (e) {
        console.log("File input changed");
        if (this.files && this.files.length > 0) {
            console.log("Files selected:", this.files.length);
            handleQrFile(this.files[0]);
        } else {
            console.log("No files selected");
        }
        isFileDialogOpen = false;
    });
    
    $("#removeQrImg").on("click", function () {
        resetQrUpload();
    });
    
    // Test button handler
    $("#testQrUploadBtn").on("click", function () {
        console.log("Test upload button clicked");
        alert("Test button clicked! The JavaScript is working. Now try clicking the upload area above.");
    });
    
    function handleQrFile(file) {
        console.log("Handling QR file:", file.name);
        
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
        
        console.log("File validation passed");
        
        // Show preview
        const reader = new FileReader();
        reader.onload = function (e) {
            console.log("File reader loaded, showing preview");
            $qrPreviewImg.attr("src", e.target.result);
            $qrPreviewName.text(file.name);
            $qrUploadPlaceholder.hide();
            $qrUploadPreview.show();
            $scanQrBtn.prop("disabled", false);
            console.log("Preview shown, scan button enabled");
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
    
    // ── Scan QR Code (Frontend Only) ───────────────────────────────
    $scanQrBtn.on("click", function () {
        console.log("Scan QR button clicked");
        const fileInput = $qrInput[0];
        console.log("File input has files:", fileInput.files.length);
        if (fileInput.files.length > 0) {
            simulateQrScan(fileInput.files[0]);
        } else {
            console.log("No files to scan");
            alert("Please upload an image first");
        }
    });
    
    function simulateQrScan(file) {
        console.log("Starting QR scan with backend service for:", file.name);
        
        if (isScanning) {
            console.log("Scan already in progress");
            return;
        }
        
        isScanning = true;
        $scanQrBtn.prop("disabled", true);
        showQrLoading();
        
        console.log("Scan started, showing loading");
        
        // Get selected language
        const selectedLang = $("#qrLangSelect").val() || $("#langSelect").val() || "en";
        console.log("Using language:", selectedLang);
        
        // Create FormData for file upload
        const formData = new FormData();
        formData.append('image', file);
        formData.append('lang', selectedLang);
        
        // Get conversation ID if available
        const convId = currentConvId || "";
        if (convId) {
            formData.append('conv_id', convId);
        }
        
        // Send to backend for actual QR scanning
        $.ajax({
            type: "POST",
            url: "/qr/scan",
            data: formData,
            processData: false,
            contentType: false,
            timeout: 30000, // 30 seconds timeout
            success: function(response) {
                console.log("Backend QR scan response:", response);
                
                if (response.success) {
                    // Format the response for display
                    const formattedResponse = {
                        success: true,
                        qr_data: response.qr_data,
                        product_info: response.product_info,
                        confidence: response.confidence || 0.85,
                        format: response.format || "QR_CODE",
                        chat_response: response.chat_response || "QR code scanned successfully",
                        language: selectedLang,
                        extraction_method: "Backend Service"
                    };
                    
                    console.log("Scan completed, showing results");
                    showQrResult(formattedResponse);
                } else {
                    // Handle error response
                    showQrError(response.error || "QR scan failed");
                }
                
                isScanning = false;
                $scanQrBtn.prop("disabled", false);
            },
            error: function(xhr, status, error) {
                console.error("QR scan error:", status, error);
                
                let errorMessage = "QR scan failed. Please try again.";
                if (status === "timeout") {
                    errorMessage = "QR scan timed out. Please try again.";
                } else if (xhr.status === 400) {
                    errorMessage = "Invalid image file. Please upload a valid QR code image.";
                } else if (xhr.status === 500) {
                    errorMessage = "Server error during QR scan. Please try again later.";
                }
                
                showQrError(errorMessage);
                isScanning = false;
                $scanQrBtn.prop("disabled", false);
            }
        });
    }
    
    function generateAIResponse(qrData, productInfo, language = "en") {
        // Language-specific prefixes
        const langPrefixes = {
            'en': '',
            'hi': 'मैंने एक QR कोड स्कैन किया है जो ',
            'te': 'నేనొక QR కోడ్ స్కాన్ చేశాను అది ',
            'ta': 'நான் ஒரு QR குறியீட்டை ஸ்கேன் செய்தேன் அது ',
            'kn': 'ನಾನು ಒಂದು QR ಕೋಡ್ ಅನ್ನು ಸ್ಕ್ಯಾನ್ ಮಾಡಿದ್ದೇನೆ ಅದು ',
            'ml': 'ഞാൻ ഒരു QR കോഡ് സ്കാൻ ചെയ്തു അത് ',
            'mr': 'मी एक QR कोड स्कॅन केला आहे तो ',
            'bn': 'আমি একটি QR কোড স্ক্যান করেছি যেটি ',
            'gu': 'હું એક QR કોડ સ્કેન કર્યો છું જે ',
            'pa': 'ਮੈਂ ਇੱਕ QR ਕੋਡ ਸਕੈਨ ਕੀਤਾ ਹੈ ਜੋ '
        };
        
        const prefix = langPrefixes[language] || langPrefixes['en'];
        
        // QR Scanner should ONLY analyze QR codes, never provide agricultural information
        if (productInfo.type === "url") {
            let response = prefix + `I successfully extracted a URL from the QR code image. The QR code contains a link to "${productInfo.product_name || 'a product'}" on ${productInfo.platform}. `;
            
            if (language === 'en') {
                if (productInfo.category === "Electronics") {
                    response += `This is an electronic product. ${productInfo.rating ? 'Customer rating: ' + productInfo.rating + '.' : ''} ${productInfo.features ? 'Key features: ' + productInfo.features.join(', ') + '.' : ''} The QR code provides direct access to the product page where you can find detailed specifications, customer reviews, and purchasing options.`;
                } else if (productInfo.category === "Smartphones") {
                    response += `This is a smartphone device. ${productInfo.rating ? 'Rating: ' + productInfo.rating + '.' : ''} ${productInfo.features ? 'Specifications: ' + productInfo.features.join(', ') + '.' : ''} The QR code links to the product page with detailed specs, pricing, and customer reviews.`;
                } else if (productInfo.category === "Programming Books") {
                    response += `This is a technical book. ${productInfo.author ? 'By ' + productInfo.author + '.' : ''} ${productInfo.features ? 'Book details: ' + productInfo.features.join(', ') + '.' : ''} The QR code provides access to purchase options, sample chapters, and customer reviews.`;
                } else if (productInfo.category === "Food Delivery") {
                    response += `This is a food service listing on ${productInfo.platform}. ${productInfo.rating ? 'Rating: ' + productInfo.rating + '.' : ''} ${productInfo.features ? 'Services: ' + productInfo.features.join(', ') + '.' : ''} The QR code gives instant access to the menu, customer reviews, and ordering options.`;
                } else if (productInfo.category === "Fashion") {
                    response += `This is a fashion item from ${productInfo.brand || 'a brand'}. ${productInfo.features ? 'Product details: ' + productInfo.features.join(', ') + '.' : ''} The QR code links to the product page with size charts, reviews, and availability.`;
                } else {
                    response += `This is an online product listing. The QR code contains a direct link to the product page where you can view full details, check specifications, and make a purchase.`;
                }
                response += ` I extracted this information directly from the QR code image you provided.`;
            } else {
                response += `This is a ${productInfo.product_name || 'product'} from ${productInfo.platform || 'online store'}. The QR code contains the direct link.`;
            }
            
            return response;
            
        } else if (productInfo.type === "product_id") {
            let response = prefix + `I successfully extracted a product identifier from the QR code image: ${qrData}. `;
            
            if (language === 'en') {
                if (productInfo.product_id_type === "UPC" || productInfo.product_id_type === "EAN") {
                    response += `This is a ${productInfo.product_id_type} barcode for "${productInfo.product_name || 'a product'}"${productInfo.manufacturer ? ' from ' + productInfo.manufacturer : ''}. ${productInfo.features ? 'Product information: ' + productInfo.features.join(', ') + '.' : ''} I decoded this from the QR code. Use this code to look up product details in retail databases or compare prices.`;
                } else if (productInfo.product_id_type === "ISBN") {
                    response += `This is an ISBN for "${productInfo.product_name || 'a book'}"${productInfo.author ? ' by ' + productInfo.author : ''}. ${productInfo.features ? 'Book details: ' + productInfo.features.join(', ') + '.' : ''} I extracted this ISBN from the QR code. Use it to find book information, compare prices, or check library availability.`;
                } else if (productInfo.product_id_type === "SKU") {
                    response += `This is a SKU for "${productInfo.product_name || 'a product'}"${productInfo.manufacturer ? ' from ' + productInfo.manufacturer : ''}. ${productInfo.features ? 'Specifications: ' + productInfo.features.join(', ') + '.' : ''} I decoded this SKU from the QR code. Contact the manufacturer for detailed specifications and pricing.`;
                } else {
                    response += `This is a product identifier I extracted from the QR code. For detailed information about this product, contact the manufacturer or supplier directly.`;
                }
            } else {
                response += `This is a ${productInfo.product_id_type || 'product ID'} for ${productInfo.product_name || 'a product'}. I extracted this from the QR code.`;
            }
            
            return response;
            
        } else if (productInfo.type === "wifi_config") {
            let response = prefix + `I successfully extracted Wi-Fi network settings from the QR code image. `;
            
            if (language === 'en') {
                response += `The QR code contains connection details for "${productInfo.network_name || 'the network'}". ${productInfo.features ? 'Network features: ' + productInfo.features.join(', ') + '.' : ''} I decoded this Wi-Fi information from the QR code. You can use it to connect devices automatically without entering credentials manually. Ensure you trust the network before connecting.`;
            } else {
                response += `This QR code contains Wi-Fi connection settings. I extracted this information.`;
            }
            
            return response;
            
        } else if (productInfo.type === "contact_info") {
            let response = prefix + `I successfully extracted contact information from the QR code image. `;
            
            if (language === 'en') {
                response += `The QR code contains a digital business card. ${productInfo.features ? 'Features: ' + productInfo.features.join(', ') + '.' : ''} I decoded this contact information from the QR code. You can save it to your phone, call the number, or send email without typing manually.`;
            } else {
                response += `This QR code contains contact information. I extracted this data.`;
            }
            
            return response;
            
        } else if (productInfo.type === "location") {
            let response = prefix + `I successfully extracted location data from the QR code image. `;
            
            if (language === 'en') {
                response += `The QR code points to: ${productInfo.location || 'a specific location'}. ${productInfo.features ? 'Location features: ' + productInfo.features.join(', ') + '.' : ''} I decoded these coordinates from the QR code. You can open this location in maps, get directions, or share it with others.`;
            } else {
                response += `This QR code contains location information. I extracted these coordinates.`;
            }
            
            return response;
            
        } else {
            if (language === 'en') {
                return `I successfully scanned the QR code image and extracted: ${qrData}. This is general data decoded from the QR code. For specific product information, ensure the QR code contains a direct link or standardized identifier like UPC, EAN, or ISBN. I extracted this information directly from your QR code image.`;
            } else {
                return prefix + `contains: ${qrData}. I extracted this data from the QR code image.`;
            }
        }
    }
    
    // ── Camera QR Scanning ───────────────────────────────
    $startCameraBtn.on("click", function () {
        console.log("Start camera button clicked");
        startCamera();
    });
    
    $stopCameraBtn.on("click", function () {
        console.log("Stop camera button clicked");
        stopCamera();
    });
    
    $captureQrBtn.on("click", function () {
        console.log("Capture QR button clicked");
        captureQrFromCamera();
    });
    
    let cameraStream = null;
    let isCameraActive = false;
    
    async function startCamera() {
        try {
            console.log("Starting camera...");
            
            // Request camera permission
            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    facingMode: 'environment', // Use back camera if available
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                } 
            });
            
            cameraStream = stream;
            isCameraActive = true;
            
            // Show video element and hide placeholder
            $qrVideo.show();
            $cameraPlaceholder.hide();
            
            // Set video source and play it
            const video = $qrVideo[0];
            video.srcObject = stream;
            video.play(); // Ensure video starts playing
            
            // Show camera controls
            $startCameraBtn.hide();
            $stopCameraBtn.show();
            $captureQrBtn.show();
            
            console.log("Camera started successfully");
            
        } catch (error) {
            console.error("Camera error:", error);
            let errorMessage = "Camera access denied or not available.";
            
            if (error.name === 'NotAllowedError') {
                errorMessage = "Camera permission denied. Please allow camera access and try again.";
            } else if (error.name === 'NotFoundError') {
                errorMessage = "No camera found on this device.";
            } else if (error.name === 'NotReadableError') {
                errorMessage = "Camera is already in use by another application.";
            }
            
            alert(errorMessage);
        }
    }
    
    function stopCamera() {
        console.log("Stopping camera...");
        
        if (cameraStream) {
            // Stop all video tracks
            cameraStream.getTracks().forEach(track => track.stop());
            cameraStream = null;
        }
        
        // Hide video and show placeholder
        $qrVideo.hide();
        $cameraPlaceholder.show();
        
        // Reset camera controls
        $startCameraBtn.show();
        $stopCameraBtn.hide();
        $captureQrBtn.hide();
        
        // Clear video source
        $qrVideo[0].srcObject = null;
        
        isCameraActive = false;
        console.log("Camera stopped");
    }
    
    function captureQrFromCamera() {
        if (!isCameraActive || !cameraStream) {
            console.log("Camera not active");
            alert("Please start the camera first");
            return;
        }
        
        console.log("Capturing QR from camera");
        
        // Create canvas for capture
        const canvas = $qrCanvas[0];
        const video = $qrVideo[0];
        
        // Set canvas dimensions to match video
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        // Draw current video frame to canvas
        const context = canvas.getContext('2d');
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Show captured image preview briefly
        const capturedImageUrl = canvas.toDataURL('image/jpeg');
        
        // Create a temporary preview element
        const $preview = $('<div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); z-index: 10000;">' +
            '<h4 style="margin: 0 0 10px 0; color: #28a745;">✓ QR Code Captured!</h4>' +
            '<img src="' + capturedImageUrl + '" style="max-width: 200px; max-height: 200px; border-radius: 4px; margin-bottom: 10px;">' +
            '<p style="margin: 0; color: #666; font-size: 14px;">Processing...</p>' +
            '</div>');
        
        $('body').append($preview);
        
        // Remove preview after 1.5 seconds and process the image
        setTimeout(function() {
            $preview.remove();
            
            // Convert canvas to blob (image file)
            canvas.toBlob(function(blob) {
                // Create file object from blob
                const file = new File([blob], "camera_capture.jpg", { 
                    type: "image/jpeg",
                    lastModified: Date.now()
                });
                
                console.log("Camera captured, processing file with backend service");
                
                // Stop camera after capture
                stopCamera();
                
                // Process the captured image using backend service
                processCameraCapture(file);
                
            }, 'image/jpeg', 0.9);
        }, 1500);
    }
    
    function processCameraCapture(file) {
        console.log("Processing camera capture with backend service");
        
        if (isScanning) {
            console.log("Scan already in progress");
            return;
        }
        
        isScanning = true;
        showQrLoading();
        
        console.log("Camera scan started, showing loading");
        
        // Get selected language
        const selectedLang = $("#qrLangSelect").val() || $("#langSelect").val() || "en";
        console.log("Using language:", selectedLang);
        
        // Create FormData for file upload
        const formData = new FormData();
        formData.append('image', file);
        formData.append('lang', selectedLang);
        
        // Get conversation ID if available
        const convId = currentConvId || "";
        if (convId) {
            formData.append('conv_id', convId);
        }
        
        // Send to backend for actual QR scanning
        $.ajax({
            type: "POST",
            url: "/qr/scan",
            data: formData,
            processData: false,
            contentType: false,
            timeout: 30000, // 30 seconds timeout
            success: function(response) {
                console.log("Backend camera QR scan response:", response);
                
                if (response.success) {
                    // Format the response for display
                    const formattedResponse = {
                        success: true,
                        qr_data: response.qr_data,
                        product_info: response.product_info,
                        confidence: response.confidence || 0.85,
                        format: response.format || "QR_CODE",
                        chat_response: response.chat_response || "QR code scanned successfully from camera",
                        language: selectedLang,
                        extraction_method: "Camera Capture"
                    };
                    
                    console.log("Camera scan completed, showing results");
                    showQrResult(formattedResponse);
                } else {
                    // Handle error response
                    showQrError(response.error || "Camera QR scan failed");
                }
                
                isScanning = false;
            },
            error: function(xhr, status, error) {
                console.error("Camera QR scan error:", status, error);
                
                let errorMessage = "Camera QR scan failed. Please try again.";
                if (status === "timeout") {
                    errorMessage = "Camera QR scan timed out. Please try again.";
                } else if (xhr.status === 400) {
                    errorMessage = "Invalid camera image. Please capture a clear QR code.";
                } else if (xhr.status === 500) {
                    errorMessage = "Server error during camera QR scan. Please try again later.";
                }
                
                showQrError(errorMessage);
                isScanning = false;
            }
        });
    }
    
    // Cleanup on page unload
    $(window).on('beforeunload', function() {
        stopCamera();
    });
    
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
        
        // Display comprehensive product information
        const productInfo = response.product_info;
        let productHtml = "";
        
        if (productInfo) {
            productHtml = '<div class="product-details">';
            
            // Platform/Type info
            if (productInfo.platform) {
                productHtml += `<div class="product-platform"><strong>Platform:</strong> ${productInfo.platform}</div>`;
            }
            if (productInfo.type) {
                productHtml += `<div class="product-type"><strong>Type:</strong> ${productInfo.type}</div>`;
            }
            
            // Product ID info
            if (productInfo.product_id) {
                productHtml += `<div class="product-id"><strong>${productInfo.product_id_type || 'Product ID'}:</strong> ${productInfo.product_id}</div>`;
            }
            
            // URL info
            if (productInfo.url) {
                productHtml += `<div class="product-url"><strong>URL:</strong> <a href="${productInfo.url}" target="_blank" rel="noopener noreferrer">${productInfo.url}</a></div>`;
            }
            
            // Category
            if (productInfo.category) {
                productHtml += `<div class="product-category"><strong>Category:</strong> ${productInfo.category}</div>`;
            }
            
            // Availability
            if (productInfo.availability) {
                productHtml += `<div class="product-availability"><strong>Availability:</strong> ${productInfo.availability}</div>`;
            }
            
            // Price
            if (productInfo.price) {
                productHtml += `<div class="product-price"><strong>Price:</strong> ${productInfo.price}</div>`;
            }
            
            // Brand
            if (productInfo.brand) {
                productHtml += `<div class="product-brand"><strong>Brand:</strong> ${productInfo.brand}</div>`;
            }
            
            // Description
            if (productInfo.description) {
                productHtml += `<div class="product-description"><strong>Description:</strong><br>${productInfo.description}</div>`;
            }
            
            // Features
            if (productInfo.features && productInfo.features.length > 0) {
                productHtml += '<div class="product-features"><strong>Features:</strong><ul>';
                productInfo.features.forEach(feature => {
                    productHtml += `<li>${feature}</li>`;
                });
                productHtml += '</ul></div>';
            }
            
            // Actions
            if (productInfo.actions && productInfo.actions.length > 0) {
                productHtml += '<div class="product-actions"><strong>Actions:</strong><ul>';
                productInfo.actions.forEach(action => {
                    productHtml += `<li>${action}</li>`;
                });
                productHtml += '</ul></div>';
            }
            
            // Notes
            if (productInfo.note) {
                productHtml += `<div class="product-note"><strong>Note:</strong> ${productInfo.note}</div>`;
            }
            
            productHtml += '</div>';
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
    
    // ── Cleanup ─────────────────────────────────────────────────
    $(window).on("beforeunload", function () {
        stopCamera();
    });
    
    console.log("QR Scanner Simple JavaScript fully loaded and ready!");
    
    // Sync QR language selector with main chat language selector
    function syncLanguageSelectors() {
        const mainLang = $("#langSelect").val();
        $("#qrLangSelect").val(mainLang);
    }
    
    // Update QR language when main language changes
    $("#langSelect").on("change", function() {
        syncLanguageSelectors();
    });
    
    // Update main language when QR language changes
    $("#qrLangSelect").on("change", function() {
        $("#langSelect").val($(this).val());
    });
    
    // Initial sync
    syncLanguageSelectors();
    
});
