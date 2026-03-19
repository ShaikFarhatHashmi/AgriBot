/**
 * static/js/detect.js
 *
 * Responsibilities:
 *   - Tab switching (Chat / Disease Detection / QR Scanner)
 *   - Disease Detection: Upload mode + Camera mode (capture & analyse)
 *   - QR Scanner: Camera mode (auto-scan frames) + Upload mode
 *   - POST /image/predict  -> disease result + RAG answer
 *   - POST /qr/scan        -> QR decode + RAG explanation
 *   - "Ask follow-up in Chat" shortcuts
 */

$(function () {

    // ==========================================================
    //  TAB SWITCHING
    // ==========================================================
    $('.mode-tab').on('click', function () {
        var tab = $(this).data('tab');
        $('.mode-tab').removeClass('active');
        $(this).addClass('active');
        $('.tab-panel').hide();
        $('#panel-' + tab).show();

        // Stop cameras when switching away
        if (tab !== 'image') stopDiseaseCamera();
        if (tab !== 'qr')    stopQRCamera();
    });

    // ==========================================================
    //  DISEASE DETECTION
    // ==========================================================
    var selectedFile    = null;
    var lastDisease     = '';
    var diseaseCamStream = null;
    var diseaseCaptured  = null;   // Blob captured from camera

    // Element refs - upload mode
    var $uploadZone  = $('#uploadZone');
    var $imageInput  = $('#imageInput');
    var $placeholder = $('#uploadPlaceholder');
    var $preview     = $('#uploadPreview');
    var $previewImg  = $('#previewImg');
    var $previewName = $('#previewName');
    var $removeBtn   = $('#removeImg');
    var $analyseBtn  = $('#analyseBtn');

    // Element refs - result card
    var $resultWrap  = $('#resultWrap');
    var $loading     = $('#resultLoading');
    var $success     = $('#resultSuccess');
    var $errorDiv    = $('#resultError');
    var $confBadge   = $('#confBadge');
    var $diseaseName = $('#diseaseName');
    var $warnBox     = $('#warnBox');
    var $warnText    = $('#warnText');
    var $ragBody     = $('#ragBody');
    var $errorMsg    = $('#errorMsg');
    var $followupBtn = $('#followupBtn');

    // -- Disease mode switcher ---------------------------------
    window.switchDiseaseMode = function (mode) {
        if (mode === 'upload') {
            $('#diseaseBtnUpload').addClass('active');
            $('#diseaseBtnCamera').removeClass('active');
            $('#diseaseUploadMode').show();
            $('#diseaseCameraMode').hide();
            stopDiseaseCamera();
        } else {
            $('#diseaseBtnCamera').addClass('active');
            $('#diseaseBtnUpload').removeClass('active');
            $('#diseaseCameraMode').show();
            $('#diseaseUploadMode').hide();
        }
        $resultWrap.hide();
    };

    // -- Disease upload events ---------------------------------
    $uploadZone.on('click', function (e) {
        if ($(e.target).closest('#removeImg').length) return;
        if ($(e.target).is($imageInput)) return;
        $imageInput[0].click();
    });

    $imageInput.on('change', function () {
        if (this.files && this.files[0]) handleFile(this.files[0]);
    });

    $uploadZone.on('dragover', function (e) {
        e.preventDefault();
        $uploadZone.addClass('drag-over');
    });
    $uploadZone.on('dragleave', function () {
        $uploadZone.removeClass('drag-over');
    });
    $uploadZone.on('drop', function (e) {
        e.preventDefault();
        $uploadZone.removeClass('drag-over');
        var file = e.originalEvent.dataTransfer.files[0];
        if (file) handleFile(file);
    });

    $removeBtn.on('click', function (e) {
        e.stopPropagation();
        resetUpload();
    });

    $analyseBtn.on('click', function () {
        if (!selectedFile) return;
        runPrediction(selectedFile);
    });

    function handleFile(file) {
        var allowed = ['image/jpeg', 'image/png', 'image/webp'];
        if (!allowed.includes(file.type)) {
            showError('Invalid file type. Please upload a JPG, PNG, or WEBP image.');
            return;
        }
        if (file.size > 5 * 1024 * 1024) {
            showError('File too large. Maximum allowed size is 5 MB.');
            return;
        }
        selectedFile = file;
        var reader = new FileReader();
        reader.onload = function (e) {
            $previewImg.attr('src', e.target.result);
            $previewName.text(file.name);
            $placeholder.hide();
            $preview.show();
            $analyseBtn.prop('disabled', false);
            $resultWrap.hide();
        };
        reader.readAsDataURL(file);
    }

    function resetUpload() {
        selectedFile = null;
        $imageInput.val('');
        $previewImg.attr('src', '');
        $previewName.text('');
        $placeholder.show();
        $preview.hide();
        $analyseBtn.prop('disabled', true);
        $resultWrap.hide();
    }

    // -- Disease camera events ---------------------------------
    $('#diseaseStartCameraBtn').on('click', function () {
        startDiseaseCamera();
    });
    $('#diseaseStopCameraBtn').on('click', function () {
        stopDiseaseCamera();
    });
    $('#diseaseCaptureBtn').on('click', function () {
        captureDiseasePicture();
    });
    $('#diseaseRetakeBtn').on('click', function () {
        retakeDiseasePicture();
    });
    $('#diseaseAnalyseCapturedBtn').on('click', function () {
        if (!diseaseCaptured) return;
        var file = new File([diseaseCaptured], 'capture.jpg',
                            { type: 'image/jpeg' });
        runPrediction(file);
    });

    function startDiseaseCamera() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            $('#diseaseCameraStatus').text(
                'Camera not supported in this browser.');
            return;
        }
        navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: { ideal: 'environment' },
                width:  { ideal: 1280 },
                height: { ideal: 720 }
            }
        }).then(function (stream) {
            diseaseCamStream = stream;
            var video = document.getElementById('diseaseVideo');
            video.srcObject = stream;
            video.style.display = 'block';

            $('#diseaseCameraPlaceholder').hide();
            $('#diseaseCamOverlay').show();
            $('#diseaseStartCameraBtn').hide();
            $('#diseaseCaptureBtn').show();
            $('#diseaseStopCameraBtn').show();
            $('#diseaseCapturePreview').hide();
            $resultWrap.hide();
            $('#diseaseCameraStatus').text(
                'Camera ready — centre the leaf and press Capture.');
        }).catch(function (err) {
            var msg = 'Camera access denied.';
            if (err.name === 'NotFoundError')
                msg = 'No camera found on this device.';
            else if (err.name === 'NotAllowedError')
                msg = 'Camera permission denied. Please allow camera access.';
            $('#diseaseCameraStatus').text(msg);
        });
    }

    function stopDiseaseCamera() {
        if (diseaseCamStream) {
            diseaseCamStream.getTracks().forEach(function (t) { t.stop(); });
            diseaseCamStream = null;
        }
        var video = document.getElementById('diseaseVideo');
        if (video) { video.srcObject = null; video.style.display = 'none'; }

        $('#diseaseCameraPlaceholder').show();
        $('#diseaseCamOverlay').hide();
        $('#diseaseStartCameraBtn').show();
        $('#diseaseCaptureBtn').hide();
        $('#diseaseStopCameraBtn').hide();
        $('#diseaseCapturePreview').hide();
        $('#diseaseCameraStatus').text('');
        diseaseCaptured = null;
    }

    function captureDiseasePicture() {
        var video  = document.getElementById('diseaseVideo');
        var canvas = document.getElementById('diseaseCanvas');
        canvas.width  = video.videoWidth  || 640;
        canvas.height = video.videoHeight || 480;
        canvas.getContext('2d').drawImage(
            video, 0, 0, canvas.width, canvas.height);

        canvas.toBlob(function (blob) {
            diseaseCaptured = blob;
            var url = URL.createObjectURL(blob);
            $('#diseaseCapturedImg').attr('src', url);
            $('#diseaseCapturePreview').show();

            video.style.display = 'none';
            $('#diseaseCamOverlay').hide();
            $('#diseaseCaptureBtn').hide();
            $('#diseaseCameraStatus').text(
                'Photo captured — press Analyse or Retake.');
        }, 'image/jpeg', 0.92);
    }

    function retakeDiseasePicture() {
        diseaseCaptured = null;
        $('#diseaseCapturePreview').hide();
        var video = document.getElementById('diseaseVideo');
        video.style.display = 'block';
        $('#diseaseCamOverlay').show();
        $('#diseaseCaptureBtn').show();
        $resultWrap.hide();
        $('#diseaseCameraStatus').text(
            'Camera ready — centre the leaf and press Capture.');
    }

    // -- Disease prediction shared by both modes ---------------
    function runPrediction(file) {
        showLoading();
        var formData = new FormData();
        formData.append('image', file);
        formData.append('lang',
            $('#langSelect').val() || 'en');
        formData.append('conv_id',
            (typeof currentConvId !== 'undefined' ? currentConvId : '') || '');

        $.ajax({
            type: 'POST', url: '/image/predict',
            data: formData, processData: false, contentType: false,
            success: function (response) {
                if (response.success) {
                    showSuccess(response);
                    if (response.conv_id && typeof loadSidebar === 'function') {
                        if (typeof currentConvId !== 'undefined')
                            currentConvId = response.conv_id;
                        loadSidebar();
                    }
                } else {
                    showError(response.error || 'Prediction failed. Please try again.');
                }
            },
            error: function (xhr) {
                var msg = 'Network error. Please check your connection.';
                try {
                    var b = JSON.parse(xhr.responseText);
                    if (b.error) msg = b.error;
                } catch (e) {}
                showError(msg);
            }
        });
    }

    function showLoading() {
        $analyseBtn.prop('disabled', true);
        $resultWrap.show();
        $loading.show();
        $success.hide();
        $errorDiv.hide();
    }

    function showSuccess(data) {
        $loading.hide(); $errorDiv.hide(); $success.show();
        lastDisease = data.disease || '';
        $diseaseName.text(data.disease || 'Unknown');
        var conf = parseFloat(data.confidence) || 0;
        $confBadge.text(conf.toFixed(1) + '%')
                  .toggleClass('low', !data.reliable);
        if (data.warning) { $warnText.text(data.warning); $warnBox.show(); }
        else              { $warnBox.hide(); }
        $ragBody.text('');
        typewriterText(data.rag_answer || 'No treatment info available.',
                       $ragBody);
        $analyseBtn.prop('disabled', false);
    }

    function showError(message) {
        $loading.hide(); $success.hide();
        $errorMsg.text(message);
        $errorDiv.show(); $resultWrap.show();
        $analyseBtn.prop('disabled', false);
    }

    $followupBtn.on('click', function () {
        $('#tab-chat').trigger('click');
        $('#messageText').val(
            'Tell me more about how to treat ' + lastDisease).focus();
    });

    // ==========================================================
    //  QR SCANNER — Camera + Upload
    // ==========================================================
    var $qrUploadZone  = $('#qrUploadZone');
    var $qrInput       = $('#qrInput');
    var $qrPlaceholder = $('#qrPlaceholder');
    var $qrPreview     = $('#qrPreview');
    var $qrPreviewImg  = $('#qrPreviewImg');
    var $qrPreviewName = $('#qrPreviewName');
    var $qrRemove      = $('#qrRemove');
    var $qrScanBtn     = $('#qrScanBtn');
    var $qrResultWrap  = $('#qrResultWrap');
    var $qrLoading     = $('#qrLoading');
    var $qrSuccess     = $('#qrSuccess');
    var $qrError       = $('#qrError');
    var $qrRawText     = $('#qrRawText');
    var $qrExplanation = $('#qrExplanation');
    var $qrErrorMsg    = $('#qrErrorMsg');
    var $qrFollowupBtn = $('#qrFollowupBtn');

    var qrSelectedFile = null;
    var lastQRText     = '';
    var qrCamStream    = null;
    var scanInterval   = null;

    // -- QR mode switcher -------------------------------------
    window.switchQRMode = function (mode) {
        if (mode === 'camera') {
            $('#qrBtnCamera').addClass('active');
            $('#qrBtnUpload').removeClass('active');
            $('#qrCameraMode').show();
            $('#qrUploadMode').hide();
        } else {
            $('#qrBtnUpload').addClass('active');
            $('#qrBtnCamera').removeClass('active');
            $('#qrUploadMode').show();
            $('#qrCameraMode').hide();
            stopQRCamera();
        }
        $qrResultWrap.hide();
    };

    // -- QR camera events -------------------------------------
    $('#qrStartCameraBtn').on('click', function () { startQRCamera(); });
    $('#qrStopCameraBtn').on('click',  function () { stopQRCamera();  });

    function startQRCamera() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            $('#qrCameraStatus').text('Camera not supported in this browser.');
            return;
        }
        navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: { ideal: 'environment' },
                width:  { ideal: 640 },
                height: { ideal: 480 }
            }
        }).then(function (stream) {
            qrCamStream = stream;
            var video = document.getElementById('qrVideo');
            video.srcObject = stream;
            video.style.display = 'block';

            $('#qrCameraPlaceholder').hide();
            $('#qrScanOverlay').show();
            $('#qrStartCameraBtn').hide();
            $('#qrStopCameraBtn').show();
            $('#qrCameraStatus').text(
                'Camera active — scanning for QR code…');

            video.onloadedmetadata = function () {
                video.play();
                scanInterval = setInterval(function () {
                    scanFrameForQR(video);
                }, 500);
            };
        }).catch(function (err) {
            var msg = 'Camera access denied.';
            if (err.name === 'NotFoundError')
                msg = 'No camera found on this device.';
            else if (err.name === 'NotAllowedError')
                msg = 'Camera permission denied. Please allow camera access.';
            $('#qrCameraStatus').text(msg);
        });
    }

    function stopQRCamera() {
        if (scanInterval) { clearInterval(scanInterval); scanInterval = null; }
        if (qrCamStream) {
            qrCamStream.getTracks().forEach(function (t) { t.stop(); });
            qrCamStream = null;
        }
        var video = document.getElementById('qrVideo');
        if (video) { video.srcObject = null; video.style.display = 'none'; }

        $('#qrCameraPlaceholder').show();
        $('#qrScanOverlay').hide();
        $('#qrStartCameraBtn').show();
        $('#qrStopCameraBtn').hide();
        $('#qrCameraStatus').text('');
    }

    function scanFrameForQR(video) {
        var canvas  = document.getElementById('qrCanvas');
        var context = canvas.getContext('2d');
        canvas.width  = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        canvas.toBlob(function (blob) {
            if (!blob) return;
            clearInterval(scanInterval);
            scanInterval = null;
            $('#qrCameraStatus').text(
                'QR code detected — fetching information…');

            var file = new File([blob], 'frame.jpg', { type: 'image/jpeg' });
            runQRScan(file, function (success) {
                if (!success) {
                    $('#qrCameraStatus').text(
                        'Camera active — scanning for QR code…');
                    if (qrCamStream) {
                        scanInterval = setInterval(function () {
                            scanFrameForQR(video);
                        }, 500);
                    }
                }
            });
        }, 'image/jpeg', 0.92);
    }

    // -- QR upload events -------------------------------------
    $qrUploadZone.on('click', function (e) {
        if ($(e.target).closest('#qrRemove').length) return;
        if ($(e.target).is($qrInput)) return;
        $qrInput[0].click();
    });
    $qrInput.on('change', function () {
        if (this.files && this.files[0]) handleQRFile(this.files[0]);
    });
    $qrUploadZone.on('dragover', function (e) {
        e.preventDefault(); $qrUploadZone.addClass('drag-over');
    });
    $qrUploadZone.on('dragleave', function () {
        $qrUploadZone.removeClass('drag-over');
    });
    $qrUploadZone.on('drop', function (e) {
        e.preventDefault();
        $qrUploadZone.removeClass('drag-over');
        var file = e.originalEvent.dataTransfer.files[0];
        if (file) handleQRFile(file);
    });
    $qrRemove.on('click', function (e) {
        e.stopPropagation(); resetQRUpload();
    });
    $qrScanBtn.on('click', function () {
        if (!qrSelectedFile) return;
        runQRScan(qrSelectedFile, null);
    });

    function handleQRFile(file) {
        var allowed = ['image/jpeg', 'image/png', 'image/webp'];
        if (!allowed.includes(file.type)) {
            showQRError('Invalid file type. Please upload JPG, PNG or WEBP.');
            return;
        }
        if (file.size > 5 * 1024 * 1024) {
            showQRError('File too large. Maximum size is 5 MB.');
            return;
        }
        qrSelectedFile = file;
        var reader = new FileReader();
        reader.onload = function (e) {
            $qrPreviewImg.attr('src', e.target.result);
            $qrPreviewName.text(file.name);
            $qrPlaceholder.hide();
            $qrPreview.show();
            $qrScanBtn.prop('disabled', false);
            $qrResultWrap.hide();
        };
        reader.readAsDataURL(file);
    }

    function resetQRUpload() {
        qrSelectedFile = null;
        $qrInput.val('');
        $qrPreviewImg.attr('src', '');
        $qrPreviewName.text('');
        $qrPlaceholder.show();
        $qrPreview.hide();
        $qrScanBtn.prop('disabled', true);
        $qrResultWrap.hide();
    }

    // -- QR scan shared by camera + upload --------------------
    function runQRScan(file, callback) {
        $qrResultWrap.show();
        $qrLoading.show();
        $qrSuccess.hide();
        $qrError.hide();

        var formData = new FormData();
        formData.append('image', file);
        formData.append('lang',
            $('#langSelect').val() || 'en');
        formData.append('conv_id',
            (typeof currentConvId !== 'undefined' ? currentConvId : '') || '');

        $.ajax({
            type: 'POST', url: '/qr/scan',
            data: formData, processData: false, contentType: false,
            success: function (response) {
                $qrLoading.hide();
                if (response.success) {
                    stopQRCamera();
                    lastQRText = response.qr_text || '';
                    $qrRawText.text(response.qr_text);
                    $qrSuccess.show();
                    $qrExplanation.text('');
                    typewriterText(
                        response.explanation || 'No information available.',
                        $qrExplanation);
                    if (response.conv_id && typeof loadSidebar === 'function') {
                        if (typeof currentConvId !== 'undefined')
                            currentConvId = response.conv_id;
                        loadSidebar();
                    }
                    if (callback) callback(true);
                } else {
                    $qrResultWrap.hide();
                    if (callback) callback(false);
                    else showQRError(response.error || 'No QR code found.');
                }
            },
            error: function (xhr) {
                $qrLoading.hide();
                $qrResultWrap.hide();
                var msg = 'Network error. Please try again.';
                try {
                    var b = JSON.parse(xhr.responseText);
                    if (b.error) msg = b.error;
                } catch (e) {}
                if (callback) callback(false);
                else showQRError(msg);
            }
        });
    }

    $qrFollowupBtn.on('click', function () {
        $('#tab-chat').trigger('click');
        $('#messageText').val('Tell me more about ' + lastQRText).focus();
    });

    function showQRError(message) {
        $qrLoading.hide(); $qrSuccess.hide();
        $qrErrorMsg.text(message);
        $qrError.show(); $qrResultWrap.show();
    }

    // ==========================================================
    //  TYPEWRITER — shared by disease + QR panels
    // ==========================================================
    function typewriterText(text, $el, speed) {
        speed = speed || 10;
        var i = 0;
        $el.text('');
        var iv = setInterval(function () {
            if (i < text.length) {
                $el.text($el.text() + text.charAt(i));
                i++;
                var scroll = $('.detect-scroll')[0];
                if (scroll) scroll.scrollTop = scroll.scrollHeight;
            } else {
                clearInterval(iv);
                $el.text(text);
            }
        }, speed);
    }

});