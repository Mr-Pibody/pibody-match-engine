let state = null;
let kindFilter = "all";
let selectedEntityId = null;

const VIEW_TITLES = {
  discover: ["Need Discovery — Exprimer un Besoin", "Privacy-by-Design : les identites restent protegees jusqu'a la validation d'un match mutuel"],
  explorer: ["Universal Match Explorer & Skill Path", "Analyse 6 dimensions, reciprocite mutuelle et parcours de progression"],
  graph: ["Pibody Relationship Graph", "Reseau de relations entre besoins, competences, mentors et projets"],
  team: ["Team & Opportunity Composer", "Composition intelligente d'equipes complementaires"],
  governance: ["Optimisation Combinatoire & Gouvernance", "Simulation multicritere, Hongrois, Gale-Shapley et audit SQLite"],
};

const DIM_LABELS = {
  pertinence_besoin: "Pertinence du besoin",
  competences: "Competences",
  complementarite: "Complementarite",
  disponibilite: "Disponibilite",
  alignement_objectifs: "Alignement objectifs",
  reciprocite: "Reciprocite mutuelle",
};

function switchView(id) {
  document.querySelectorAll(".view").forEach((el) => el.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach((el) => el.classList.remove("active"));
  document.getElementById(`view-${id}`).classList.add("active");
  document.querySelector(`.nav-item[data-view="${id}"]`).classList.add("active");
  document.getElementById("page-title").textContent = VIEW_TITLES[id][0];
  document.getElementById("page-sub").textContent = VIEW_TITLES[id][1];
}

function toggleTheme() {
  const root = document.documentElement;
  root.setAttribute("data-theme", root.getAttribute("data-theme") === "dark" ? "light" : "dark");
}

function openModal(id) { document.getElementById(id).classList.add("open"); }
function closeModal(id) { document.getElementById(id).classList.remove("open"); }

async function submitConsent(accepted) {
  state = await (await fetch("/api/consent", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ accepted, scope: "storage_and_matching" }) })).json();
  renderAll();
}

async function submitConsent(accepted) {
  state = await (await fetch("/api/consent", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ accepted, scope: "storage_and_matching" }) })).json();
  renderAll();
}

async function submitConsent(accepted) {
  const res = await fetch("/api/consent", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ accepted, scope: "storage_and_matching" }),
  });
  state = await res.json();
  if (!accepted) {
    alert("Mode lecture seule active : aucune donnee personnelle ne sera enregistree sans votre accord.");
  }
  renderAll();
}

function syncConsentBanner() {
  const bannerEl = document.getElementById("consent-banner");
  if (!bannerEl) return;
  bannerEl.style.display = state.consent && state.consent.accepted ? "none" : "flex";
}

function buildClarificationChip(q) {
  const lower = q.toLowerCase();
  let answer = "Inclure un profil UI/UX Design";
  let label = "Ajouter : UI/UX Design";
  if (lower.includes("competence") || lower.includes("domaine")) {
    answer = "Competences : Python, Machine Learning";
    label = "Preciser : Python · IA";
  } else if (lower.includes("maturite")) {
    answer = "Niveau prototype fonctionnel";
    label = "Preciser : Prototype";
  } else if (lower.includes("disponibilite")) {
    answer = "Disponibilite 10h/semaine sur 1 mois";
    label = "Preciser : 10h/sem · 1 mois";
  }
  return `<button class="chip" onclick="refineWithAnswer('${answer}')">${label}</button>`;
}

async function loadState() {
  state = await (await fetch("/api/state")).json();
  if (state.active_need) {
    document.getElementById("need-input").value = state.active_need.raw_query;
  }
  renderAll();
}

async function loadSandbox() {
  state = await (await fetch("/api/sandbox/load", { method: "POST" })).json();
  renderAll();
}

async function resetSandbox() {
  state = await (await fetch("/api/sandbox/reset", { method: "POST" })).json();
  document.getElementById("need-input").value = "";
  selectedEntityId = null;
  renderAll();
}

function useScenario(text) {
  document.getElementById("need-input").value = text;
  runDiscovery();
}

async function runDiscovery() {
  const query = document.getElementById("need-input").value.trim();
  if (!query) return;
  const res = await fetch("/api/discover", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) return alert((await res.json()).error);
  state = await res.json();
  selectedEntityId = null;
  renderAll();
}

