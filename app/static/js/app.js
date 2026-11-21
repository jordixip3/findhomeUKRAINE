
let map = null;
let markers = [];
let allProperties = [];

document.addEventListener("DOMContentLoaded", () => {
  initMap();
  initCalculator();
  loadProperties();

  document.getElementById("search-btn")?.addEventListener("click", applyFilters);
  document.getElementById("subdivision-filter")?.addEventListener("change", applyFilters);
  document.getElementById("bedrooms-filter")?.addEventListener("change", applyFilters);
});

function initMap() {
  const container = document.getElementById("leaflet-map");
  if (!container) return;
  map = L.map('leaflet-map').setView(CONFIG.mapCenter, CONFIG.mapZoom);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);
}

function initCalculator() {
  const rentSlider = document.getElementById("rent-slider");
  const roomSlider = document.getElementById("roommates-slider");
  const rentDisp = document.getElementById("rent-display");
  const roomDisp = document.getElementById("roommates-display");
  const perPerson = document.getElementById("per-person-val");
  const savings = document.getElementById("savings-val");

  function update() {
    const rent = parseFloat(rentSlider.value);
    const rooms = parseInt(roomSlider.value);
    const pp = Math.round(rent / rooms);
    const save = Math.round(rent * 0.45);

    rentDisp.textContent = Number(rent).toLocaleString() + " " + CONFIG.currency;
    roomDisp.textContent = rooms + " чел.";
    perPerson.textContent = Number(pp).toLocaleString() + " " + CONFIG.currency;
    savings.textContent = "~" + Number(save).toLocaleString() + " " + CONFIG.currency;
  }

  rentSlider?.addEventListener("input", update);
  roomSlider?.addEventListener("input", update);
}

async function loadProperties() {
  try {
    const res = await fetch("api/v1/properties");
    allProperties = await res.json();
    renderProperties(allProperties);
  } catch (e) {
    console.error("Error loading properties:", e);
  }
}

function renderProperties(props) {
  const grid = document.getElementById("properties-grid");
  if (!grid) return;
  grid.innerHTML = "";

  if (markers.length && map) {
    markers.forEach(m => map.removeLayer(m));
    markers = [];
  }

  if (!props.length) {
    grid.innerHTML = "<p class='no-results'>Объекты по заданным критериям не найдены.</p>";
    return;
  }

  props.forEach(p => {
    const rpp = Math.round(p.total_rent / Math.max(1, p.bedrooms));
    const card = document.createElement("div");
    card.className = "property-card";
    card.innerHTML = `
      <div class="prop-img-box">
        <img src="static/images/hero-home.png" alt="${p.title}">
        <span class="portal-tag">${p.source_portal || 'Verified'}</span>
      </div>
      <div class="prop-info">
        <h3>${p.title}</h3>
        <p class="prop-address">📍 ${p.address || p.city}</p>
        <div class="prop-specs">
          <span>🛏️ ${p.bedrooms} комн.</span>
          <span>🚿 ${p.bathrooms} сан.</span>
          <span>📐 ${p.surface} m²</span>
        </div>
        <div class="prop-price-box">
          <div>
            <span class="price-val">${rpp.toLocaleString()} ${CONFIG.currency}</span>
            <span class="price-sub">/чел/мес</span>
          </div>
          <a href="https://wa.me/34603331391?text=${encodeURIComponent('Здравствуйте! Интересует квартира: ' + p.title)}" target="_blank" class="btn-visit-wsp">
            Записаться
          </a>
        </div>
      </div>
    `;
    grid.appendChild(card);

    if (map && p.latitude && p.longitude) {
      const m = L.marker([p.latitude, p.longitude]).addTo(map);
      m.bindPopup(`<b>${p.title}</b><br>${p.address}<br><b>${rpp.toLocaleString()} ${CONFIG.currency}/чел</b>`);
      markers.push(m);
    }
  });
}

function applyFilters() {
  const sub = document.getElementById("subdivision-filter")?.value;
  const bed = document.getElementById("bedrooms-filter")?.value;
  const budget = parseFloat(document.getElementById("budget-filter")?.value);

  const filtered = allProperties.filter(p => {
    if (sub && p.subdivision_code !== sub) return false;
    if (bed && p.bedrooms < parseInt(bed)) return false;
    if (budget && p.total_rent > budget) return false;
    return true;
  });

  renderProperties(filtered);
}
