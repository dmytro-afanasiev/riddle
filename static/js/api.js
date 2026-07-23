const API = "/api/v1";

function getToken() {
    return localStorage.getItem("token");
}

function setToken(token, expiresAt) {
    localStorage.setItem("token", token);
    localStorage.setItem("token_expires_at", expiresAt);
}

function clearToken() {
    localStorage.removeItem("token");
    localStorage.removeItem("token_expires_at");
}

function isLoggedIn() {
    const token = getToken();
    if (!token) return false;
    const exp = localStorage.getItem("token_expires_at");
    if (exp && new Date(exp) < new Date()) {
        clearToken();
        return false;
    }
    return true;
}

function requireAuth() {
    if (!isLoggedIn()) {
        window.location.href = "/login.html";
    }
}

function requireGuest() {
    if (isLoggedIn()) {
        window.location.href = "/dashboard.html";
    }
}

// --- toast notifications ---

function ensureToastContainer() {
    let c = document.getElementById("toast-container");
    if (!c) {
        c = document.createElement("div");
        c.id = "toast-container";
        document.body.appendChild(c);
    }
    return c;
}

function toast(msg, type) {
    const container = ensureToastContainer();
    const el = document.createElement("div");
    el.className = "toast toast--" + type;
    el.textContent = msg;
    container.appendChild(el);
    setTimeout(function () {
        el.remove();
    }, 4000);
}

function toastError(msg) { toast(msg, "error"); }
function toastSuccess(msg) { toast(msg, "success"); }

// --- api helpers ---

async function api(path, opts) {
    opts = opts || {};
    const headers = {};
    if (opts.body) {
        headers["Content-Type"] = "application/json";
    }
    const token = getToken();
    if (token) {
        headers["Authorization"] = "Bearer " + token;
    }
    const resp = await fetch(API + path, {
        method: opts.method || "GET",
        headers: headers,
        body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
    let data = null;
    const text = await resp.text();
    if (text) {
        try { data = JSON.parse(text); } catch (e) { /* not json */ }
    }
    if (!resp.ok) {
        var msg = (data && data.msg) ? data.msg : "Request failed (" + resp.status + ")";
        var e = new Error(msg);
        e.status = resp.status;
        e.details = (data && data.details) || {};
        throw e;
    }
    return data;
}

async function register(username, password) {
    await api("/auth/register", {
        method: "POST",
        body: { username: username, password: password },
    });
}

async function login(username, password) {
    const data = await api("/auth/login", {
        method: "POST",
        body: { username: username, password: password },
    });
    setToken(data.token, data.expires_at);
    return data;
}

async function logout() {
    try {
        await api("/auth/logout", { method: "POST" });
    } finally {
        clearToken();
        clearPrivateCookie();
    }
}

async function whoami() {
    return await api("/auth/whoami");
}

async function getClues(limit, offset, status) {
    var qs = "?limit=" + limit + "&offset=" + offset;
    if (status) qs += "&status=" + status;
    return await api("/clues" + qs);
}

async function getRandomClue() {
    var data = await api("/clues/random");
    return (data && data.msg) ? data.msg : "";
}

async function tryPhrase(phrase) {
    await api("/finale/try", { method: "POST", body: { phrase: phrase } });
}

async function checkFinale() {
    try {
        await api("/finale/check");
        setPrivateCookie();
        return true;
    } catch (e) {
        return false;
    }
}

function setPrivateCookie() {
    var token = getToken();
    if (token) {
        document.cookie = "token=" + token + ";path=/private/;Secure;SameSite=Strict";
    }
}

function clearPrivateCookie() {
    document.cookie = "token=;path=/private/;Secure;SameSite=Strict;max-age=0";
}

async function requestClue(page, level, description) {
    const body = { page: page, level: level };
    if (description) {
        body.description = description;
    }
    try {
        await api("/clues", { method: "POST", body: body });
    } catch (e) {
        if (e.status === 429 && e.details &&
                typeof e.details.seconds_to_wait === "number") {
            var when = new Date(Date.now() + e.details.seconds_to_wait * 1000);
            throw new Error(
                "You've already requested a clue recently. " +
                "Next request available " + when.toLocaleString() + "."
            );
        }
        throw e;
    }
}