function refineWithAnswer(extra) {
  const box = document.getElementById("need-input");
  box.value = `${box.value.trim()} (${extra})`;
  runDiscovery();
}

function inspectEntity(entityId) {
  selectedEntityId = entityId;
  renderExplorer();
  switchView("explorer");
}

function setKindFilter(kind, btn) {
  kindFilter = kind;
  document.querySelectorAll(".filter-bar .chip").forEach((c) => c.classList.remove("active"));
  btn.classList.add("active");
  renderExplorer();
}

function renderAll() {
  const need = state.active_need;
  document.getElementById("active-universe-badge").textContent = need ? need.universe : "Mode Confidentiel";
  document.getElementById("vault-status").textContent =
    `${state.stored_entities_count} entite(s) en base SQLite protegee`;
  syncConsentBanner();
  renderDiscover();
  renderExplorer();
  renderGraph();
  renderTeam();
  renderGovernance();
}

function renderDiscover() {
  const need = state.active_need;
  const intelCard = document.getElementById("need-intelligence-card");
  const clarifCard = document.getElementById("clarification-card");
  const matchesGrid = document.getElementById("discover-matches");
  document.getElementById("unlock-counter").textContent =
    `${state.unlocked_matches_count} identite(s) revelee(s) sur ${state.stored_entities_count}`;

  if (!need) {
    intelCard.innerHTML = `
      <h2>Aucune requete active</h2>
      <p class="muted">
        La base demarre vierge sans donnees fictives. Enregistrez des profils, mentors ou projets via
        <strong>+ Enregistrer une entite</strong> (ou chargez le catalogue synthetique) puis exprimez votre besoin.
      </p>`;
    clarifCard.innerHTML = `
      <h2>Confidentialite Progressive</h2>
      <p class="muted">
        Les personnes et mentors sont stockes dans SQLite pour le calcul de compatibilite, mais restent
        pseudonymises (<em>Profil protege #01</em>) tant qu'aucun match mutuel pertinent n'est etabli.
      </p>`;
    matchesGrid.innerHTML = `<p class="muted">Exprimez un besoin ci-dessus pour lancer l'analyse.</p>`;
    return;
  }

  const skillsHtml = need.required_skills.length ? need.required_skills.map((s) => `<span class="badge-blue">${s}</span>`).join(" ") : `<span class="badge-amber">Aucune competence detectee</span>`;
  intelCard.innerHTML = `
    <div class="card-head">
      <h2>Need Intelligence — Structuration du Besoin</h2>
      <span class="badge-green">${need.intent}</span>
    </div>
    <p><strong>Objectif principal :</strong> ${need.primary_goal}</p>
    <p class="muted">${need.summary}</p>
    <div><strong>Competences detectees :</strong> ${skillsHtml}</div>
    <div style="margin-top:8px" class="muted">
      Taille cible : <strong>${need.team_size}</strong> · Disponibilite souhaitee : <strong>${need.requested_hours_week}h/sem</strong>
    </div>
  `;

  const qs = need.clarification_questions;
  clarifCard.innerHTML = `
    <div class="card-head">
      <h2>Clarification Intelligente</h2>
      <span class="badge-amber">${qs.length} precision(s)</span>
    </div>
    ${qs.length ? qs.map((q) => `
      <div style="margin-bottom:10px">
        <div style="font-size:0.86rem;margin-bottom:4px">${q}</div>
        ${buildClarificationChip(q)}
      </div>`).join("") : `<p class="muted">Votre demande est suffisamment precise pour une recommandation optimale.</p>`}
  `;

  const matches = state.universal_matches.slice(0, 6);
  matchesGrid.innerHTML = matches.length ? matches.map((m) => `
    <div class="entity-card" onclick="inspectEntity('${m.entity_id}')">
      <div class="card-head" style="margin:0">
        <span class="badge-blue">${m.entity_kind}</span>
        <strong>${(m.combined_score * 100).toFixed(0)}%</strong>
      </div>
      <strong>${m.entity_name}</strong>
      <span class="muted" style="font-size:0.82rem">${m.headline}</span>
      <p style="margin:0;font-size:0.82rem">${m.explanation}</p>
      <div style="display:flex;gap:6px;flex-wrap:wrap">
        <span class="${m.identity_unlocked ? "badge-green" : "badge-amber"}">
          ${m.identity_unlocked ? "Identite revelee (Match)" : "Identite protegee"}
        </span>
        <span class="badge-blue">Reciprocite ${(m.reciprocity_score * 100).toFixed(0)}%</span>
        ${m.is_serendipitous ? `<span class="badge-purple">Passerelle inter-univers</span>` : ""}
      </div>
    </div>
  `).join("") : `<p class="muted">Aucune entite en base. Ajoutez des profils ou chargez le catalogue synthetique.</p>`;
}

