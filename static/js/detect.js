/**
 * static/js/detect.js — Plant Disease Detection UI
 *
 * Responsibilities:
 *   - Tab switching (Chat ↔ Disease Detection)
 *   - Image upload: click-to-pick + drag-and-drop + preview
 *   - Client-side validation (type, size)
 *   - POST /image/predict → show CNN result + RAG answer
 *   - "Ask follow-up in Chat" shortcut
 */

$(function () {

    // ── Element refs ───────────────────────────────────────────
    const $uploadZone   = $('#uploadZone');
    const $imageInput   = $('#imageInput');
    const $placeholder  = $('#uploadPlaceholder');
    const $preview      = $('#uploadPreview');
    const $previewImg   = $('#previewImg');
    const $previewName  = $('#previewName');
    const $removeBtn    = $('#removeImg');
    const $analyseBtn   = $('#analyseBtn');
    const $resultWrap   = $('#resultWrap');
    const $loading      = $('#resultLoading');
    const $success      = $('#resultSuccess');
    const $errorDiv     = $('#resultError');
    const $confBadge    = $('#confBadge');
    const $diseaseName  = $('#diseaseName');
    const $warnBox      = $('#warnBox');
    const $warnText     = $('#warnText');
    const $ragBody      = $('#ragBody');
    const $errorMsg     = $('#errorMsg');
    const $followupBtn  = $('#followupBtn');

    let selectedFile   = null;
    let lastDisease    = '';

    // ── Tab switching ──────────────────────────────────────────
    $('.mode-tab').on('click', function () {
        const tab = $(this).data('tab');

        $('.mode-tab').removeClass('active');
        $(this).addClass('active');

        $('.tab-panel').hide();
        $('#panel-' + tab).show();
    });

    // ── Click upload zone to open file picker ──────────────────
    $uploadZone.on('click', function (e) {
        if ($(e.target).closest('#removeImg').length) return;
        if ($(e.target).is($imageInput)) return; 
        $imageInput.trigger('click');
    });

    // ── File selected via picker ───────────────────────────────
    $imageInput.on('change', function () {
        if (this.files && this.files[0]) {
            handleFile(this.files[0]);
        }
    });

    // ── Drag and drop ──────────────────────────────────────────
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
        const file = e.originalEvent.dataTransfer.files[0];
        if (file) handleFile(file);
    });

    // ── Remove image ───────────────────────────────────────────
    $removeBtn.on('click', function (e) {
        e.stopPropagation();
        resetUpload();
    });

    // ── Analyse button ─────────────────────────────────────────
    $analyseBtn.on('click', function () {
        if (!selectedFile) return;
        runPrediction(selectedFile);
    });

    // ── Follow-up: switch to chat tab, pre-fill the question ───
    $followupBtn.on('click', function () {
        // Switch to chat tab
        $('#tab-chat').trigger('click');

        // Pre-fill the message input with a sensible follow-up
        const query = 'Tell me more about how to treat ' + lastDisease;
        $('#messageText').val(query).focus();
    });

    // ── Handle a picked/dropped file ──────────────────────────
    function handleFile(file) {
        const allowed = ['image/jpeg', 'image/png', 'image/webp'];

        if (!allowed.includes(file.type)) {
            showError('Invalid file type. Please upload a JPG, PNG, or WEBP image.');
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            showError('File too large. Maximum allowed size is 5 MB.');
            return;
        }

        selectedFile = file;

        const reader = new FileReader();
        reader.onload = function (e) {
            $previewImg.attr('src', e.target.result);
            $previewName.text(file.name);
            $placeholder.hide();
            $preview.show();
            $analyseBtn.prop('disabled', false);
            $resultWrap.hide();           // hide previous result when new image picked
        };
        reader.readAsDataURL(file);
    }

    // ── Call POST /image/predict ───────────────────────────────
    function runPrediction(file) {
        showLoading();

        const formData = new FormData();
        formData.append('image', file);   // matches request.files["image"] in controller
        formData.append('lang', $('#langSelect').val() || 'en');
        formData.append('conv_id', (typeof currentConvId !== 'undefined' ? currentConvId : '') || '');

        $.ajax({
            type: 'POST',
            url: '/image/predict',
            data: formData,
            processData: false,           // do NOT let jQuery serialize FormData
            contentType: false,           // let browser set multipart boundary
            success: function (response) {
                if (response.success) {
                    showSuccess(response);
                    // Refresh sidebar to show detection in history
                    if (response.conv_id && typeof loadSidebar === 'function') {
                        if (typeof currentConvId !== 'undefined') currentConvId = response.conv_id;
                        loadSidebar();
                    }
                } else {
                    showError(response.error || 'Prediction failed. Please try again.');
                }
            },
            error: function (xhr) {
                let msg = 'Network error. Please check your connection.';
                try {
                    const body = JSON.parse(xhr.responseText);
                    if (body.error) msg = body.error;
                } catch (e) { /* ignore */ }
                showError(msg);
            }
        });
    }

    // ── UI state helpers ───────────────────────────────────────

    function showLoading() {
        $analyseBtn.prop('disabled', true);
        $resultWrap.show();
        $loading.show();
        $success.hide();
        $errorDiv.hide();
    }

    function showSuccess(data) {
        $loading.hide();
        $errorDiv.hide();
        $success.show();

        // Store disease name for follow-up button
        lastDisease = data.disease || '';

        // Disease name
        $diseaseName.text(data.disease || 'Unknown');

        // Confidence badge
        const conf   = parseFloat(data.confidence) || 0;
        const isLow  = !data.reliable;
        $confBadge
            .text(conf.toFixed(1) + '%')
            .toggleClass('low', isLow);

        // Warning box
        if (data.warning) {
            $warnText.text(data.warning);
            $warnBox.show();
        } else {
            $warnBox.hide();
        }

        // RAG answer (typewriter effect matching chat.js style)
        $ragBody.text('');
        typewriterText(data.rag_answer || 'No treatment information available.', $ragBody);

        $analyseBtn.prop('disabled', false);
    }

    function showError(message) {
        $loading.hide();
        $success.hide();
        $errorMsg.text(message);
        $errorDiv.show();
        $resultWrap.show();
        $analyseBtn.prop('disabled', false);
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

    // ── Typewriter effect (mirrors chat.js behaviour) ──────────
    function typewriterText(text, $el, speed) {
        speed = speed || 10;
        let i = 0;
        $el.text('');

        const iv = setInterval(function () {
            if (i < text.length) {
                $el.text($el.text() + text.charAt(i));
                i++;
                // scroll detect panel to bottom while typing
                const scroll = $('.detect-scroll')[0];
                if (scroll) scroll.scrollTop = scroll.scrollHeight;
            } else {
                clearInterval(iv);
                $el.text(text);   // final clean render
            }
        }, speed);
    }

});