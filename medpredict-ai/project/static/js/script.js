// ---------- Data ----------
const ALL_SYMPTOMS = JSON.parse(document.getElementById('symptomData').textContent);
let selectedSymptoms = []; // array of {value, label}

// ---------- Elements ----------
const input = document.getElementById('symptomInput');
const dropdown = document.getElementById('symptomDropdown');
const chipsContainer = document.getElementById('selectedChips');
const predictBtn = document.getElementById('predictBtn');
const resultPlaceholder = document.getElementById('resultPlaceholder');
const resultContent = document.getElementById('resultContent');

// ---------- Dropdown rendering ----------
function renderDropdown(filter = '') {
  const query = filter.trim().toLowerCase();
  const selectedValues = new Set(selectedSymptoms.map(s => s.value));

  let matches = ALL_SYMPTOMS.filter(s => s.label.toLowerCase().includes(query));
  matches = matches.slice(0, 40);

  if (matches.length === 0) {
    dropdown.innerHTML = `<div class="symptom-option disabled">No symptoms found</div>`;
  } else {
    dropdown.innerHTML = matches.map(s => {
      const isSelected = selectedValues.has(s.value);
      return `<div class="symptom-option ${isSelected ? 'disabled' : ''}" data-value="${s.value}" data-label="${s.label}">
                ${isSelected ? '✓ ' : ''}${s.label}
              </div>`;
    }).join('');
  }
  dropdown.classList.add('open');
}

input.addEventListener('focus', () => renderDropdown(input.value));
input.addEventListener('input', () => renderDropdown(input.value));

document.addEventListener('click', (e) => {
  if (!e.target.closest('.symptom-search')) {
    dropdown.classList.remove('open');
  }
});

dropdown.addEventListener('click', (e) => {
  const opt = e.target.closest('.symptom-option');
  if (!opt || opt.classList.contains('disabled')) return;
  addSymptom(opt.dataset.value, opt.dataset.label);
  input.value = '';
  renderDropdown('');
  input.focus();
});

function addSymptom(value, label) {
  if (selectedSymptoms.some(s => s.value === value)) return;
  selectedSymptoms.push({ value, label });
  renderChips();
}

function removeSymptom(value) {
  selectedSymptoms = selectedSymptoms.filter(s => s.value !== value);
  renderChips();
}

function renderChips() {
  chipsContainer.innerHTML = selectedSymptoms.map(s => `
    <div class="chip">
      ${s.label}
      <button type="button" data-value="${s.value}" aria-label="Remove ${s.label}">✕</button>
    </div>
  `).join('');

  chipsContainer.querySelectorAll('button').forEach(btn => {
    btn.addEventListener('click', () => removeSymptom(btn.dataset.value));
  });
}

// ---------- Predict ----------
predictBtn.addEventListener('click', async () => {
  if (selectedSymptoms.length === 0) {
    alert('Please select at least one symptom first.');
    return;
  }

  const modelChoice = document.querySelector('input[name="modelChoice"]:checked').value;

  predictBtn.disabled = true;
  predictBtn.innerHTML = 'Analyzing...';

  try {
    const res = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symptoms: selectedSymptoms.map(s => s.value),
        model: modelChoice
      })
    });
    const data = await res.json();

    if (!res.ok) {
      alert(data.error || 'Something went wrong. Please try again.');
      return;
    }

    renderResult(data);
  } catch (err) {
    alert('Could not reach the prediction server. Is the Flask app running?');
    console.error(err);
  } finally {
    predictBtn.disabled = false;
    predictBtn.innerHTML = 'Predict Disease <span>&rarr;</span>';
  }
});

function renderResult(data) {
  resultPlaceholder.style.display = 'none';
  resultContent.style.display = 'block';

  document.getElementById('diseaseName').textContent = data.final_prediction;
  document.getElementById('diseaseDescription').textContent = data.suggestion.description;

  const severity = data.suggestion.severity || 'medium';
  const badge = document.getElementById('severityBadge');
  badge.textContent = severity.charAt(0).toUpperCase() + severity.slice(1) + ' Concern';
  badge.className = 'badge ' + severity;

  // Model comparison cards
  const comparisonDiv = document.getElementById('modelComparison');
  comparisonDiv.innerHTML = '';
  const modelLabels = { random_forest: '🌲 Random Forest', xgboost: '⚡ XGBoost' };
  Object.entries(data.predictions).forEach(([key, val]) => {
    comparisonDiv.innerHTML += `
      <div class="model-result">
        <div class="mr-label">${modelLabels[key] || key}</div>
        <div class="mr-disease">${val.disease}</div>
        <div class="mr-conf">${val.confidence}% confidence</div>
      </div>`;
  });

  // Precautions
  const list = document.getElementById('precautionList');
  list.innerHTML = data.suggestion.precautions.map(p => `<li>${p}</li>`).join('');

  // Doctor note
  const doctorNote = document.getElementById('doctorNote');
  if (data.suggestion.doctor) {
    doctorNote.textContent = '👩‍⚕️ This condition typically warrants a consultation with a healthcare professional.';
    doctorNote.style.display = 'block';
  } else {
    doctorNote.textContent = '🏡 This is often manageable with self-care, but see a doctor if symptoms persist or worsen.';
    doctorNote.style.display = 'block';
  }

  resultContent.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