function renderExplorer() {
  const list = state.universal_matches.filter(
    (m) => kindFilter === "all" || m.entity_kind === kindFilter
  );
  if (!selectedEntityId || !list.some((m) => m.entity_id === selectedEntityId)) {
    selectedEntityId = list.length ? list[0].entity_id : null;
  }

  document.getElementById("explorer-list").innerHTML = list.map((m) => `
    <div class="cand-item ${m.entity_id === selectedEntityId ? "selected" : ""}"
         onclick="selectedEntityId='${m.entity_id}'; renderExplorer();">
      <div>
        <strong>${m.entity_name}</strong>
        <div class="muted" style="font-size:0.78rem">${m.entity_kind} · ${m.identity_unlocked ? "Devoile" : "Protege"}</div>
      </div>
      <span class="badge-blue">${(m.combined_score * 100).toFixed(0)}%</span>
    </div>
  `).join("") || `<p class="muted">Aucune entite evaluee pour le moment.</p>`;

  const active = list.find((m) => m.entity_id === selectedEntityId);
  const pane = document.getElementById("explorer-detail");
  if (!active) { pane.innerHTML = `<p class="muted">Exprimez un besoin pour explorer les correspondances.</p>`; return; }

  const dimsHtml = Object.entries(active.dimensions).map(([k, v]) => `
    <div class="dim-box">
      <div style="font-size:0.78rem">${DIM_LABELS[k] || k} : <strong>${(v * 100).toFixed(0)}%</strong></div>
      <div class="track"><div class="fill" style="width:${(v * 100).toFixed(0)}%"></div></div>
    </div>
  `).join("");

  pane.innerHTML = `
    <div class="card-head">
      <div>
        <h2 style="margin:0">${active.entity_name}</h2>
        <span class="muted">${active.headline}</span>
      </div>
      <span class="${active.identity_unlocked ? "badge-green" : "badge-amber"}">
        ${active.identity_unlocked ? "Match confirme — Identite revelee" : "Identite masquee (score sous le seuil)"}
      </span>
    </div>
    <p>${active.explanation}</p>
    <div class="dim-grid">${dimsHtml}</div>
    <div class="grid-2" style="margin-top:10px">
      <div>
        <strong>Competences alignees :</strong>
        <div>${active.matched_skills.map((s) => `<span class="badge-green">${s}</span>`).join(" ") || "Aucune"}</div>
      </div>
      <div>
        <strong>Competences a completer :</strong>
        <div>${active.missing_skills.map((s) => `<span class="badge-amber">${s}</span>`).join(" ") || "Aucune lacune"}</div>
      </div>
    </div>
  `;

  document.getElementById("skill-pathways").innerHTML = state.skill_pathways.map((p) => `
    <div class="entity-card">
      <div class="card-head" style="margin:0">
        <span class="badge-amber">Lacune : ${p.missing_skill}</span>
        <span class="badge-green">+${Math.round(p.projected_gain * 100)}%</span>
      </div>
      <div style="font-size:0.84rem"><strong>1. Ressource :</strong> ${p.resource_name}</div>
      <div style="font-size:0.84rem"><strong>2. Mentor :</strong> ${p.mentor_name}</div>
      <div style="font-size:0.84rem"><strong>3. Pratique :</strong> ${p.practice_project}</div>
      <p class="muted" style="margin:0;font-size:0.8rem">${p.rationale}</p>
    </div>
  `).join("");
}

