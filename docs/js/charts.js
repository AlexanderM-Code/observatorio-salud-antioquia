// Gráficas en SVG hechas a mano, sin librerías externas.
// Todas miden el ancho real de su contenedor para que el texto
// conserve su tamaño en celular y en escritorio.

const NS = 'http://www.w3.org/2000/svg';
export const formato = new Intl.NumberFormat('es-CO');

function crear(tag, atributos = {}, padre) {
  const el = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(atributos)) el.setAttribute(k, v);
  if (padre) padre.appendChild(el);
  return el;
}

function texto(padre, x, y, contenido, atributos = {}) {
  const t = crear('text', { x, y, ...atributos }, padre);
  t.textContent = contenido;
  return t;
}

// Máximo del eje redondeado a un número fácil de leer (1, 1,5, 2, 2,5, 3, 4, 5, 6, 8 o 10 × 10^n).
const PASOS = [1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10];
function maximoBonito(valor) {
  if (valor <= 0) return 1;
  const exp = 10 ** Math.floor(Math.log10(valor));
  return PASOS.find((p) => p * exp >= valor) * exp;
}

function lienzo(contenedor, alto) {
  const ancho = Math.max(280, Math.round(contenedor.clientWidth || 640));
  contenedor.innerHTML = '';
  const svg = crear('svg', { viewBox: `0 0 ${ancho} ${alto}` }, contenedor);
  return { svg, ancho, alto };
}

// Elige cuántas líneas guía usar para que todas caigan en números redondos.
function divisionesRedondas(max) {
  for (const d of [4, 5, 3]) {
    const paso = max / d;
    const base = paso / 10 ** Math.floor(Math.log10(paso));
    if ([1, 2, 2.5, 5].some((b) => Math.abs(base - b) < 1e-9)) return d;
  }
  return 4;
}

function ejeY(svg, area, max, divisiones = divisionesRedondas(max)) {
  const g = crear('g', { class: 'axis' }, svg);
  for (let i = 0; i <= divisiones; i++) {
    const y = area.y(max * i / divisiones);
    crear('line', { x1: area.x0, x2: area.x1, y1: y, y2: y, class: 'gridline' }, g);
    texto(g, area.x0 - 8, y + 4, formato.format(Math.round(max * i / divisiones)), { 'text-anchor': 'end' });
  }
}

function etiquetasX(svg, area, etiquetas, cuantas) {
  const g = crear('g', { class: 'axis' }, svg);
  const cada = Math.max(1, Math.ceil(etiquetas.length / cuantas));
  etiquetas.forEach((e, i) => {
    const ultimo = i === etiquetas.length - 1;
    if (i % cada === 0 || (ultimo && i % cada >= cada / 2)) {
      texto(g, area.xi(i), area.y1 + 20, e, { 'text-anchor': 'middle' });
    }
  });
}

function marco(ancho, alto, n, max, m) {
  const x0 = m.l, x1 = ancho - m.r, y0 = m.t, y1 = alto - m.b;
  return {
    x0, x1, y0, y1,
    xi: (i) => x0 + ((x1 - x0) * i) / Math.max(n - 1, 1),
    y: (v) => y1 - ((y1 - y0) * v) / max,
  };
}

function trazo(area, valores) {
  return valores.map((v, i) => `${area.xi(i).toFixed(1)},${area.y(v).toFixed(1)}`).join(' ');
}

// Dibuja la línea y la anima "escribiéndose" de izquierda a derecha.
function curva(svg, puntos, clase, animar) {
  const linea = crear('polyline', { points: puntos, class: clase }, svg);
  if (animar) {
    const largo = linea.getTotalLength();
    linea.style.setProperty('--len', largo);
    linea.style.strokeDasharray = largo;
    linea.classList.add('draw');
  }
  return linea;
}

/**
 * Canal endémico: zonas por cuartiles de años anteriores y la curva del año.
 * q1, q2, q3 y casos son arreglos de 52 semanas.
 */
