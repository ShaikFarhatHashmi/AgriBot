/**
 * static/js/chat.js — Chat Interface Logic
 *
 * Responsibilities:
 *   - Send messages to /ask via AJAX
 *   - Render bot responses with markdown formatting
 *   - Typing indicator, timestamps
 *   - Voice input (speech-to-text) and voice reading (text-to-speech)
 *   - Voice synthesis debugging and better error handling
 */

$(function () {

    // ── Speech synthesis setup ─────────────────────────────────────────────
    const synth = window.speechSynthesis;
    const msg   = new SpeechSynthesisUtterance();
    msg.rate  = 1;
    msg.pitch = 1;
    msg.voice = null; // Will be set when voices are loaded

    // ── State ──────────────────────────────────────────────────────────────
    let isProcessing = false;

    // ── Welcome message ────────────────────────────────────────────────────
    const WELCOME_MSG =
        "🌱🌾 Welcome to AgriBot! I'm your AI assistant for Indian farming and agriculture.\n\n" +
        "You can ask me about:\n" +
        "- Crop diseases and remedies\n" +
        "- Fertilizer recommendations\n" +
        "- Pest control methods\n" +
        "- Government schemes for farmers\n" +
        "- Weather-based farming tips\n\n" +
        "How can I help you today?";

    setTimeout(() => appendBotMessage(WELCOME_MSG), 500);

    // ── Event listeners ────────────────────────────────────────────────────
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

    // ── Core: send message ─────────────────────────────────────────────────
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
            url: "/ask",
            data: { messageText: message },
            success: function (response) {
                removeTypingIndicator();
                const answer = response.error ? "Error: " + response.error : response.answer;
                appendBotMessage(answer);

                if ($("#voiceReadingCheckbox").is(":checked")) {
                    speakResponse(answer);
                }

                isProcessing = false;
                enableInput();
            },
            error: function () {
                removeTypingIndicator();
                appendBotMessage("Sorry, something went wrong. Please try again.");
                isProcessing = false;
                enableInput();
            }
        });
    }

    // ── Message renderers ──────────────────────────────────────────────────

    function appendUserMessage(text) {
        const time = getTime();
        const el = $(`
            <div class="message-container user-container">
                <span class="timestamp">${time}</span>
                <div class="message user-message"></div>
                <div class="avatar"><img src="/static/images/user.png" alt="You"
                     onerror="this.parentElement.innerHTML='👤'"></div>
            </div>
        `);
        el.find(".user-message").text(text);
        $(".chat-messages").append(el);
        scrollToBottom();
    }

    function appendBotMessage(text) {
        const time = getTime();
        const el = $(`
            <div class="message-container bot-container">
                <div class="avatar"><img src="/static/images/robo.png" alt="AgriBot"
                     onerror="this.parentElement.innerHTML='🌾'"></div>
                <div class="message bot-message"></div>
                <span class="timestamp">${time}</span>
            </div>
        `);
        $(".chat-messages").append(el);
        typewriterRender(text, el.find(".bot-message"));
    }

    /**
     * Typewriter effect that renders markdown as it types.
     * Markdown supported: **bold**, *italic*, - bullet lists, numbered lists
     */
    function typewriterRender(text, element, speed = 12) {
        let i = 0;
        element.html("");

        const interval = setInterval(() => {
            if (i < text.length) {
                i++;
                element.html(renderMarkdown(text.substring(0, i)));
                scrollToBottom();
            } else {
                clearInterval(interval);
                element.html(renderMarkdown(text));   // final clean render
            }
        }, speed);
    }

    /**
     * Convert plain text with markdown to HTML.
     * Handles: **bold**, *italic*, - bullets, numbered lists, newlines.
     */
    function renderMarkdown(text) {
        // Inline: bold and italic
        text = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
        text = text.replace(/\*(.*?)\*/g, "<em>$1</em>");

        const lines  = text.split("\n");
        let html     = "";
        let inUl     = false;
        let inOl     = false;

        lines.forEach(line => {
            const trimmed = line.trim();

            if (!trimmed) {
                if (inUl) { html += "</ul>"; inUl = false; }
                if (inOl) { html += "</ol>"; inOl = false; }
                return;
            }

            // Unordered bullet: "- text" or "• text"
            if (/^[-•]\s/.test(trimmed)) {
                if (inOl) { html += "</ol>"; inOl = false; }
                if (!inUl) { html += "<ul>"; inUl = true; }
                html += `<li>${trimmed.replace(/^[-•]\s/, "")}</li>`;

            // Ordered list: "1. text"
            } else if (/^\d+\.\s/.test(trimmed)) {
                if (inUl) { html += "</ul>"; inUl = false; }
                if (!inOl) { html += "<ol>"; inOl = true; }
                html += `<li>${trimmed.replace(/^\d+\.\s/, "")}</li>`;

            } else {
                if (inUl) { html += "</ul>"; inUl = false; }
                if (inOl) { html += "</ol>"; inOl = false; }
                html += `<p>${trimmed}</p>`;
            }
        });

        if (inUl) html += "</ul>";
        if (inOl) html += "</ol>";
        return html;
    }

    // ── Typing indicator ───────────────────────────────────────────────────
    function showTypingIndicator() {
        const el = $(`
            <div class="message-container bot-container" id="typing-row">
                <div class="avatar"><img src="/static/images/robo.png" alt="Bot"
                     onerror="this.parentElement.innerHTML='🌾'"></div>
                <div class="typing-indicator"><span></span><span></span><span></span></div>
            </div>
        `);
        $(".chat-messages").append(el);
        scrollToBottom();
    }

    function removeTypingIndicator() { $("#typing-row").remove(); }

    // ── Voice output ────────────────────────────────────────────────────────
    function speakResponse(text) {
        if (!('speechSynthesis' in window)) {
            console.log("Speech synthesis not supported");
            return;
        }

        // Cancel any ongoing speech
        synth.cancel();

        // Clean up text (remove markdown)
        const cleanText = text.replace(/\*\*(.*?)\*\*/g, '$1')
                              .replace(/\*(.*?)\*/g, '$1')
                              .replace(/[-•]\s/g, '')
                              .replace(/\d+\.\s/g, '')
                              .replace(/\n+/g, ' ');

        msg.text = cleanText;
        msg.rate = 0.9; // Slightly slower for better comprehension
        msg.pitch = 1;
        msg.volume = 1;

        // Try to set a female voice (often preferred for assistants)
        const voices = synth.getVoices();
        const femaleVoice = voices.find(voice => 
            voice.name.includes('Female') || 
            voice.name.includes('Samantha') ||
            voice.name.includes('Karen') ||
            voice.lang.includes('en-IN') ||
            voice.lang.includes('en-GB')
        );
        
        if (femaleVoice) {
            msg.voice = femaleVoice;
        }

        synth.speak(msg);
    }

    // Load voices when they're ready
    function loadVoices() {
        if (synth.getVoices().length > 0) {
            console.log("Voices loaded:", synth.getVoices().length);
        }
    }

    // Voices load asynchronously, so we need to handle both cases
    if (synth.onvoiceschanged !== undefined) {
        synth.onvoiceschanged = loadVoices;
    } else {
        // Fallback for older browsers
        setTimeout(loadVoices, 100);
    }

    // ── Voice input ────────────────────────────────────────────────────────
    function handleVoiceInput(e) {
        e.preventDefault();
        if (!("webkitSpeechRecognition" in window) || isProcessing) return;

        const btn         = $("#btn-voice");
        const recognition = new webkitSpeechRecognition();
        recognition.lang            = "en-IN";
        recognition.interimResults  = false;
        recognition.maxAlternatives = 1;

        btn.addClass("listening");

        recognition.onresult = function (event) {
            btn.removeClass("listening");
            const speech = event.results[0][0].transcript;
            $("#messageText").val(speech);
            console.log("Voice input: " + speech);
            sendMessage();
        };

        recognition.onerror = function (event) {
            btn.removeClass("listening");
            console.error("Speech recognition error:", event.error);
            alert("Voice input error: " + event.error);
        };

        recognition.onend = function () { btn.removeClass("listening"); };

        recognition.start();
    }

    // ── Helpers ────────────────────────────────────────────────────────────
    function disableInput() {
        $("#messageText, #btn-send, #btn-voice").prop("disabled", true);
    }

    function enableInput() {
        $("#messageText, #btn-send, #btn-voice").prop("disabled", false);
        $("#messageText").focus();
    }

    function scrollToBottom() {
        const el = $(".chat-messages")[0];
        if (el) el.scrollTop = el.scrollHeight;
    }

    function getTime() {
        return new Date().toLocaleTimeString("en-IN", {
            hour: "2-digit", minute: "2-digit"
        });
    }
});