function renderGraph() {
  const { nodes, links } = state.relationship_graph;
  if (!nodes.length) {
    document.getElementById("graph-canvas").innerHTML = `<p class="muted">Aucun graphe actif tant qu'aucun besoin n'est analyse.</p>`;
    document.getElementById("serendipity-panel").innerHTML = `<h2>Discovery Intelligence</h2><p class="muted">Lancez une recherche pour visualiser les passerelles.</p>`;
    return;
  }
  const maskedNames = Object.fromEntries(state.universal_matches.map((m) => [m.entity_id, m.entity_name]));
  const cx = 310, cy = 190;
  const pos = { need_root: [cx, cy] };
  const others = nodes.filter((n) => n.id !== "need_root");
  others.forEach((n, idx) => {
    const angle = (2 * Math.PI * idx) / Math.max(1, others.length);
    const radius = n.type === "skill" ? 105 : 165;
    pos[n.id] = [cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius];
  });

  const colors = { need: "#2563eb", skill: "#16a34a", mentor: "#9333ea", personne: "#0284c7", projet: "#d97706", communaute: "#db2777", formation_ressource: "#0d9488" };
  const linesSvg = links.map((l) => {
    const a = pos[l.source], b = pos[l.target];
    if (!a || !b) return "";
    return `<line x1="${a[0]}" y1="${a[1]}" x2="${b[0]}" y2="${b[1]}" stroke="#64748b" stroke-opacity="0.45" stroke-width="1.5"/>`;
  }).join("");

  const nodesSvg = nodes.map((n) => {
    const [x, y] = pos[n.id];
    const r = n.id === "need_root" ? 22 : n.type === "skill" ? 13 : 16;
    const fill = colors[n.type] || "#3b82f6";
    const label = maskedNames[n.id] || n.label;
    return `<g style="cursor:pointer" onclick="if('${n.id}'.startsWith('ent_'))inspectEntity('${n.id}')">` +
      `<circle cx="${x}" cy="${y}" r="${r}" fill="${fill}" />` +
      `<text x="${x}" y="${y + r + 13}" text-anchor="middle" font-size="10.5" fill="currentColor">${label}</text></g>`;
  }).join("");

  document.getElementById("graph-canvas").innerHTML =
    `<svg width="620" height="390" viewBox="0 0 620 390">${linesSvg}${nodesSvg}</svg>`;

  const serendip = state.universal_matches.filter((m) => m.is_serendipitous);
  document.getElementById("serendipity-panel").innerHTML = `
    <div class="card-head">
      <h2>Discovery Intelligence</h2>
      <span class="badge-purple">${serendip.length} passerelle(s)</span>
    </div>
    <p class="muted">Connexions inattendues reliant plusieurs univers ou domaines complementaires :</p>
    ${serendip.map((m) => `
      <div class="entity-card" style="margin-bottom:10px" onclick="inspectEntity('${m.entity_id}')">
        <strong>${m.entity_name} (${m.entity_kind})</strong>
        <span style="font-size:0.82rem">${m.discovery_reason}</span>
      </div>`).join("") || `<p class="muted">Toutes les correspondances sont dans l'univers principal.</p>`}
  `;
}

function renderTeam() {
  const t = state.team_composition;
  if (!t) {
    document.getElementById("team-summary-card").innerHTML = `<h2>Team Composer</h2><p class="muted">Analysez un besoin de projet pour assembler une equipe complementaire.</p>`;
    document.getElementById("team-members-grid").innerHTML = "";
    return;
  }
  const maskedNames = Object.fromEntries(state.universal_matches.map((m) => [m.entity_id, m.entity_name]));
  document.getElementById("team-summary-card").innerHTML = `
    <div class="card-head">
      <h2>Equipe Complementaire Recommandee (${t.members.length} membres)</h2>
      <span class="badge-green">Score d'equipe : ${(t.overall_score * 100).toFixed(0)}%</span>
    </div>
    <p>${t.rationale}</p>
    <div style="display:flex;gap:14px;flex-wrap:wrap">
      <span>Couverture des besoins : <strong>${(t.collective_coverage * 100).toFixed(0)}%</strong></span>
      <span>Indice de synergie : <strong>${(t.synergy_score * 100).toFixed(0)}%</strong></span>
      <span>Competences couvertes : <strong>${t.covered_skills.join(", ") || "Aucune"}</strong></span>
    </div>
  `;

  document.getElementById("team-members-grid").innerHTML = t.members.map((m) => `
    <div class="entity-card" onclick="inspectEntity('${m.entity_id}')">
      <div class="card-head" style="margin:0">
        <span class="badge-blue">${m.entity_kind}</span>
        <strong>${(m.combined_score * 100).toFixed(0)}%</strong>
      </div>
      <strong>${maskedNames[m.entity_id] || m.entity_name}</strong>
      <span class="muted" style="font-size:0.82rem">${m.headline}</span>
    </div>
  `).join("");
}

function renderGovernance() {
  const hList = state.hungarian.assignments;
  document.getElementById("hungarian-avg").textContent = `Moyenne : ${(state.hungarian.average_score * 100).toFixed(1)}%`;
  document.getElementById("hungarian-table").innerHTML =
    `<tr><th>Profil</th><th>Mission</th><th>Score</th></tr>` +
    (hList.length ? hList.map((a) => `<tr><td>${a.profile_name}</td><td>${a.opportunity_title}</td><td><strong>${(a.breakdown.total_score * 100).toFixed(1)}%</strong></td></tr>`).join("") : `<tr><td colspan="3" class="muted">Aucune affectation active.</td></tr>`);

  const gsList = state.gale_shapley.assignments;
  document.getElementById("gs-stable").textContent = state.gale_shapley.is_stable ? "Stable (0 blocage)" : "Instable";
  document.getElementById("gs-table").innerHTML =
    `<tr><th>Profil</th><th>Mission</th><th>Score</th></tr>` +
    (gsList.length ? gsList.map((a) => `<tr><td>${a.profile_name}</td><td>${a.opportunity_title}</td><td><strong>${(a.breakdown.total_score * 100).toFixed(1)}%</strong></td></tr>`).join("") : `<tr><td colspan="3" class="muted">Aucun appariement active.</td></tr>`);

  document.getElementById("fairness-badge").textContent =
    `Anonymisation neutre : ${state.fairness.anonymization_invariant ? "100% Valide" : "Alerte"}`;

  const pMap = Object.fromEntries(state.profiles.map((p) => [p.profile_id, p.display_name]));
  const oMap = Object.fromEntries(state.opportunities.map((o) => [o.opportunity_id, o.title]));
  document.getElementById("audit-table").innerHTML =
    `<tr><th>Date</th><th>Profil</th><th>Opportunite</th><th>Score</th><th>Decision</th><th>Justification</th></tr>` +
    (state.audits.length ? state.audits.map((a) => `
      <tr>
        <td>${new Date(a.timestamp_utc).toLocaleString("fr-FR")}</td>
        <td>${pMap[a.profile_id] || a.profile_id}</td>
        <td>${oMap[a.opportunity_id] || a.opportunity_id}</td>
        <td>${(a.total_score * 100).toFixed(1)}%</td>
        <td>${a.decision}</td>
        <td>${a.reviewer_note}</td>
      </tr>`).join("") : `<tr><td colspan="6" class="muted">Aucune decision enregistree.</td></tr>`);
}

function applyPreset(s, o, e, r) {
  document.getElementById("w-skills").value = s.toFixed(2);
  document.getElementById("w-obj").value = o.toFixed(2);
  document.getElementById("w-exp").value = e.toFixed(2);
  document.getElementById("w-req").value = r.toFixed(2);
  recalculate();
}

async function recalculate() {
  const res = await fetch("/api/evaluate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      skills: +document.getElementById("w-skills").value,
      objectives: +document.getElementById("w-obj").value,
      experience: +document.getElementById("w-exp").value,
      requirements: +document.getElementById("w-req").value,
      strict_mandatory: document.getElementById("strict-mode").checked,
    }),
  });
  if (!res.ok) return alert((await res.json()).error);
  state = await res.json();
  renderGovernance();
}

async function submitEntity(ev) {
  ev.preventDefault();
  const fd = new FormData(ev.target);
  const data = Object.fromEntries(fd.entries());
  data.open_to_mentor = fd.get("open_to_mentor") === "true";
  const res = await fetch("/api/entities", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    alert(err.error || "Action bloquee : veuillez accepter la politique de confidentialite.");
    return;
  }
  if (!res.ok) return alert((await res.json()).error);
  state = await res.json();
  ev.target.reset();
  closeModal("modal-entity");
  renderAll();
}

loadState();


