"""
Servidor web — Traductor LSA bidireccional
--------------------------------------------
Sección 1: Muestra las señas detectadas en tiempo real
Sección 2: Respuesta en imágenes LSA (persona oyente escribe y se muestra en señas)

Deploy en Render.
"""

from flask import Flask, jsonify, request, Response
from datetime import datetime

app = Flask(__name__)

estado = {
    "texto_actual": "",
    "letra_actual": "",
    "confianza": 0.0,
    "finalizado": False,
    "historial": [],
    "respuesta_imagenes": "",
}

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RAPIRO LSA - Comunicación bidireccional</title>
<style>
  :root {
    --bg: #eef7f7;
    --surface: rgba(255, 255, 255, 0.9);
    --surface-strong: #ffffff;
    --text: #17324d;
    --muted: #60758a;
    --primary: #0f766e;
    --primary-strong: #0b5f59;
    --accent: #6d5dfc;
    --accent-soft: #ebe9ff;
    --success: #16a34a;
    --warning: #f59e0b;
    --danger: #dc2626;
    --border: #d8e8ea;
    --shadow: 0 18px 50px rgba(15, 118, 110, 0.13);
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: Inter, 'Segoe UI', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    min-height: 100vh;
    color: var(--text);
    background:
      radial-gradient(circle at top left, rgba(45, 212, 191, 0.24), transparent 34rem),
      linear-gradient(135deg, #f7fbff 0%, #eaf7f4 48%, #f7f3ff 100%);
    padding: 28px 18px 44px;
  }
  .container { max-width: 1120px; margin: 0 auto; }
  .hero {
    text-align: center;
    padding: 34px 24px 22px;
  }
  .eyebrow {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 8px 14px; border-radius: 999px;
    background: rgba(15, 118, 110, 0.10); color: var(--primary-strong);
    font-weight: 800; font-size: 0.78rem; letter-spacing: .08em; text-transform: uppercase;
    margin-bottom: 16px;
  }
  h1 { font-size: clamp(2.4rem, 7vw, 4.6rem); line-height: .95; letter-spacing: -0.06em; }
  .subtitle { max-width: 760px; margin: 18px auto 0; color: var(--muted); font-size: clamp(1rem, 2.4vw, 1.25rem); line-height: 1.55; }
  .mode-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; margin: 18px 0 28px; }
  .mode-card {
    width: 100%; border: 1px solid var(--border); border-radius: 26px; padding: 24px;
    background: var(--surface); box-shadow: var(--shadow); text-align: left; color: inherit;
    cursor: pointer; transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
  }
  .mode-card:hover, .mode-card.active { transform: translateY(-3px); border-color: rgba(15, 118, 110, .42); box-shadow: 0 22px 60px rgba(15, 118, 110, .18); }
  .mode-card.active { outline: 3px solid rgba(15, 118, 110, .12); background: #fbffff; }
  .mode-icon { width: 52px; height: 52px; display: grid; place-items: center; border-radius: 18px; font-size: 1.8rem; background: var(--accent-soft); margin-bottom: 16px; }
  .mode-card:first-child .mode-icon { background: #dff8f3; }
  .mode-card h2 { font-size: clamp(1.35rem, 3vw, 1.8rem); margin-bottom: 10px; }
  .mode-card p { color: var(--muted); line-height: 1.55; font-size: 1rem; }
  .panel { display: none; background: var(--surface); border: 1px solid var(--border); border-radius: 30px; box-shadow: var(--shadow); padding: clamp(18px, 3vw, 30px); }
  .panel.active { display: block; }
  .section-header { display: flex; justify-content: space-between; gap: 18px; align-items: flex-start; margin-bottom: 22px; }
  .section-header h2 { font-size: clamp(1.45rem, 3vw, 2.1rem); margin-bottom: 8px; }
  .section-header p, .help-text { color: var(--muted); line-height: 1.55; }

  .detection-layout { display: grid; grid-template-columns: minmax(260px, .9fr) minmax(300px, 1.1fr); gap: 20px; align-items: stretch; }
  .camera-zone {
    border: 2px dashed #a8d8d2; border-radius: 26px; min-height: 350px; padding: 20px;
    background: linear-gradient(160deg, #063b42 0%, #0f766e 100%); color: white;
    display: flex; flex-direction: column; justify-content: space-between; overflow: hidden; position: relative;
  }
  .camera-zone::before { content: ''; position: absolute; inset: 18px; border: 1px solid rgba(255,255,255,.22); border-radius: 22px; pointer-events: none; }
  .camera-label { position: relative; z-index: 1; display: flex; justify-content: space-between; gap: 10px; font-weight: 800; }
  .camera-visual { position: relative; z-index: 1; display: grid; place-items: center; gap: 8px; text-align: center; color: rgba(255,255,255,.83); }
  .camera-visual .hand { font-size: 4.4rem; filter: drop-shadow(0 16px 20px rgba(0,0,0,.22)); }
  .result-card, .message-card, .history-card, .reply-card { background: var(--surface-strong); border: 1px solid var(--border); border-radius: 24px; padding: 22px; }
  .result-card { text-align: center; margin-bottom: 16px; }
  .letra-actual { font-size: clamp(5rem, 15vw, 8rem); font-weight: 900; color: var(--primary); line-height: 1; min-height: 120px; transition: all .2s; }
  .letra-actual.nada { color: #9aa9b5; }
  .letra-actual.finalizar { color: var(--accent); }
  .confianza { color: var(--muted); min-height: 24px; font-weight: 700; }
  .estado-badge { display: inline-flex; align-items: center; gap: 8px; padding: 9px 14px; border-radius: 999px; font-size: .8rem; font-weight: 900; text-transform: uppercase; letter-spacing: .05em; margin-top: 14px; }
  .estado-badge.activo { background: #dcfce7; color: #166534; }
  .estado-badge.esperando { background: #fef3c7; color: #92400e; }
  .estado-badge.completado { background: var(--accent-soft); color: #4c1d95; }
  .texto-label { font-size: .8rem; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; font-weight: 900; margin-bottom: 10px; }
  .texto-formado { font-size: clamp(1.7rem, 5vw, 2.7rem); font-weight: 850; color: var(--text); background: #f8fbfc; border: 1px solid var(--border); border-radius: 18px; padding: 22px; min-height: 86px; word-break: break-word; }
  .texto-formado.finalizado { border-color: rgba(22, 163, 74, .45); box-shadow: 0 0 0 4px rgba(22, 163, 74, .10); color: var(--success); }
  .cursor { animation: blink 1s infinite; color: var(--primary); }
  @keyframes blink { 0%,50%{opacity:1;} 51%,100%{opacity:0;} }
  .historial { margin-top: 16px; }
  .historial-item, .resp-item { background: #f8fbfc; border: 1px solid var(--border); border-radius: 16px; padding: 13px 15px; margin-top: 8px; display: flex; justify-content: space-between; gap: 12px; align-items: center; }
  .historial-texto, .resp-texto { font-weight: 750; color: var(--text); }
  .historial-hora, .resp-hora { color: var(--muted); font-size: .82rem; white-space: nowrap; }

  .input-row { display: grid; grid-template-columns: 1fr auto auto; gap: 10px; margin-top: 14px; }
  .input-texto, .speed-select { padding: 15px 16px; font-size: 1.05rem; border: 1px solid #bfd7dc; border-radius: 15px; color: var(--text); background: #fbffff; outline: none; }
  .input-texto { font-weight: 750; text-transform: uppercase; }
  .input-texto:focus, .speed-select:focus { border-color: var(--primary); box-shadow: 0 0 0 4px rgba(15,118,110,.12); }
  .btn { border: 0; border-radius: 15px; padding: 14px 18px; font-weight: 900; cursor: pointer; transition: transform .15s ease, filter .15s ease, background .15s ease; font-size: .97rem; }
  .btn:hover:not(:disabled) { transform: translateY(-1px); filter: brightness(.98); }
  .btn:disabled { opacity: .45; cursor: not-allowed; }
  .btn-primary { background: var(--primary); color: white; }
  .btn-secondary { background: #e8f4f5; color: var(--primary-strong); }
  .btn-ghost { background: #f2f5f8; color: var(--muted); }

  .reply-status { display: inline-flex; align-items: center; gap: 8px; width: fit-content; padding: 9px 14px; border-radius: 999px; font-size: .82rem; font-weight: 900; text-transform: uppercase; letter-spacing: .05em; background: #eef6ff; color: #1e3a8a; }
  .reply-status.playing { background: #dcfce7; color: #166534; }
  .reply-status.finished { background: var(--accent-soft); color: #4c1d95; }
  .reply-status.warning { background: #fff7ed; color: #9a3412; }
  .sequence-message { color: var(--muted); line-height: 1.55; font-weight: 750; }
  .countdown-number { font-size: clamp(7rem, 26vw, 13rem); line-height: .9; font-weight: 950; color: var(--primary); text-align: center; text-shadow: 0 18px 35px rgba(15, 118, 110, .20); animation: pulseCount .65s ease; }
  @keyframes pulseCount { 0% { transform: scale(.82); opacity: .25; } 70% { transform: scale(1.06); opacity: 1; } 100% { transform: scale(1); opacity: 1; } }
  .final-card { border: 1px solid rgba(22, 163, 74, .35); background: #f0fdf4; color: #14532d; border-radius: 22px; padding: 20px; box-shadow: 0 12px 32px rgba(22, 163, 74, .10); }
  .final-card h3 { font-size: clamp(1.5rem, 4vw, 2.1rem); margin-bottom: 8px; }
  .final-phrase { margin-top: 12px; padding: 16px; border-radius: 16px; background: white; color: var(--text); font-size: clamp(1.7rem, 5vw, 2.8rem); font-weight: 950; word-break: break-word; }
  .final-images-title { margin-top: 18px; font-weight: 950; color: var(--text); }
  .final-images-grid { margin-top: 12px; display: grid; grid-template-columns: repeat(auto-fill, minmax(96px, 1fr)); gap: 12px; }
  .final-image-card { min-height: 116px; border-radius: 18px; background: white; border: 1px solid rgba(22, 163, 74, .22); display: grid; place-items: center; padding: 10px; }
  .final-image-card img { width: 100%; max-width: 96px; aspect-ratio: 1; object-fit: contain; }
  .unsupported-list { margin-top: 12px; display: grid; gap: 8px; }
  .unsupported-item { padding: 10px 12px; border-radius: 12px; background: #fff7ed; color: #9a3412; font-weight: 800; }

  .sequence-shell { margin-top: 20px; display: none; }
  .sequence-shell.visible { display: grid; gap: 16px; }
  .sequence-stage { display: grid; grid-template-columns: minmax(220px, 330px) 1fr; gap: 18px; align-items: stretch; }
  .current-sign { border-radius: 26px; background: linear-gradient(155deg, var(--accent-soft), #ffffff); border: 1px solid #d9d5ff; padding: 24px; text-align: center; min-height: 260px; display: grid; place-items: center; }
  .sign-image { width: min(190px, 58vw); height: min(190px, 58vw); object-fit: contain; display: none; margin: 0 auto 8px; }
  .sign-loading { width: min(190px, 58vw); height: min(190px, 58vw); margin: 0 auto 10px; border-radius: 40px; display: grid; place-items: center; background: rgba(255,255,255,.72); border: 2px dashed #c9c3ff; color: var(--muted); font-weight: 900; }
  .missing-note { display: none; margin-top: 10px; padding: 9px 11px; border-radius: 12px; background: #fff7ed; color: #9a3412; font-size: .9rem; font-weight: 700; }
  .sequence-info h3 { font-size: 1.5rem; margin-bottom: 8px; }
  .sequence-meta { color: var(--muted); font-weight: 750; margin-bottom: 16px; }
  .controls { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin: 16px 0; }
  .speed-control { display: flex; align-items: center; gap: 8px; color: var(--muted); font-weight: 800; }
  .senas-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(92px, 1fr)); gap: 12px; margin-top: 14px; }
  .sena-card { background: #fbffff; border: 2px solid #d7d2ff; border-radius: 18px; padding: 12px 8px; text-align: center; animation: aparecer .35s ease-out forwards; opacity: 0; transform: translateY(12px); cursor: pointer; }
  .sena-card.active { border-color: var(--accent); box-shadow: 0 0 0 4px rgba(109,93,252,.12); }
  .sena-card.unsupported { border-color: #fed7aa; background: #fff7ed; }
  .sena-letra { font-size: 2.3rem; font-weight: 950; color: var(--accent); line-height: 1; }
  .sena-card.unsupported .sena-letra { color: var(--warning); }
  .sena-desc { color: var(--muted); font-size: .72rem; line-height: 1.25; margin-top: 7px; min-height: 28px; }
  @keyframes aparecer { to { opacity: 1; transform: translateY(0); } }
  .empty-state { border: 1px dashed #bcd7dc; border-radius: 20px; padding: 24px; color: var(--muted); text-align: center; background: rgba(255,255,255,.52); }
  @media (max-width: 820px) {
    body { padding: 18px 12px 30px; }
    .mode-grid, .detection-layout, .sequence-stage { grid-template-columns: 1fr; }
    .section-header { flex-direction: column; }
    .input-row { grid-template-columns: 1fr; }
    .camera-zone { min-height: 260px; }
    .controls .btn, .speed-control, .speed-select { width: 100%; justify-content: center; }
  }
</style>
</head>
<body>
<div class="container">
  <header class="hero">
    <div class="eyebrow">🤝 Tecnología accesible</div>
    <h1>RAPIRO LSA</h1>
    <p class="subtitle">Comunicación bidireccional entre persona sorda y persona oyente.</p>
  </header>

  <nav class="mode-grid" aria-label="Opciones principales">
    <button class="mode-card active" type="button" onclick="cambiarTab(0)">
      <div class="mode-icon">🖐️</div>
      <h2>Detección de señas</h2>
      <p>La persona sorda realiza una seña frente a la cámara y el sistema la interpreta.</p>
    </button>
    <button class="mode-card" type="button" onclick="cambiarTab(1)">
      <div class="mode-icon">💬</div>
      <h2>Responder en LSA</h2>
      <p>La persona oyente escribe una palabra o frase y el sistema la muestra mediante imágenes de señas.</p>
    </button>
  </nav>

  <section class="panel active" id="tab0" aria-live="polite">
    <div class="section-header">
      <div><h2>Detectar señas</h2><p>Ubicá la mano dentro de la zona de cámara. El resultado detectado aparecerá en tiempo real.</p></div>
      <div class="estado-badge esperando" id="estado">Esperando seña…</div>
    </div>
    <div class="detection-layout">
      <div class="camera-zone">
        <div class="camera-label"><span>Zona de cámara / detección</span><span>● En vivo</span></div>
        <div class="camera-visual"><div class="hand">🖐️</div><p>Colocá la seña frente a la cámara del sistema detector.</p></div>
        <div class="help-text" style="color:rgba(255,255,255,.78)">Estados: Esperando seña → Detectando → Resultado detectado.</div>
      </div>
      <div>
        <div class="result-card">
          <div class="texto-label">Letra, palabra o acción detectada</div>
          <div class="letra-actual" id="letra">-</div>
          <div class="confianza" id="confianza"></div>
        </div>
        <div class="message-card">
          <div class="texto-label">Mensaje detectado</div>
          <div class="texto-formado" id="texto"><span class="cursor">|</span></div>
          <p class="help-text" style="margin-top:12px">Cuando el detector finalice el mensaje, se guardará automáticamente en el historial.</p>
        </div>
        <div class="historial" id="historial"></div>
      </div>
    </div>
  </section>

  <section class="panel" id="tab1">
    <div class="section-header">
      <div><h2>Responder en LSA</h2><p>Escribí una palabra o frase. Se normaliza a mayúsculas y se muestran las señas letra por letra.</p></div>
    </div>
    <div class="reply-card">
      <label class="texto-label" for="inputResp">Texto de la persona oyente</label>
      <div class="input-row">
        <input type="text" class="input-texto" id="inputResp" placeholder="Ej.: HOLA" maxlength="80" autocomplete="off">
        <button class="btn btn-primary" id="generateBtn" onclick="enviarRespuesta()">Generar señas</button>
        <button class="btn btn-ghost" onclick="limpiarSenas()">Reiniciar</button>
      </div>
      <p class="help-text" style="margin-top:12px">Se ignoran espacios para reproducir la secuencia y los caracteres sin imagen disponible se marcan con aviso.</p>
    </div>
    <div id="senasContainer" class="sequence-shell"></div>
    <div class="respuesta-historial" id="respHistorial"></div>
  </section>
</div>

<script>
const SIGN_IMAGE_BASE = '/static/lsa/';
const SIGN_IMAGE_EXT = '.png';
const LSA_DESC = {
  'A': 'Puño cerrado, pulgar al costado', 'B': 'Dedos índice y medio extendidos', 'C': 'Mano curvada en forma de C',
  'D': 'Índice, medio y anular abiertos', 'E': 'Mano en C tocando la mejilla', 'F': 'Índice y pulgar unidos',
  'G': 'Índice apuntando al costado', 'H': 'Índice y medio horizontales', 'I': 'Meñique extendido', 'J': 'Meñique traza una J',
  'K': 'Índice y medio en V', 'L': 'Pulgar e índice en L', 'M': 'Tres dedos sobre el pulgar', 'N': 'Dos dedos sobre el pulgar',
  'O': 'Dedos formando círculo', 'P': 'Similar a K hacia abajo', 'Q': 'Índice y pulgar hacia abajo', 'R': 'Índice y medio cruzados',
  'S': 'Puño cerrado cerca de la cara', 'T': 'Pulgar entre índice y medio', 'U': 'Índice y medio juntos', 'V': 'Índice y medio en V',
  'W': 'Tres dedos abiertos', 'X': 'Índice doblado', 'Y': 'Pulgar y meñique extendidos', 'Z': 'Índice traza una Z'
};
const SUPPORTED_CHARS = Object.keys(LSA_DESC);
const COUNTDOWN_VALUES = ['3', '2', '1'];
let respHistorial = [];
let replyState = 'idle';
let currentSequence = [];
let currentIndex = 0;
let currentPhrase = '';
let countdownIndex = 0;
let sequenceTimer = null;
const LETTER_DURATION_MS = 4000;
let missingMessages = [];
let preloadedSignImages = new Map();
let paused = false;

function cambiarTab(idx) {
  document.querySelectorAll('.mode-card').forEach((t,i) => t.classList.toggle('active', i===idx));
  document.querySelectorAll('.panel').forEach((c,i) => c.classList.toggle('active', i===idx));
}
function normalizarTexto(valor) {
  return valor.toUpperCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/\s+/g, ' ').trim();
}
function caracteresSecuencia(texto) { return normalizarTexto(texto).replace(/\s/g, '').split(''); }
function setGeneratingDisabled(disabled) {
  const btn = document.getElementById('generateBtn');
  if (btn) btn.disabled = disabled;
}
function enviarRespuesta() {
  if (replyState === 'countdown' || replyState === 'playing') return;
  const input = document.getElementById('inputResp');
  const texto = normalizarTexto(input.value);
  if (!texto) {
    renderInitialState('Escribí una palabra o frase para generar las señas en LSA.');
    return;
  }
  limpiarTimers();
  currentPhrase = texto;
  currentSequence = caracteresSecuencia(texto);
  currentIndex = 0;
  countdownIndex = 0;
  missingMessages = [];
  preloadedSignImages = new Map();
  paused = false;
  if (!currentSequence.length) {
    renderInitialState('No hay letras reproducibles. Escribí al menos una letra para generar señas.');
    return;
  }
  respHistorial.unshift({ texto, hora: new Date().toLocaleTimeString() });
  actualizarRespHistorial();
  fetch('/api/respuesta', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({texto}) });
  precargarImagenesSecuencia();
  iniciarConteo();
}
function precargarImagenesSecuencia() {
  [...new Set(currentSequence)].filter(letra => SUPPORTED_CHARS.includes(letra)).forEach(letra => {
    const img = new Image();
    img.src = SIGN_IMAGE_BASE + encodeURIComponent(letra) + SIGN_IMAGE_EXT;
    preloadedSignImages.set(letra, img);
  });
}
function iniciarConteo() {
  replyState = 'countdown';
  setGeneratingDisabled(true);
  renderCountdown(COUNTDOWN_VALUES[countdownIndex]);
  sequenceTimer = setTimeout(avanzarConteo, 1000);
}
function avanzarConteo() {
  countdownIndex += 1;
  if (countdownIndex < COUNTDOWN_VALUES.length) {
    renderCountdown(COUNTDOWN_VALUES[countdownIndex]);
    sequenceTimer = setTimeout(avanzarConteo, 1000);
    return;
  }
  replyState = 'playing';
  currentIndex = 0;
  reproducirLetraActual();
}
function reproducirLetraActual() {
  if (replyState !== 'playing' || paused) return;
  if (currentIndex >= currentSequence.length) {
    finalizarSecuencia();
    return;
  }
  renderPlaying();
  currentIndex += 1;
  sequenceTimer = setTimeout(reproducirLetraActual, LETTER_DURATION_MS);
}
function togglePausa() {
  if (replyState !== 'playing') return;
  paused = !paused;
  if (paused) {
    limpiarTimers(false);
    renderPlaying();
  } else {
    reproducirLetraActual();
  }
}
function limpiarTimers(resetPaused = true) {
  if (sequenceTimer) clearTimeout(sequenceTimer);
  sequenceTimer = null;
  if (resetPaused) paused = false;
}
function renderInitialState(message = 'Escribí una palabra o frase para generar las señas en LSA.') {
  const container = document.getElementById('senasContainer');
  container.className = 'sequence-shell visible';
  container.innerHTML = `<div class="empty-state">${escapeHTML(message)}</div>`;
}
function renderCountdown(value) {
  const container = document.getElementById('senasContainer');
  container.className = 'sequence-shell visible';
  container.innerHTML = `
    <div class="current-sign" aria-live="assertive">
      <div>
        <div class="reply-status playing">Preparando secuencia</div>
        <div class="countdown-number" key="${escapeHTML(value)}">${escapeHTML(value)}</div>
        <p class="sequence-message">Las señas se mostrarán una por una durante 4 segundos.</p>
      </div>
    </div>`;
}
function renderPlaying() {
  const letra = currentSequence[currentIndex] || '';
  const supported = SUPPORTED_CHARS.includes(letra);
  const imgPath = SIGN_IMAGE_BASE + encodeURIComponent(letra) + SIGN_IMAGE_EXT;
  const container = document.getElementById('senasContainer');
  container.className = 'sequence-shell visible';
  container.innerHTML = `
    <div class="sequence-stage">
      <div class="current-sign">
        <div>
          <img id="signImage" class="sign-image" alt="Imagen de seña LSA para la letra actual">
          <div id="signLoading" class="sign-loading">Cargando imagen…</div>
          <div class="texto-label">Seña actual</div>
          <div class="missing-note" id="missingNote"></div>
        </div>
      </div>
      <div class="sequence-info">
        <div class="reply-status playing">${paused ? 'Secuencia pausada' : 'Reproduciendo'}</div>
        <h3>Letra ${currentIndex + 1} de ${currentSequence.length}</h3>
        <div class="sequence-meta">Frase a generar: ${escapeHTML(currentPhrase)}</div>
        <p class="sequence-message">${escapeHTML(LSA_DESC[letra] || 'No hay imagen disponible para este carácter; la secuencia continúa.')}</p>
        <div class="controls">
          <button class="btn btn-secondary" onclick="togglePausa()">${paused ? '▶ Reanudar' : '⏸ Pausar'}</button>
          <button class="btn btn-ghost" onclick="limpiarSenas()">↺ Reiniciar</button>
        </div>
      </div>
    </div>`;
  const img = document.getElementById('signImage');
  const note = document.getElementById('missingNote');
  const loading = document.getElementById('signLoading');
  if (!supported) {
    const msg = `No hay imagen disponible para el carácter: ${letra}`;
    registrarFaltante(msg);
    note.textContent = msg;
    note.style.display = 'block';
    loading.style.display = 'none';
    return;
  }
  const preloaded = preloadedSignImages.get(letra);
  if (preloaded && preloaded.complete && preloaded.naturalWidth > 0) {
    img.style.display = 'block';
    loading.style.display = 'none';
  }
  img.onload = () => {
    img.style.display = 'block';
    loading.style.display = 'none';
  };
  img.onerror = () => {
    const msg = `No se encontró la imagen ${letra}${SIGN_IMAGE_EXT}. Cargala en static/lsa/ para verla.`;
    registrarFaltante(msg);
    img.style.display = 'none';
    note.textContent = msg;
    note.style.display = 'block';
    loading.style.display = 'none';
  };
  img.src = imgPath;
}
function registrarFaltante(msg) {
  if (!missingMessages.includes(msg)) missingMessages.push(msg);
}
function imagenesUsadasHTML() {
  const imagenes = currentSequence.filter(letra => SUPPORTED_CHARS.includes(letra));
  if (!imagenes.length) return '';
  return `
    <div class="final-images-title">Imágenes utilizadas:</div>
    <div class="final-images-grid">
      ${imagenes.map(letra => {
        const imgPath = SIGN_IMAGE_BASE + encodeURIComponent(letra) + SIGN_IMAGE_EXT;
        return `<div class="final-image-card"><img src="${imgPath}" alt="Imagen de seña LSA utilizada" onerror="this.closest('.final-image-card').style.display='none'"></div>`;
      }).join('')}
    </div>`;
}
function finalizarSecuencia() {
  limpiarTimers();
  replyState = 'finished';
  setGeneratingDisabled(false);
  const warnings = missingMessages.length ? `<div class="unsupported-list">${missingMessages.map(m => `<div class="unsupported-item">${escapeHTML(m)}</div>`).join('')}</div>` : '';
  const usedImages = imagenesUsadasHTML();
  const container = document.getElementById('senasContainer');
  container.className = 'sequence-shell visible';
  container.innerHTML = `
    <div class="final-card">
      <div class="reply-status finished">Secuencia finalizada</div>
      <h3>Secuencia finalizada</h3>
      <p>Frase generada:</p>
      <div class="final-phrase">${escapeHTML(currentPhrase)}</div>
      ${usedImages}
      ${warnings}
      <div class="controls"><button class="btn btn-ghost" onclick="limpiarSenas()">↺ Reiniciar</button></div>
    </div>`;
}
function limpiarSenas() {
  limpiarTimers();
  replyState = 'idle';
  currentSequence = [];
  currentIndex = 0;
  currentPhrase = '';
  missingMessages = [];
  setGeneratingDisabled(false);
  document.getElementById('inputResp').value = '';
  renderInitialState();
}
function actualizarRespHistorial() {
  const el = document.getElementById('respHistorial');
  if (respHistorial.length === 0) { el.innerHTML = ''; return; }
  el.innerHTML = '<div class="texto-label" style="margin-top:18px">Respuestas enviadas</div>' + respHistorial.slice(0,5).map(r => `<div class="resp-item"><span class="resp-texto">${escapeHTML(r.texto)}</span><span class="resp-hora">${r.hora}</span></div>`).join('');
}
function escapeHTML(value) { return String(value).replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char])); }
document.addEventListener('keydown', e => { if (e.key === 'Enter' && document.activeElement.id === 'inputResp') enviarRespuesta(); });
document.addEventListener('DOMContentLoaded', () => renderInitialState());
async function actualizar() {
  try {
    const res = await fetch('/api/estado');
    const data = await res.json();
    const letraEl = document.getElementById('letra');
    const confEl = document.getElementById('confianza');
    const textoEl = document.getElementById('texto');
    const estadoEl = document.getElementById('estado');
    letraEl.textContent = data.letra_actual || '-';
    letraEl.className = 'letra-actual';
    if (data.letra_actual === 'NADA') letraEl.classList.add('nada');
    if (data.letra_actual === 'FINALIZAR') letraEl.classList.add('finalizar');
    confEl.textContent = data.confianza > 0 ? (data.confianza * 100).toFixed(0) + '% confianza' : '';
    if (data.finalizado) {
      textoEl.textContent = data.texto_actual;
      textoEl.className = 'texto-formado finalizado';
      estadoEl.textContent = 'Resultado detectado';
      estadoEl.className = 'estado-badge completado';
    } else if (data.letra_actual || data.texto_actual) {
      textoEl.innerHTML = escapeHTML(data.texto_actual || '') + '<span class="cursor">|</span>';
      textoEl.className = 'texto-formado';
      estadoEl.textContent = 'Detectando…';
      estadoEl.className = 'estado-badge activo';
    } else {
      textoEl.innerHTML = '<span class="cursor">|</span>';
      textoEl.className = 'texto-formado';
      estadoEl.textContent = 'Esperando seña…';
      estadoEl.className = 'estado-badge esperando';
    }
    const histEl = document.getElementById('historial');
    histEl.innerHTML = data.historial && data.historial.length > 0 ? '<div class="history-card"><div class="texto-label">Historial de mensajes</div>' + data.historial.map(h => `<div class="historial-item"><span class="historial-texto">${escapeHTML(h.texto)}</span><span class="historial-hora">${h.hora}</span></div>`).reverse().join('') + '</div>' : '';
  } catch (e) {}
}
setInterval(actualizar, 300);
actualizar();
</script>
</body>
</html>"""


@app.route("/")
def index():
    return Response(HTML_PAGE, mimetype="text/html")


@app.route("/api/estado")
def get_estado():
    return jsonify(estado)


@app.route("/api/letra", methods=["POST"])
def recibir_letra():
    data = request.json
    estado["letra_actual"] = data.get("letra", "")
    estado["confianza"] = data.get("confianza", 0.0)
    estado["texto_actual"] = data.get("texto", "")
    estado["finalizado"] = False
    return jsonify({"ok": True})


@app.route("/api/finalizar", methods=["POST"])
def finalizar():
    data = request.json
    texto = data.get("texto", "")
    estado["texto_actual"] = texto
    estado["finalizado"] = True
    estado["letra_actual"] = "FINALIZAR"
    estado["historial"].append({
        "texto": texto,
        "hora": datetime.now().strftime("%H:%M:%S"),
    })
    print(f"\n  MENSAJE FINALIZADO: \"{texto}\"")
    return jsonify({"ok": True})


@app.route("/api/respuesta", methods=["POST"])
def recibir_respuesta():
    data = request.json
    texto = data.get("texto", "")
    estado["respuesta_imagenes"] = texto
    print(f"\n  RESPUESTA LSA: \"{texto}\"")
    return jsonify({"ok": True})


@app.route("/api/reset", methods=["POST"])
def reset():
    estado["texto_actual"] = ""
    estado["letra_actual"] = ""
    estado["confianza"] = 0.0
    estado["finalizado"] = False
    return jsonify({"ok": True})


if __name__ == "__main__":
    print("=" * 50)
    print("  Servidor web LSA - Bidireccional")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False)
