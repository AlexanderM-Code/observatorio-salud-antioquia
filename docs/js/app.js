// Carga los datos que genera el pipeline y dibuja la página.
import { canal, barras, lineas, mini, formato } from './charts.js';

const reducirMovimiento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const cargar = (nombre) => fetch(`data/${nombre}.json`).then((r) => {
  if (!r.ok) throw new Error(`No se pudo cargar ${nombre}.json`);
  return r.json();
});

// Contexto de cada enfermedad en las gráficas pequeñas.
const NOTAS = {
  '210': 'Epidemias en 2010 y 2016. Medellín concentra la mitad de los casos.',
  '490': 'Cayó casi 90\u00a0% entre 2010 y 2017. Se concentra en el Bajo Cauca.',
  '470': 'Sigue a la malaria vivax, con su pico también en 2010.',
  '831': 'Los casos caen 69\u00a0% en 2020, el año en que cerraron los colegios.',
  '820': 'La única con tendencia al alza: 2022 es su año con más casos.',
  '420': 'Enfermedad rural; hoy registra cerca de un tercio de su pico de 2010.',
};

// Años usados como base del canal: hasta 7 anteriores, mínimo 5.
// 2007 se excluye porque la fuente solo tiene ese año incompleto.
const PRIMER_ANIO_COMPLETO = 2008;
const ANIOS_BASE = 7;
const MINIMO_BASE = 5;

function cuartil(valores, q) {
  const v = [...valores].sort((a, b) => a - b);
  const pos = (v.length - 1) * q;
  const base = Math.floor(pos);
  const resto = pos - base;
  return v[base + 1] !== undefined ? v[base] + resto * (v[base + 1] - v[base]) : v[base];
}

/** Calcula el canal endémico de un año a partir de la serie semanal. */
function canalEndemico(semanal, anio) {
  const base = Object.keys(semanal)
    .map(Number)
    .filter((a) => a >= PRIMER_ANIO_COMPLETO && a < anio && a >= anio - ANIOS_BASE);
  if (base.length < MINIMO_BASE || !semanal[anio]) return null;

  const semanas = Array.from({ length: 52 }, (_, s) => s);
  const porSemana = semanas.map((s) => base.map((a) => semanal[a][s] ?? 0));
  return {
    base,
    q1: porSemana.map((v) => cuartil(v, 0.25)),
    q2: porSemana.map((v) => cuartil(v, 0.5)),
    q3: porSemana.map((v) => cuartil(v, 0.75)),
    casos: semanas.map((s) => semanal[anio][s] ?? 0),
  };
}

async function iniciar() {
  const [resumen, porAnio, semanal, top] = await Promise.all(
    ['resumen', 'eventos_por_anio', 'semanal', 'top_municipios'].map(cargar),
  );

  document.getElementById('casos-total').textContent = formato.format(resumen.casos);
  document.getElementById('anio-inicio').textContent = resumen.anio_inicio;
  document.getElementById('anio-fin').textContent = resumen.anio_fin;
  document.getElementById('actualizado').textContent = resumen.actualizado;

  const anios = porAnio.anios.map(String);
  const serie = (codigo) => porAnio.eventos.find((e) => e.codigo === codigo);

  // --- 1. Canal endémico del dengue (la parte interactiva) ---
  const dengueSemanal = semanal['210'] || {};
  const aniosConCanal = Object.keys(dengueSemanal).map(Number).filter((a) => canalEndemico(dengueSemanal, a));
  const contenedorAnios = document.getElementById('years');
  contenedorAnios.innerHTML = aniosConCanal
    .map((a) => `<button class="year" type="button" data-anio="${a}" aria-pressed="false">${a}</button>`)
    .join('');

  let anioActual = aniosConCanal.includes(2016) ? 2016 : aniosConCanal.at(-1);

  const dibujarCanal = (animar) => {
    const datos = canalEndemico(dengueSemanal, anioActual);
    contenedorAnios.querySelectorAll('.year').forEach((b) =>
      b.setAttribute('aria-pressed', String(Number(b.dataset.anio) === anioActual)));
    canal(document.getElementById('chart-canal'), { ...datos, animar: animar && !reducirMovimiento });

    const enEpidemia = datos.casos.filter((v, i) => v > datos.q3[i]).length;
    const pico = Math.max(...datos.casos);
    const semanaPico = datos.casos.indexOf(pico) + 1;
    const desde = Math.min(...datos.base), hasta = Math.max(...datos.base);
    document.getElementById('veredicto').innerHTML = enEpidemia === 0
      ? `En ${anioActual}, ninguna semana superó el canal calculado con ${desde}–${hasta}. El pico fue la semana ${semanaPico}, con ${formato.format(pico)} casos.`
      : `En ${anioActual}, <strong>${enEpidemia} de 52 semanas</strong> estuvieron en zona de epidemia frente a ${desde}–${hasta}. El pico fue la semana ${semanaPico}, con ${formato.format(pico)} casos.`;
  };

  contenedorAnios.addEventListener('click', (e) => {
    const boton = e.target.closest('.year');
    if (!boton) return;
    anioActual = Number(boton.dataset.anio);
    dibujarCanal(true);
  });

  // --- 2. Dengue por año ---
  const dengue = serie('210');
  const dibujarDengue = () => barras(document.getElementById('chart-dengue-anual'), anios, dengue.casos, { umbral: 20000 });

  // --- 3. Malaria ---
  const dibujarMalaria = () => lineas(document.getElementById('chart-malaria'), anios, [
    { valores: serie('490').casos, clase: 'line-vivax' },
    { valores: serie('470').casos, clase: 'line-falciparum' },
  ]);
  const ranking = top['490'] || [];
  const maximo = Math.max(...ranking.map((r) => r.casos), 1);
  document.getElementById('top-malaria').innerHTML = ranking.map((r) => `
    <li>
      <span>${r.municipio}</span>
      <span class="fill" style="transform: scaleX(${(r.casos / maximo).toFixed(3)})"></span>
      <span class="n">${formato.format(r.casos)}</span>
    </li>`).join('');

  // --- 4. Seis enfermedades en gráficas pequeñas ---
  const multiples = document.getElementById('multiples');
  multiples.innerHTML = porAnio.eventos.map((e) => `
    <article class="mini">
      <h3>${e.nombre}</h3>
      <div class="plot" data-codigo="${e.codigo}" role="img" aria-label="Casos por año de ${e.nombre}"></div>
      <p>${NOTAS[e.codigo] || ''}</p>
    </article>`).join('');
  const dibujarMultiples = () => multiples.querySelectorAll('.plot').forEach((el) =>
    mini(el, anios, serie(el.dataset.codigo).casos));

  const dibujarTodo = (animar) => {
    dibujarCanal(animar);
    dibujarDengue();
    dibujarMalaria();
    dibujarMultiples();
  };
  dibujarTodo(true);

  // Al cambiar el ancho de la ventana se redibuja, sin animación.
  let espera, anchoPrevio = window.innerWidth;
  window.addEventListener('resize', () => {
    if (window.innerWidth === anchoPrevio) return;
    anchoPrevio = window.innerWidth;
    clearTimeout(espera);
    espera = setTimeout(() => dibujarTodo(false), 150);
  });
}

iniciar().catch((error) => {
  console.error(error);
  document.querySelectorAll('.plot').forEach((el) => {
    el.innerHTML = '<p>No se pudieron cargar los datos. Recarga la página.</p>';
  });
});
