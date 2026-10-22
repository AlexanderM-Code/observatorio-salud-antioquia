// Carga los datos que genera el pipeline y dibuja la página.
import { barras, lineas, formato } from './charts.js';

const cargar = (nombre) => fetch(`data/${nombre}.json`).then((r) => {
  if (!r.ok) throw new Error(`No se pudo cargar ${nombre}.json`);
  return r.json();
});

// Notas de contexto que aparecen al explorar cada evento.
const NOTAS = {
  '210': 'Epidemias en 2010 y 2016. Medellín concentra cerca de la mitad de los casos.',
  '490': 'Caída de casi 90 % entre 2010 y 2017; se concentra en el Bajo Cauca.',
  '470': 'Sigue la misma tendencia de la malaria vivax, con un pico en 2010.',
  '831': 'Los casos caen cerca de 70 % en 2020, cuando los colegios cerraron por la pandemia.',
  '820': 'Es el único evento destacado con tendencia al alza: 2022 es el año con más casos.',
  '420': 'Enfermedad rural transmitida por un insecto; hoy registra cerca de un tercio de los casos de su pico de 2010.',
};

async function iniciar() {
  const [resumen, porAnio, semanal, top] = await Promise.all(
    ['resumen', 'eventos_por_anio', 'semanal', 'top_municipios'].map(cargar),
  );

  // Resumen
  document.getElementById('casos-total').textContent = formato.format(resumen.casos);
  document.getElementById('anio-inicio').textContent = resumen.anio_inicio;
  document.getElementById('anio-fin').textContent = resumen.anio_fin;
  document.getElementById('actualizado').textContent = resumen.actualizado;

  const anios = porAnio.anios.map(String);
  const serie = (codigo) => porAnio.eventos.find((e) => e.codigo === codigo);

  // Dengue por año, con las dos epidemias resaltadas
  const dengue = serie('210');
  const picos = anios.filter((a, i) => dengue.casos[i] > 20000);
  barras(document.getElementById('chart-dengue-anual'), anios, dengue.casos, { resaltar: picos });

  // Curva semanal del dengue con selector de año
  const selector = document.getElementById('anio-semanal');
  const aniosSemanales = Object.keys(semanal['210'] || {}).sort();
  selector.innerHTML = aniosSemanales.map((a) => `<option value="${a}">${a}</option>`).join('');
  selector.value = aniosSemanales.includes('2016') ? '2016' : aniosSemanales.at(-1);
  const dibujarSemanal = () => {
    let valores = semanal['210'][selector.value];
    // La semana 53 solo existe en algunos años: se omite si está vacía.
    if (valores.length === 53 && valores[52] === 0) valores = valores.slice(0, 52);
    const semanas = valores.map((_, i) => `S${i + 1}`);
    lineas(document.getElementById('chart-dengue-semanal'), semanas, [{ valores }], { area: true, marcarMaximo: true });
  };
  selector.addEventListener('change', dibujarSemanal);
  dibujarSemanal();

  // Malaria: vivax y falciparum
  lineas(document.getElementById('chart-malaria'), anios, [
    { valores: serie('490').casos },
    { valores: serie('470').casos },
  ]);

  // Ranking de municipios con malaria vivax
  const ranking = top['490'] || [];
  const maximo = Math.max(...ranking.map((r) => r.casos), 1);
  document.getElementById('top-malaria').innerHTML = ranking.map((r) => `
    <li>
      <span>${r.municipio}</span>
      <span class="barra" style="transform: scaleX(${(r.casos / maximo).toFixed(3)})"></span>
      <span class="valor">${formato.format(r.casos)}</span>
    </li>`).join('');

  // Explorador por evento
  const picker = document.getElementById('picker');
  picker.innerHTML = porAnio.eventos.map((e, i) =>
    `<button class="chip" type="button" data-codigo="${e.codigo}" aria-pressed="${i === 0}">${e.nombre}</button>`,
  ).join('');
  const explorar = (codigo) => {
    const evento = serie(codigo);
    picker.querySelectorAll('.chip').forEach((c) => c.setAttribute('aria-pressed', String(c.dataset.codigo === codigo)));
    document.getElementById('explorar-titulo').textContent = `${evento.nombre}: casos por año en Antioquia`;
    document.getElementById('explorar-nota').textContent = NOTAS[codigo] || '';
    lineas(document.getElementById('chart-explorar'), anios, [{ valores: evento.casos }], { area: true, marcarMaximo: true });
  };
  picker.addEventListener('click', (e) => {
    const boton = e.target.closest('.chip');
    if (boton) explorar(boton.dataset.codigo);
  });
  explorar(porAnio.eventos[0].codigo);

  // Al cambiar el tamaño de la ventana, se redibujan las gráficas.
  let espera;
  window.addEventListener('resize', () => {
    clearTimeout(espera);
    espera = setTimeout(() => {
      barras(document.getElementById('chart-dengue-anual'), anios, dengue.casos, { resaltar: picos });
      dibujarSemanal();
      lineas(document.getElementById('chart-malaria'), anios, [
        { valores: serie('490').casos },
        { valores: serie('470').casos },
      ]);
      explorar(picker.querySelector('[aria-pressed="true"]').dataset.codigo);
    }, 150);
  });
}

iniciar().catch((error) => {
  console.error(error);
  document.querySelectorAll('.chart-area').forEach((el) => {
    el.innerHTML = '<p class="note">No se pudieron cargar los datos. Recarga la página.</p>';
  });
});