export function canal(contenedor, { q1, q2, q3, casos, animar = true }) {
  const angosto = (contenedor.clientWidth || 640) < 560;
  const { svg, ancho, alto } = lienzo(contenedor, angosto ? 300 : 420);
  const max = maximoBonito(Math.max(...casos, ...q3) * 1.08);
  const area = marco(ancho, alto, 52, max, { t: 26, r: 10, b: 30, l: 52 });

  // Zonas apiladas del canal y, encima, el exceso de casos sobre el canal.
  const banda = (abajo, arriba, clase) => {
    const sup = arriba.map((v, i) => `${area.xi(i)},${area.y(v)}`);
    const inf = abajo.map((v, i) => `${area.xi(i)},${area.y(v)}`).reverse();
    crear('polygon', { points: [...sup, ...inf].join(' '), class: clase }, svg);
  };
  const ceros = q1.map(() => 0);
  banda(q3, casos.map((v, i) => Math.max(v, q3[i])), 'z-epidemia');
  banda(q2, q3, 'z-alerta');
  banda(q1, q2, 'z-seguridad');
  banda(ceros, q1, 'z-exito');

  ejeY(svg, area, max);
  const semanas = casos.map((_, i) => `S${i + 1}`);
  etiquetasX(svg, area, semanas, angosto ? 5 : 9);

  curva(svg, trazo(area, casos), 'curve', animar);

  // Semanas en epidemia: un punto rojo sobre la curva.
  casos.forEach((v, i) => {
    if (v > q3[i]) crear('circle', { cx: area.xi(i), cy: area.y(v), r: angosto ? 2.6 : 3.4, class: 'outbreak' }, svg);
  });

  // Etiqueta del pico.
  const pico = Math.max(...casos);
  const i = casos.indexOf(pico);
  const ancla = i > 40 ? 'end' : i < 8 ? 'start' : 'middle';
  texto(svg, area.xi(i), area.y(pico) - 12, `Semana ${i + 1}: ${formato.format(pico)} casos`, { 'text-anchor': ancla, class: 'peak-label' });
}

/** Barras por año; las que superan el umbral se resaltan. */
export function barras(contenedor, etiquetas, valores, { umbral = Infinity } = {}) {
  const angosto = (contenedor.clientWidth || 640) < 480;
  const { svg, ancho, alto } = lienzo(contenedor, 280);
  const max = maximoBonito(Math.max(...valores));
  const m = { t: 24, r: 6, b: 30, l: 52 };
  const area = marco(ancho, alto, valores.length, max, m);
  ejeY(svg, area, max);

  const paso = (area.x1 - area.x0) / valores.length;
  valores.forEach((v, i) => {
    const x = area.x0 + i * paso + paso * 0.14;
    const caliente = v > umbral;
    const r = crear('rect', {
      x, y: area.y(v), width: paso * 0.72, height: area.y1 - area.y(v),
      class: caliente ? 'col hot' : 'col',
    }, svg);
    crear('title', {}, r).textContent = `${etiquetas[i]}: ${formato.format(v)} casos`;
    if (caliente) texto(svg, x + paso * 0.36, area.y(v) - 7, formato.format(v), { 'text-anchor': 'middle', class: 'bar-label' });
  });

  const g = crear('g', { class: 'axis' }, svg);
  const cada = angosto ? 5 : 3;
  etiquetas.forEach((e, i) => {
    const ultimo = i === etiquetas.length - 1;
    if (i % cada === 0 || (ultimo && i % cada >= 2)) {
      texto(g, area.x0 + i * paso + paso * 0.5, area.y1 + 20, e, { 'text-anchor': 'middle' });
    }
  });
}

/** Varias líneas sobre los mismos años. series: [{ valores, clase }]. */
export function lineas(contenedor, etiquetas, series) {
  const angosto = (contenedor.clientWidth || 640) < 480;
  const { svg, ancho, alto } = lienzo(contenedor, 260);
  const max = maximoBonito(Math.max(...series.flatMap((s) => s.valores)));
  const area = marco(ancho, alto, etiquetas.length, max, { t: 18, r: 12, b: 30, l: 52 });
  ejeY(svg, area, max);
  etiquetasX(svg, area, etiquetas, angosto ? 5 : 8);
  series.forEach((s) => crear('polyline', { points: trazo(area, s.valores), class: s.clase }, svg));
}

/** Gráfica pequeña para comparar la forma de cada historia. */
export function mini(contenedor, etiquetas, valores) {
  const { svg, ancho, alto } = lienzo(contenedor, 150);
  const max = maximoBonito(Math.max(...valores));
  const area = marco(ancho, alto, valores.length, max, { t: 22, r: 8, b: 24, l: 8 });

  const puntos = trazo(area, valores);
  crear('polygon', { points: `${area.xi(0)},${area.y1} ${puntos} ${area.xi(valores.length - 1)},${area.y1}`, class: 'area' }, svg);
  crear('polyline', { points: puntos, class: 'curve' }, svg);

  const pico = Math.max(...valores);
  const i = valores.indexOf(pico);
  const ancla = i > valores.length * 0.75 ? 'end' : i < valores.length * 0.25 ? 'start' : 'middle';
  texto(svg, area.xi(i), area.y(pico) - 8, `${etiquetas[i]}: ${formato.format(pico)}`, { 'text-anchor': ancla, class: 'peak-label' });

  const g = crear('g', { class: 'axis' }, svg);
  texto(g, area.x0, alto - 4, etiquetas[0], { 'text-anchor': 'start' });
  texto(g, area.x1, alto - 4, etiquetas.at(-1), { 'text-anchor': 'end' });
}
