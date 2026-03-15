/**

 * static/js/chat.js — Chat Interface Logic

 * Includes: messaging, markdown, voice, multilingual, chat history sidebar

 */



$(function () {



    // ── Speech synthesis ───────────────────────────────────────

    const synth = window.speechSynthesis;

    const msg   = new SpeechSynthesisUtterance();

    msg.rate = 1; msg.pitch = 1; msg.voice = null;



    // ── State ──────────────────────────────────────────────────

    let isProcessing  = false;

    let currentConvId = null;



    // ── Welcome message ────────────────────────────────────────

    const WELCOME_MSG =

        "🌱🌾 Welcome to AgriBot! I'm your AI assistant for Indian farming and agriculture.\n\n" +

        "You can ask me about:\n" +

        "- Crop diseases and remedies\n" +

        "- Fertilizer recommendations\n" +

        "- Pest control methods\n" +

        "- Government schemes for farmers\n" +

        "- Weather-based farming tips\n\n" +

        "How can I help you today?";



    setTimeout(function () { appendBotMessage(WELCOME_MSG); }, 500);

    loadSidebar();



    // ── Event bindings ─────────────────────────────────────────

    $("#btn-send").on("click", function (e) { e.preventDefault(); sendMessage(); });

    $("#messageText").on("keypress", function (e) {

        if (e.which === 13) { e.preventDefault(); sendMessage(); }

    });

    $("#btn-clear").on("click", function (e) {

        e.preventDefault();

        $(".chat-messages").empty();

        appendBotMessage(WELCOME_MSG);

    });

    $("#btn-voice").on("click", handleVoiceInput);

    $("#voiceReadingCheckbox").on("change", function () {

        if (!$(this).is(":checked")) synth.cancel();

    });

    $("#btn-new-chat").on("click", function () {

        currentConvId = null;

        $(".chat-messages").empty();

        appendBotMessage(WELCOME_MSG);

        $(".history-item").removeClass("active");

    });



    // ── Send message ───────────────────────────────────────────

    function sendMessage() {

        const message = $("#messageText").val().trim();

        if (!message || isProcessing) return;



        isProcessing = true;

        disableInput();

        appendUserMessage(message);

        $("#messageText").val("");

        showTypingIndicator();



        $.ajax({

            type: "POST",

            url:  "/ask",

            timeout: 300000, // 5 minutes timeout for first request

            data: {

                messageText: message,

                lang:        $("#langSelect").val() || "en",

                conv_id:     currentConvId || ""

            },

            success: function (response) {

                removeTypingIndicator();

                const answer = response.error ? "Error: " + response.error : response.answer;

                appendBotMessage(answer);

                if (response.conv_id) {

                    currentConvId = response.conv_id;

                    loadSidebar();

                }

                if ($("#voiceReadingCheckbox").is(":checked")) speakResponse(answer);

                isProcessing = false;

                enableInput();

            },

            error: function (xhr, status, error) {

                removeTypingIndicator();

                if (status === "timeout") {

                    appendBotMessage("⏳ Initializing AgriBot... This takes 2-5 minutes on first use. Please wait and try again.");

                } else if (status === "error" && xhr.status === 0) {

                    appendBotMessage("🔄 Connection lost. AgriBot is still initializing. Please wait 2-5 minutes and try again.");

                } else {

                    appendBotMessage("Sorry, something went wrong. Please try again.");

                }

                isProcessing = false;

                enableInput();

            }

        });

    }



    // ── Message renderers ──────────────────────────────────────

    function appendUserMessage(text) {

        const el = $(

            '<div class="message-container user-container">' +

            '<span class="timestamp">' + getTime() + '</span>' +

            '<div class="message user-message"></div>' +

            '<div class="avatar"><img src="/static/images/user.png" alt="You" onerror="this.parentElement.innerHTML=\'👤\'"></div>' +

            '</div>'

        );

        el.find(".user-message").text(text);

        $(".chat-messages").append(el);

        scrollToBottom();

    }



    function appendBotMessage(text) {

        const el = $(

            '<div class="message-container bot-container">' +

            '<div class="avatar"><img src="/static/images/robo.png" alt="AgriBot" onerror="this.parentElement.innerHTML=\'🌾\'"></div>' +

            '<div class="message bot-message"></div>' +

            '<span class="timestamp">' + getTime() + '</span>' +

            '</div>'

        );

        $(".chat-messages").append(el);

        typewriterRender(text, el.find(".bot-message"));

    }



    // Instant renderers for loading history (no typewriter)

    function appendUserMessageInstant(text) {

        const el = $(

            '<div class="message-container user-container">' +

            '<div class="message user-message"></div>' +

            '<div class="avatar"><img src="/static/images/user.png" alt="You" onerror="this.parentElement.innerHTML=\'👤\'"></div>' +

            '</div>'

        );

        el.find(".user-message").text(text);

        $(".chat-messages").append(el);

    }



    function appendBotMessageInstant(text) {

        const el = $(

            '<div class="message-container bot-container">' +

            '<div class="avatar"><img src="/static/images/robo.png" alt="AgriBot" onerror="this.parentElement.innerHTML=\'🌾\'"></div>' +

            '<div class="message bot-message"></div>' +

            '</div>'

        );

        el.find(".bot-message").html(renderMarkdown(text));

        $(".chat-messages").append(el);

    }



    function typewriterRender(text, element, speed) {

        speed = speed || 12;

        let i = 0;

        element.html("");

        const interval = setInterval(function () {

            if (i < text.length) {

                i++;

                element.html(renderMarkdown(text.substring(0, i)));

                scrollToBottom();

            } else {

                clearInterval(interval);

                element.html(renderMarkdown(text));

            }

        }, speed);

    }



    function renderMarkdown(text) {

        text = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

        text = text.replace(/\*(.*?)\*/g, "<em>$1</em>");

        const lines = text.split("\n");

        let html = "", inUl = false, inOl = false;

        lines.forEach(function (line) {

            const t = line.trim();

            if (!t) {

                if (inUl) { html += "</ul>"; inUl = false; }

                if (inOl) { html += "</ol>"; inOl = false; }

                return;

            }

            if (/^[-•]\s/.test(t)) {

                if (inOl) { html += "</ol>"; inOl = false; }

                if (!inUl) { html += "<ul>"; inUl = true; }

                html += "<li>" + t.replace(/^[-•]\s/, "") + "</li>";

            } else if (/^\d+\.\s/.test(t)) {

                if (inUl) { html += "</ul>"; inUl = false; }

                if (!inOl) { html += "<ol>"; inOl = true; }

                html += "<li>" + t.replace(/^\d+\.\s/, "") + "</li>";

            } else {

                if (inUl) { html += "</ul>"; inUl = false; }

                if (inOl) { html += "</ol>"; inOl = false; }

                html += "<p>" + t + "</p>";

            }

        });

        if (inUl) html += "</ul>";

        if (inOl) html += "</ol>";

        return html;

    }



    // ── Typing indicator ───────────────────────────────────────

    function showTypingIndicator() {

        const el = $(

            '<div class="message-container bot-container" id="typing-row">' +

            '<div class="avatar"><img src="/static/images/robo.png" alt="Bot" onerror="this.parentElement.innerHTML=\'🌾\'"></div>' +

            '<div class="typing-indicator"><span></span><span></span><span></span></div>' +

            '</div>'

        );

        $(".chat-messages").append(el);

        scrollToBottom();

    }

    function removeTypingIndicator() { $("#typing-row").remove(); }



    // ── Voice output ───────────────────────────────────────────

    function speakResponse(text) {

        if (!("speechSynthesis" in window)) return;

        synth.cancel();

        const clean = text.replace(/\*\*(.*?)\*\*/g, "$1").replace(/\*(.*?)\*/g, "$1")

                          .replace(/[-•]\s/g, "").replace(/\d+\.\s/g, "").replace(/\n+/g, " ");

        msg.text = clean; msg.rate = 0.9; msg.pitch = 1; msg.volume = 1;

        const v = synth.getVoices().find(function (x) {

            return x.name.includes("Female") || x.name.includes("Samantha") ||

                   x.name.includes("Karen")  || x.lang.includes("en-IN") || x.lang.includes("en-GB");

        });

        if (v) msg.voice = v;

        synth.speak(msg);

    }

    if (synth.onvoiceschanged !== undefined) {

        synth.onvoiceschanged = function () { console.log("Voices:", synth.getVoices().length); };

    }



    // ── Voice input ────────────────────────────────────────────

    function handleVoiceInput(e) {

        e.preventDefault();

        if (!("webkitSpeechRecognition" in window) || isProcessing) return;

        const btn = $("#btn-voice");

        const rec = new webkitSpeechRecognition();

        const langMap = { "en":"en-IN","hi":"hi-IN","te":"te-IN","ta":"ta-IN",

                          "kn":"kn-IN","ml":"ml-IN","mr":"mr-IN","bn":"bn-IN","gu":"gu-IN","pa":"pa-IN" };

        rec.lang = langMap[$("#langSelect").val() || "en"] || "en-IN";

        rec.interimResults = false; rec.maxAlternatives = 1;

        btn.addClass("listening");

        rec.onresult = function (event) {

            btn.removeClass("listening");

            $("#messageText").val(event.results[0][0].transcript);

            sendMessage();

        };

        rec.onerror = function (event) {

            btn.removeClass("listening");

            alert("Voice input error: " + event.error);

        };

        rec.onend = function () { btn.removeClass("listening"); };

        rec.start();

    }



    // ══════════════════════════════════════════════════════════

    //  CHAT HISTORY SIDEBAR

    // ══════════════════════════════════════════════════════════



    function loadSidebar() {

        $.get("/history/conversations", function (data) {

            var $list = $("#historyList").empty();



            if (!data.conversations || data.conversations.length === 0) {

                $list.html(

                    '<div class="no-history">' +

                    '<i class="fas fa-seedling"></i>' +

                    '<p>No conversations yet.<br>Start chatting to see history!</p>' +

                    '</div>'

                );

                return;

            }



            // Group conversations by date

            var groups = {}, order = [];

            data.conversations.forEach(function (conv) {

                var grp = getDateGroup(conv.updated_at);

                if (!groups[grp]) { groups[grp] = []; order.push(grp); }

                groups[grp].push(conv);

            });



            order.forEach(function (grp) {

                $list.append('<div class="history-group-label">' + grp + '</div>');

                groups[grp].forEach(function (conv) {

                    var isActive    = conv.id === currentConvId ? " active" : "";

                    var isDetection = conv.title.indexOf("Disease scan:") === 0;

                    var icon        = isDetection ? "fas fa-leaf" : "fas fa-comment-alt";

                    var iconClass   = isDetection ? "history-item-icon detect-icon" : "history-item-icon";

                    var timeStr     = conv.updated_at ? conv.updated_at.substring(11, 16) : "";



                    var $item = $(

                        '<div class="history-item' + isActive + '" data-id="' + conv.id + '">' +

                        '<div class="' + iconClass + '"><i class="' + icon + '"></i></div>' +

                        '<div class="history-item-text">' +

                        '<span class="history-title">' + escapeHtml(conv.title) + '</span>' +

                        '<span class="history-date">' + timeStr + '</span>' +

                        '</div>' +

                        '<button class="history-delete" data-id="' + conv.id + '" title="Delete">' +

                        '<i class="fas fa-trash-alt"></i>' +

                        '</button>' +

                        '</div>'

                    );

                    $list.append($item);

                });

            });

        }).fail(function () {

            console.warn("Could not load chat history.");

        });

    }



    // Click a conversation → load its messages

    $(document).on("click", ".history-item", function (e) {

        if ($(e.target).closest(".history-delete").length) return;

        var convId = $(this).data("id");

        if (convId === currentConvId) return;



        currentConvId = convId;

        $(".history-item").removeClass("active");

        $(this).addClass("active");



        // Show spinner while loading

        $(".chat-messages").html(

            '<div class="history-loading">' +

            '<div class="result-spinner"></div><p>Loading conversation…</p>' +

            '</div>'

        );



        $.get("/history/messages/" + convId, function (data) {

            $(".chat-messages").empty();

            if (!data.messages || data.messages.length === 0) {

                appendBotMessage("This conversation has no messages.");

                return;

            }

            data.messages.forEach(function (m) {

                if (m.role === "user") appendUserMessageInstant(m.content);

                else                   appendBotMessageInstant(m.content);

            });

            

            // Also load disease detection results for this conversation

            $.get("/history/detections/" + convId, function (detectionData) {

                if (detectionData.detections && detectionData.detections.length > 0) {

                    detectionData.detections.forEach(function (detection) {

                        // Display disease detection result

                        var detectionHtml = 

                            '<div class="message bot-message">' +

                            '<div class="message-avatar">🔬</div>' +

                            '<div class="message-content">' +

                            '<div class="detection-result">' +

                            '<div class="detection-header">' +

                            '<strong>Plant Disease Detection</strong><br>' +

                            '<span class="disease-name">' + detection.display_name + '</span><br>' +

                            '<small>Confidence: ' + detection.confidence + '% | ' +

                            (detection.reliable ? 'Reliable' : 'Low Confidence') + '</small>' +

                            '</div>' +

                            '<div class="detection-advice">' +

                            '<strong>Treatment & Advice:</strong><br>' +

                            detection.rag_answer +

                            '</div>' +

                            '</div>' +

                            '</div>' +

                            '<div class="message-time">' + new Date(detection.created_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }) + '</div>' +

                            '</div>';

                        $(".chat-messages").append(detectionHtml);

                    });

                    scrollToBottom();

                }

            }).fail(function () {

                console.warn("Could not load disease detection results.");

            });

            

            // Also load QR scan results for this conversation

            $.get("/history/qr_scans/" + convId, function (qrData) {

                if (qrData.qr_scans && qrData.qr_scans.length > 0) {

                    qrData.qr_scans.forEach(function (qrScan) {

                        // Display QR scan result

                        var qrHtml = 

                            '<div class="message bot-message">' +

                            '<div class="message-avatar">📱</div>' +

                            '<div class="message-content">' +

                            '<div class="qr-result">' +

                            '<div class="qr-header">' +

                            '<strong>QR Code Scan</strong><br>' +

                            '<span class="qr-data">Data: ' + (qrScan.qr_data.length > 50 ? qrScan.qr_data.substring(0, 50) + "..." : qrScan.qr_data) + '</span><br>' +

                            '<small>Confidence: ' + Math.round(qrScan.confidence * 100) + '% | Format: ' + qrScan.format + '</small>' +

                            '</div>' +

                            '<div class="qr-analysis">' +

                            '<strong>AI Analysis:</strong><br>' +

                            qrScan.chat_response +

                            '</div>' +

                            '</div>' +

                            '</div>' +

                            '<div class="message-time">' + new Date(qrScan.created_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }) + '</div>' +

                            '</div>';

                        $(".chat-messages").append(qrHtml);

                    });

                    scrollToBottom();

                }

            }).fail(function () {

                console.warn("Could not load QR scan results.");

            });

            

            scrollToBottom();

        }).fail(function () {

            $(".chat-messages").empty();

            appendBotMessage("Could not load conversation. Please try again.");

        });

    });



    // Delete conversation

    $(document).on("click", ".history-delete", function (e) {

        e.stopPropagation();

        var convId = $(this).data("id");

        if (!confirm("Delete this conversation?")) return;

        $.ajax({

            type: "DELETE",

            url:  "/history/delete/" + convId,

            success: function () {

                if (currentConvId === convId) {

                    currentConvId = null;

                    $(".chat-messages").empty();

                    appendBotMessage(WELCOME_MSG);

                }

                loadSidebar();

            },

            error: function () { alert("Could not delete."); }

        });

    });



    // ── Date grouping ──────────────────────────────────────────

    function getDateGroup(isoString) {

        if (!isoString) return "Older";

        var d    = new Date(isoString);

        var now  = new Date();

        var diff = Math.floor((now - d) / 86400000);

        if (diff === 0) return "Today";

        if (diff === 1) return "Yesterday";

        if (diff < 7)   return "This Week";

        if (diff < 30)  return "This Month";

        return "Older";

    }



    function escapeHtml(text) { return $("<span>").text(text).html(); }



    // ── Core helpers ───────────────────────────────────────────

    function disableInput() { $("#messageText, #btn-send, #btn-voice").prop("disabled", true); }

    function enableInput()  {

        $("#messageText, #btn-send, #btn-voice").prop("disabled", false);

        $("#messageText").focus();

    }

    function scrollToBottom() {

        var el = $(".chat-messages")[0];

        if (el) el.scrollTop = el.scrollHeight;

    }

    function getTime() {

        return new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });

    }



});