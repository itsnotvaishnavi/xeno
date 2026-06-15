const samplePath = "/static/sample_data.json";
const seedStatus = document.getElementById("seedStatus");
const segmentSuggestion = document.getElementById("segmentSuggestion");
const messageDraftResult = document.getElementById("messageDraftResult");
const segmentStatus = document.getElementById("segmentStatus");
const campaignStatus = document.getElementById("campaignStatus");

async function loadSampleData() {
  const response = await fetch(samplePath);
  const payload = await response.json();
  const result = await fetch('/api/import-data', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }).then(r => r.json());

  seedStatus.textContent = `Loaded ${result.customers} customers and ${result.orders} orders.`;
  await refreshSegments();
  await refreshCampaignSummary();
}

async function suggestSegment() {
  const goal = document.getElementById("segmentGoal").value.trim();
  if (!goal) return;
  const res = await fetch('/api/ai/suggest-segment', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ goal }),
  }).then(r => r.json());

  segmentSuggestion.textContent = `${res.name}: ${JSON.stringify(res.criteria)} ${res.explanation || res.note || ''}`;
  document.getElementById('segmentName').value = res.name;
  document.getElementById('segmentCategory').value = res.criteria.category || '';
  document.getElementById('segmentMinSpend').value = res.criteria.min_total_spend ?? '';
  document.getElementById('segmentMaxDays').value = res.criteria.max_last_order_days ?? '';
  document.getElementById('segmentTag').value = res.criteria.tag ?? '';
}

async function draftMessage() {
  const brand = document.getElementById("messageBrand").value.trim();
  const goal = document.getElementById("messageGoal").value.trim();
  const channel = document.getElementById("messageChannel").value;
  if (!brand || !goal) return;
  const res = await fetch('/api/ai/draft-message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ brand, goal, channel }),
  }).then(r => r.json());

  messageDraftResult.innerHTML = `<strong>Subject:</strong> ${res.subject || '(not used)'}<br/><strong>Body:</strong> ${res.body}`;
  document.getElementById('campaignSubject').value = res.subject || '';
  document.getElementById('campaignBody').value = res.body || '';
}

async function saveSegment() {
  const payload = {
    name: document.getElementById('segmentName').value.trim() || 'Unnamed segment',
    criteria: {
      category: document.getElementById('segmentCategory').value.trim() || null,
      min_total_spend: document.getElementById('segmentMinSpend').value ? Number(document.getElementById('segmentMinSpend').value) : null,
      max_last_order_days: document.getElementById('segmentMaxDays').value ? Number(document.getElementById('segmentMaxDays').value) : null,
      tag: document.getElementById('segmentTag').value.trim() || null,
    },
  };
  const res = await fetch('/api/segments', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }).then(r => r.json());
  segmentStatus.textContent = `Saved segment ${res.name}.`;
  await refreshSegments();
}

async function refreshSegments() {
  const segments = await fetch('/api/segments').then(r => r.json());
  const segmentSelect = document.getElementById('campaignSegment');
  segmentSelect.innerHTML = '';
  segments.forEach((segment) => {
    const option = document.createElement('option');
    option.value = segment.id;
    option.textContent = `${segment.name} (${JSON.stringify(segment.criteria)})`;
    segmentSelect.appendChild(option);
  });
}

async function launchCampaign() {
  const payload = {
    name: document.getElementById('campaignName').value.trim() || 'Campaign',
    segment_id: Number(document.getElementById('campaignSegment').value),
    channel: document.getElementById('campaignChannel').value,
    subject: document.getElementById('campaignSubject').value.trim() || null,
    body: document.getElementById('campaignBody').value.trim(),
  };
  const res = await fetch('/api/campaigns', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }).then(r => r.json());
  campaignStatus.textContent = `Campaign launched with ${res.recipient_count} recipients.`;
  setTimeout(refreshCampaignSummary, 1200);
}

async function refreshCampaignSummary() {
  const campaigns = await fetch('/api/campaigns').then(r => r.json());
  const campaignTable = document.getElementById('campaignTable');
  campaignTable.innerHTML = '';
  campaigns.forEach((campaign) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${campaign.name}</td>
      <td>${campaign.channel}</td>
      <td>${campaign.metrics.queued || 0}</td>
      <td>${campaign.metrics.delivered || 0}</td>
      <td>${campaign.metrics.opened || 0}</td>
      <td>${campaign.metrics.clicked || 0}</td>
      <td>${campaign.metrics.converted || 0}</td>
    `;
    campaignTable.appendChild(row);
  });

  const comms = await fetch('/api/communications').then(r => r.json());
  const communicationTable = document.getElementById('communicationTable');
  communicationTable.innerHTML = '';
  comms.forEach((comm) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${comm.campaign_id}</td>
      <td>${comm.customer_id}</td>
      <td>${comm.channel}</td>
      <td>${comm.status}</td>
      <td>${comm.outcome || ''}</td>
    `;
    communicationTable.appendChild(row);
  });
}

window.addEventListener('load', async () => {
  document.getElementById('loadSampleData').addEventListener('click', loadSampleData);
  document.getElementById('suggestSegment').addEventListener('click', suggestSegment);
  document.getElementById('draftMessage').addEventListener('click', draftMessage);
  document.getElementById('saveSegment').addEventListener('click', saveSegment);
  document.getElementById('launchCampaign').addEventListener('click', launchCampaign);
  await refreshSegments();
  await refreshCampaignSummary();
});
