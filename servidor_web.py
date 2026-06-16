"""
Servidor web — Traductor LSA bidireccional
--------------------------------------------
Sección 1: Muestra las señas detectadas en tiempo real
Sección 2: Respuesta en imágenes LSA (persona no sorda escribe y se muestra en señas)

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
<title>RAPIRO LSA - Traductor de Lengua de Senas</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: #0f1117;
    color: #e4e4e7;
    min-height: 100vh;
    padding: 30px 20px;
  }
  .container { max-width: 900px; margin: 0 auto; }
  h1 {
    font-size: 1.3rem;
    font-weight: 500;
    color: #71717a;
    margin-bottom: 30px;
    letter-spacing: 2px;
    text-transform: uppercase;
    text-align: center;
  }

  /* Tabs */
  .tabs {
    display: flex;
    gap: 4px;
    margin-bottom: 24px;
    background: #18181b;
    border-radius: 12px;
    padding: 4px;
  }
  .tab {
    flex: 1;
    padding: 12px;
    text-align: center;
    border-radius: 10px;
    cursor: pointer;
    font-weight: 600;
    font-size: 0.9rem;
    transition: all 0.2s;
    color: #71717a;
  }
  .tab.active { background: #27272a; color: #e4e4e7; }
  .tab:hover:not(.active) { color: #a1a1aa; }
  .tab-content { display: none; }
  .tab-content.active { display: block; }

  /* Seccion 1: Deteccion */
  .letra-actual {
    font-size: 7rem;
    font-weight: 700;
    color: #22c55e;
    line-height: 1;
    min-height: 120px;
    text-align: center;
    transition: all 0.2s;
  }
  .letra-actual.nada { color: #3f3f46; }
  .letra-actual.finalizar { color: #a855f7; }
  .confianza { font-size: 1.1rem; color: #71717a; margin-top: 8px; text-align: center; min-height: 22px; }
  .estado-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 16px;
  }
  .estado-badge.activo { background: #052e16; color: #22c55e; }
  .estado-badge.esperando { background: #1c1917; color: #78716c; }
  .estado-badge.completado { background: #1e1b4b; color: #a855f7; }
  .texto-container { margin-top: 36px; }
  .texto-label {
    font-size: 0.8rem; color: #52525b; text-transform: uppercase;
    letter-spacing: 1px; margin-bottom: 10px;
  }
  .texto-formado {
    font-size: 2.4rem; font-weight: 600; color: #e4e4e7;
    background: #18181b; border: 1px solid #27272a; border-radius: 14px;
    padding: 24px 30px; min-height: 80px; word-wrap: break-word; transition: all 0.3s;
  }
  .texto-formado.finalizado {
    border-color: #22c55e; box-shadow: 0 0 30px rgba(34,197,94,0.15); color: #22c55e;
  }
  .cursor { animation: blink 1s infinite; }
  @keyframes blink { 0%,50% { opacity:1; } 51%,100% { opacity:0; } }

  .historial { margin-top: 30px; }
  .historial-item {
    background: #18181b; border: 1px solid #27272a; border-radius: 10px;
    padding: 14px 18px; margin-top: 8px;
    display: flex; justify-content: space-between; align-items: center;
  }
  .historial-texto { font-size: 1rem; color: #a1a1aa; }
  .historial-hora { font-size: 0.75rem; color: #52525b; }

  /* Seccion 2: Responder */
  .responder-area {
    background: #18181b; border: 1px solid #27272a; border-radius: 14px;
    padding: 24px; margin-bottom: 24px;
  }
  .responder-label { font-size: 0.95rem; color: #a1a1aa; margin-bottom: 12px; }
  .input-row { display: flex; gap: 10px; }
  .input-texto {
    flex: 1; padding: 14px 18px; font-size: 1.2rem; font-weight: 600;
    background: #0f1117; border: 1px solid #3f3f46; border-radius: 10px;
    color: #e4e4e7; outline: none; text-transform: uppercase;
  }
  .input-texto:focus { border-color: #a855f7; }
  .btn-enviar {
    padding: 14px 28px; font-size: 1rem; font-weight: 700;
    background: #7c3aed; color: white; border: none; border-radius: 10px;
    cursor: pointer; transition: all 0.2s; text-transform: uppercase; letter-spacing: 1px;
  }
  .btn-enviar:hover { background: #6d28d9; }
  .btn-limpiar {
    padding: 14px 20px; font-size: 0.9rem; font-weight: 600;
    background: #27272a; color: #a1a1aa; border: none; border-radius: 10px;
    cursor: pointer; transition: all 0.2s;
  }
  .btn-limpiar:hover { background: #3f3f46; }

  /* Cartas de letras LSA */
  .senas-grid {
    display: flex; flex-wrap: wrap; gap: 14px;
    justify-content: center; margin-top: 24px;
  }
  .sena-card {
    width: 110px; background: #1e1b4b; border: 2px solid #4c1d95;
    border-radius: 14px; padding: 14px 8px; text-align: center;
    animation: aparecer 0.4s ease-out forwards;
    opacity: 0; transform: translateY(20px);
  }
  .sena-card.espacio {
    width: 80px; background: #1c1917; border-color: #44403c;
  }
  @keyframes aparecer {
    to { opacity: 1; transform: translateY(0); }
  }
  .sena-letra {
    font-size: 2.8rem; font-weight: 800; color: #c4b5fd; line-height: 1;
  }
  .sena-card.espacio .sena-letra { font-size: 1.2rem; color: #78716c; }
  .sena-desc {
    font-size: 0.65rem; color: #8b5cf6; margin-top: 6px;
    line-height: 1.3; min-height: 28px;
  }

  .respuesta-historial { margin-top: 20px; }
  .resp-item {
    background: #1e1b4b; border: 1px solid #4c1d95; border-radius: 10px;
    padding: 14px 18px; margin-top: 8px;
    display: flex; justify-content: space-between; align-items: center;
  }
  .resp-texto { font-size: 1rem; color: #c4b5fd; }
  .resp-hora { font-size: 0.75rem; color: #6d28d9; }

  .center { text-align: center; }
</style>
</head>
<body>
<div class="container">
  <h1>Rapiro LSA - Comunicacion bidireccional</h1>

  <div class="tabs">
    <div class="tab active" onclick="cambiarTab(0)">Deteccion de senas</div>
    <div class="tab" onclick="cambiarTab(1)">Responder en LSA</div>
  </div>

  <!-- TAB 1: Deteccion -->
  <div class="tab-content active" id="tab0">
    <div class="center">
      <div class="letra-actual" id="letra">-</div>
      <div class="confianza" id="confianza"></div>
      <div class="estado-badge esperando" id="estado">Esperando conexion</div>
    </div>

    <div class="texto-container">
      <div class="texto-label">Mensaje detectado</div>
      <div class="texto-formado" id="texto"><span class="cursor">|</span></div>
    </div>

    <div class="historial" id="historial"></div>
  </div>

  <!-- TAB 2: Responder -->
  <div class="tab-content" id="tab1">
    <div class="responder-area">
      <div class="responder-label">Escribi tu respuesta y se mostrara en Lengua de Senas Argentina:</div>
      <div class="input-row">
        <input type="text" class="input-texto" id="inputResp" placeholder="Escribi aca..." maxlength="50">
        <button class="btn-enviar" onclick="enviarRespuesta()">Mostrar en LSA</button>
        <button class="btn-limpiar" onclick="limpiarSenas()">Limpiar</button>
      </div>
    </div>

    <div id="senasContainer"></div>

    <div class="respuesta-historial" id="respHistorial"></div>
  </div>
</div>

<script>
// Descripciones de cada sena LSA
const LSA_DESC = {
  'A': 'Puno cerrado, pulgar al costado',
  'B': 'Dedos indice y medio extendidos',
  'C': 'Mano curvada en forma de C',
  'D': 'Indice, medio y anular abiertos',
  'E': 'Mano en C tocando la mejilla',
  'F': 'Indice y pulgar unidos, resto cerrado',
  'G': 'Indice apuntando hacia el costado',
  'H': 'Dedos indice y medio horizontales',
  'I': 'Menique extendido, resto cerrado',
  'J': 'Menique traza forma de J',
  'K': 'Indice y medio en V, pulgar entre ellos',
  'L': 'Pulgar e indice en forma de L',
  'M': 'Tres dedos sobre el pulgar en puno',
  'N': 'Dos dedos sobre el pulgar en puno',
  'O': 'Dedos unidos formando un circulo',
  'P': 'Similar a K pero mano hacia abajo',
  'Q': 'Indice y pulgar hacia abajo',
  'R': 'Dedos indice y medio cruzados',
  'S': 'Puno cerrado cerca de la cara',
  'T': 'Pulgar entre indice y medio cerrados',
  'U': 'Indice y medio juntos hacia arriba',
  'V': 'Indice y medio abiertos en V',
  'W': 'Tres dedos abiertos hacia arriba',
  'X': 'Indice doblado como gancho',
  'Y': 'Pulgar y menique extendidos',
  'Z': 'Indice traza forma de Z en el aire',
  ' ': 'Espacio',
};

let respHistorial = [];

function cambiarTab(idx) {
  document.querySelectorAll('.tab').forEach((t,i) => t.classList.toggle('active', i===idx));
  document.querySelectorAll('.tab-content').forEach((c,i) => c.classList.toggle('active', i===idx));
}

function enviarRespuesta() {
  const input = document.getElementById('inputResp');
  const texto = input.value.trim().toUpperCase();
  if (!texto) return;

  const container = document.getElementById('senasContainer');
  container.innerHTML = '';

  const grid = document.createElement('div');
  grid.className = 'senas-grid';

  texto.split('').forEach((letra, i) => {
    const card = document.createElement('div');
    card.className = 'sena-card' + (letra === ' ' ? ' espacio' : '');
    card.style.animationDelay = (i * 0.15) + 's';

    const letraEl = document.createElement('div');
    letraEl.className = 'sena-letra';
    letraEl.textContent = letra === ' ' ? '___' : letra;

    const descEl = document.createElement('div');
    descEl.className = 'sena-desc';
    descEl.textContent = LSA_DESC[letra] || '';

    card.appendChild(letraEl);
    card.appendChild(descEl);
    grid.appendChild(card);
  });

  container.appendChild(grid);

  // Guardar en historial
  respHistorial.unshift({ texto: texto, hora: new Date().toLocaleTimeString() });
  actualizarRespHistorial();

  // Enviar al servidor
  fetch('/api/respuesta', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({texto: texto})
  });

  input.value = '';
}

function limpiarSenas() {
  document.getElementById('senasContainer').innerHTML = '';
}

function actualizarRespHistorial() {
  const el = document.getElementById('respHistorial');
  if (respHistorial.length === 0) { el.innerHTML = ''; return; }
  el.innerHTML = '<div class="texto-label">Respuestas enviadas</div>' +
    respHistorial.map(r =>
      '<div class="resp-item">' +
        '<span class="resp-texto">' + r.texto + '</span>' +
        '<span class="resp-hora">' + r.hora + '</span>' +
      '</div>'
    ).join('');
}

// Enter para enviar
document.addEventListener('keydown', e => {
  if (e.key === 'Enter' && document.activeElement.id === 'inputResp') {
    enviarRespuesta();
  }
});

// Polling de deteccion (tab 1)
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

    if (data.confianza > 0) {
      confEl.textContent = (data.confianza * 100).toFixed(0) + '% confianza';
    } else {
      confEl.textContent = '';
    }

    if (data.finalizado) {
      textoEl.textContent = data.texto_actual;
      textoEl.className = 'texto-formado finalizado';
      estadoEl.textContent = 'Mensaje completo';
      estadoEl.className = 'estado-badge completado';
    } else if (data.texto_actual) {
      textoEl.innerHTML = data.texto_actual + '<span class="cursor">|</span>';
      textoEl.className = 'texto-formado';
      estadoEl.textContent = 'Detectando';
      estadoEl.className = 'estado-badge activo';
    } else {
      textoEl.innerHTML = '<span class="cursor">|</span>';
      textoEl.className = 'texto-formado';
      estadoEl.textContent = 'Esperando senas';
      estadoEl.className = 'estado-badge esperando';
    }

    const histEl = document.getElementById('historial');
    if (data.historial && data.historial.length > 0) {
      histEl.innerHTML = '<div class="texto-label">Historial de mensajes</div>' +
        data.historial.map(h =>
          '<div class="historial-item">' +
            '<span class="historial-texto">' + h.texto + '</span>' +
            '<span class="historial-hora">' + h.hora + '</span>' +
          '</div>'
        ).reverse().join('');
    }
  } catch (e) {}
}

setInterval(actualizar, 300);
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
