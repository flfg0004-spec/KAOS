// ─── WhatsApp Baileys Bridge — KAOS ──────────────────────────────────
// Stub de integración WhatsApp vía @whiskeysockets/baileys
// Modo: Multi-Device (QR code scan)
// ──────────────────────────────────────────────────────────────────────
// Uso:
//   1. Asegúrate de WHATSAPP_ENABLED=true en ~/.hermes/.env
//   2. Ejecuta: node baileys_bridge.js
//   3. Escanea el código QR con WhatsApp en tu teléfono
//   4. Los mensajes entrantes se loggean en la consola
// ──────────────────────────────────────────────────────────────────────

const { makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const fs = require('fs');
const path = require('path');

// ─── Config ──────────────────────────────────────────────────────────
const AUTH_DIR = path.join(__dirname, 'auth_info_baileys');
const LOG_FILE = path.join(__dirname, 'baileys_bridge.log');
const RECONNECT_DELAY_MS = 5000;

// ─── Scribe ──────────────────────────────────────────────────────────
function log(level, msg, data) {
    const line = `[${new Date().toISOString()}] [${level}] ${msg}${data ? ' ' + JSON.stringify(data) : ''}`;
    console.log(line);
    fs.appendFileSync(LOG_FILE, line + '\n');
}

// ─── Connection ──────────────────────────────────────────────────────
async function connectToWhatsApp() {
    log('INFO', 'Starting Baileys WhatsApp bridge...');

    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

    const sock = makeWASocket({
        auth: state,
        printQRInTerminal: true,
        browser: ['KAOS Bridge', 'Chrome', '1.0.0'],
        syncFullHistory: false,
        markOnlineOnConnect: false,
    });

    // ─── Connection State ────────────────────────────────────────────
    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            log('INFO', 'QR code received — scan with your phone');
        }

        if (connection === 'close') {
            const shouldReconnect =
                (lastDisconnect?.error instanceof Boom)
                    ? lastDisconnect.error.output?.statusCode !== DisconnectReason.loggedOut
                    : true;

            if (shouldReconnect) {
                log('WARN', `Connection closed (${lastDisconnect?.error?.message || 'unknown'}), reconnecting in ${RECONNECT_DELAY_MS}ms...`);
                setTimeout(connectToWhatsApp, RECONNECT_DELAY_MS);
            } else {
                log('ERROR', 'Logged out — manual re-authentication required');
                process.exit(1);
            }
        }

        if (connection === 'open') {
            log('INFO', 'WhatsApp connection opened successfully');
            log('INFO', `Logged in as: ${sock.user?.id || 'unknown'}`);
        }
    });

    // ─── Credential Persistence ──────────────────────────────────────
    sock.ev.on('creds.update', saveCreds);

    // ─── Message Handler ─────────────────────────────────────────────
    sock.ev.on('messages.upsert', async ({ messages, type }) => {
        for (const msg of messages) {
            try {
                // Ignore own messages
                if (msg.key?.fromMe) continue;
                if (!msg.message) continue;

                const sender = msg.key?.remoteJid || 'unknown';
                const text = msg.message?.conversation
                    || msg.message?.extendedTextMessage?.text
                    || '[non-text message]';

                log('MSG', `From: ${sender}`, { text });

                // ─── Auto-reply placeholder ──────────────────────────
                // Descomentar para eco automático:
                // await sock.sendMessage(sender, { text: `Echo: ${text}` });
            } catch (err) {
                log('ERROR', 'Error processing message', { error: err.message });
            }
        }
    });

    // ─── Presence ────────────────────────────────────────────────────
    sock.ev.on('presence.update', ({ id, presences }) => {
        // Opcional: trackear presencia de contactos
    });

    return sock;
}

// ─── Send API ────────────────────────────────────────────────────────
// Exportable para integración con otros módulos de KAOS
async function sendMessage(sock, jid, text) {
    if (!sock) throw new Error('Socket not connected');
    const result = await sock.sendMessage(jid, { text });
    log('SEND', `Sent to ${jid}: ${text.substring(0, 80)}`);
    return result;
}

// ─── Main ────────────────────────────────────────────────────────────
if (require.main === module) {
    log('INFO', 'Baileys Bridge starting in standalone mode');
    connectToWhatsApp().catch((err) => {
        log('FATAL', 'Bridge crashed', { error: err.message });
        process.exit(1);
    });
}

module.exports = { connectToWhatsApp, sendMessage };
