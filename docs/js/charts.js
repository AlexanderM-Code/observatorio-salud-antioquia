// Gráficas en SVG hechas a mano, sin librerías externas.
// Cada función recibe un contenedor y datos ya listos para dibujar.

const NS = 'http://www.w3.org/2000/svg';
const formato = new Intl.NumberFormat('es-CO');

function crear(tag, atributos = {}, padre) {
  const el = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(atributos)) el.setAttribute(k, v);
  if (padre) padre.appendChild(el);
  return el;
}

// Redondea el máximo del eje a un número "bonito" (1, 2, 5 × 10^n).
function maximoBonito(valor) {
  if (valor <= 0) return 1;
  const exp = Math.pow(10, Math.floor(Math.log10(valor)));
  const base = valor / exp;
  const paso = base <= 1 ? 1 : base <= 2 ? 2 : base <= 5 ? 5 : 10;
  return paso * exp;
}

// El ancho del dibujo es el ancho real del contenedor: así el texto conserva
// su tamaño en celular y en escritorio.
function anchoDe(contenedor) {
  return Math.max(300, Math.round(contenedor.clientWidth || 640));
}

function lienzo(contenedor, ancho, alto) {
  contenedor.innerHTML = '';
  return crear('svg', { viewBox: `0 0 ${ancho} ${alto}`, preserveAspectRatio: 'xMidYMid meet' }, contenedor);
}

function ejeY(svg, m, ancho, alto, max) {
  const g = crear('g', { class: 'axis' }, svg);
  for (let i = 0; i <= 4; i++) {
    const valor = (max / 4) * i;
    const y = alto - m.b - ((alto - m.t - m.b) * i) / 4;
    crear('line', { x1: m.l, x2: ancho - m.r, y1: y, y2: y }, g);
    const t = crear('text', { x: m.l - 8, y: y + 4, 'text-anchor': 'end' }, g);
    t.textContent = formato.format(Math.round(valor));
  }
}

/** Barras verticales con etiquetas en el eje x y los picos resaltados. */
export function barras(contenedor, etiquetas, valores, { resaltar = [] } = {}) {
  const ancho = anchoDe(contenedor), alto = 280, m = { t: 20, r: 8, b: 30, l: 52 };
  const svg = lienzo(contenedor, ancho, alto);
  const max = maximoBonito(Math.max(...valores));
  ejeY(svg, m, ancho, alto, max);

  const paso = (ancho - m.l - m.r) / valores.length;
  valores.forEach((v, i) => {
    const h = ((alto - m.t - m.b) * v) / max;
    const x = m.l + i * paso + paso * 0.15;
    const destacado = resaltar.includes(etiquetas[i]);
    const barra = crear('rect', {
      x, y: alto - m.b - h, width: paso * 0.7, height: Math.max(h, 0), rx: 3,
      class: destacado || resaltar.length === 0 ? 'bar' : 'bar bar-muted',
    }, svg);
    crear('title', {}, barra).textContent = `${etiquetas[i]}: ${formato.format(v)} casos`;
    if (destacado) {
      const t = crear('text', { x: x + paso * 0.35, y: alto - m.b - h - 6, 'text-anchor': 'middle', class: 'peak' }, svg);
      t.textContent = formato.format(v);
    }
    const cadaBarra = ancho < 480 ? 5 : 3;
    if (i % cadaBarra === 0 || (i === valores.length - 1 && (valores.length - 1) % cadaBarra >= 2)) {
      const t = crear('text', { x: x + paso * 0.35, y: alto - 10, 'text-anchor': 'middle', class: 'label' }, svg);
      t.textContent = etiquetas[i];
    }
  });
}

/** Líneas (una o varias series) sobre un eje x de etiquetas. */
export function lineas(contenedor, etiquetas, series, { area = false, marcarMaximo = false } = {}) {
  const ancho = anchoDe(contenedor), alto = 280, m = { t: 22, r: 12, b: 30, l: 52 };
  const svg = lienzo(contenedor, ancho, alto);
  const max = maximoBonito(Math.max(...series.flatMap((s) => s.valores)));
  ejeY(svg, m, ancho, alto, max);

  const x = (i) => m.l + ((ancho - m.l - m.r) * i) / Math.max(etiquetas.length - 1, 1);
  const y = (v) => alto - m.b - ((alto - m.t - m.b) * v) / max;

  series.forEach((serie, s) => {
    const puntos = serie.valores.map((v, i) => `${x(i)},${y(v)}`).join(' ');
    if (area && s === 0) {
      crear('polygon', { points: `${x(0)},${y(0)} ${puntos} ${x(serie.valores.length - 1)},${y(0)}`, class: 'area' }, svg);
    }
    crear('polyline', { points: puntos, class: s === 0 ? 'line' : 'line line-2' }, svg);

    if (marcarMaximo && s === 0) {
      const vmax = Math.max(...serie.valores);
      const i = serie.valores.indexOf(vmax);
      crear('circle', { cx: x(i), cy: y(vmax), r: 4.5, class: 'dot' }, svg);
      const t = crear('text', { x: x(i), y: y(vmax) - 10, 'text-anchor': 'middle', class: 'peak' }, svg);
      t.textContent = `${etiquetas[i]}: ${formato.format(vmax)}`;
    }
  });

  const cada = Math.ceil(etiquetas.length / (ancho < 480 ? 5 : 8));
  const ultimo = etiquetas.length - 1;
  etiquetas.forEach((e, i) => {
    // La última etiqueta solo se muestra si no queda encima de la anterior.
    if (i % cada === 0 || (i === ultimo && ultimo % cada >= cada / 2)) {
      const t = crear('text', { x: x(i), y: alto - 10, 'text-anchor': 'middle', class: 'label' }, svg);
      t.textContent = e;
    }
  });
}

export { formato };
