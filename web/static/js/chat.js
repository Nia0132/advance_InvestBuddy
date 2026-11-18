let sessionId = localStorage.getItem("investbuddy_session_id");
if (!sessionId) {
    sessionId = "sess_" + Math.random().toString(36).substring(2, 11) + "_" + Date.now();
    localStorage.setItem("investbuddy_session_id", sessionId);
}

document.addEventListener("DOMContentLoaded", () => {
    fetchStatus();
});

async function fetchStatus() {
    try {
        const res = await fetch("/api/status");
        if (res.ok) {
            const data = await res.json();
            const el = document.getElementById("lastUpdateText");
            if (el && data.last_update) {
                el.innerText = `Update: ${data.last_update}`;
            }
        }
    } catch (e) {
        console.warn("Gagal mengambil status metadata:", e);
    }
}

function handleChatSubmit(event) {
    event.preventDefault();
    const input = document.getElementById("userInput");
    const text = input.value.trim();
    if (!text) return;

    input.value = "";
    sendMessage(text);
}

function sendQuickMessage(text) {
    sendMessage(text);
}

async function sendMessage(text) {
    appendUserMessage(text);
    const loadingId = showLoadingIndicator();

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: sessionId,
                message: text
            })
        });

        removeLoadingIndicator(loadingId);

        if (response.ok) {
            const result = await response.json();
            appendBotMessage(result.response, result.quick_replies);
        } else {
            appendBotMessage("⚠️ Maaf, terjadi kendala komunikasi dengan server. Silakan coba kembali.");
        }
    } catch (err) {
        removeLoadingIndicator(loadingId);
        appendBotMessage("⚠️ Gagal terhubung ke backend server InvestBuddy.");
    }
}

function appendUserMessage(text) {
    const container = document.getElementById("messagesContainer");
    const msgDiv = document.createElement("div");
    msgDiv.className = "message user-message";
    msgDiv.innerHTML = `
        <div class="avatar">👤</div>
        <div class="message-content">
            <div class="text-content">
                <p>${escapeHtml(text)}</p>
            </div>
        </div>
    `;
    container.appendChild(msgDiv);
    scrollToBottom();
}

function appendBotMessage(markdownText, quickReplies = []) {
    const container = document.getElementById("messagesContainer");
    const msgDiv = document.createElement("div");
    msgDiv.className = "message bot-message";

    const renderedHtml = marked.parse(markdownText || "");

    let pillsHtml = "";
    if (quickReplies && quickReplies.length > 0) {
        pillsHtml = '<div class="pill-group">' +
            quickReplies.map(p => `<button class="pill" onclick="sendQuickMessage('${escapeHtml(p)}')">${escapeHtml(p)}</button>`).join("") +
            '</div>';
    }

    msgDiv.innerHTML = `
        <div class="avatar">🤖</div>
        <div class="message-content">
            <div class="text-content">
                ${renderedHtml}
            </div>
            ${pillsHtml}
        </div>
    `;
    container.appendChild(msgDiv);
    scrollToBottom();
}

function showLoadingIndicator() {
    const container = document.getElementById("messagesContainer");
    const id = "loading_" + Date.now();
    const loadingDiv = document.createElement("div");
    loadingDiv.className = "message bot-message";
    loadingDiv.id = id;
    loadingDiv.innerHTML = `
        <div class="avatar">🤖</div>
        <div class="message-content">
            <div class="loading-dots">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    container.appendChild(loadingDiv);
    scrollToBottom();
    return id;
}

function removeLoadingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function scrollToBottom() {
    const container = document.getElementById("messagesContainer");
    container.scrollTop = container.scrollHeight;
}

async function resetSession() {
    if (confirm("Mulai sesi baru dan reset riwayat kalkulator aktif?")) {
        try {
            await fetch(`/api/reset?session_id=${sessionId}`, { method: "POST" });
        } catch (e) {}
        sessionId = "sess_" + Math.random().toString(36).substring(2, 11) + "_" + Date.now();
        localStorage.setItem("investbuddy_session_id", sessionId);
        location.reload();
    }
}

function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
}
