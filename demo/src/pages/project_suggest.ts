import { apiPost } from '../api';

const DEFAULT_THEMES = [
  "Artificial Intelligence", "FinTech", "Healthcare", "Web3 / Blockchain",
  "EdTech", "Sustainability", "Cybersecurity", "IoT", "DSA", "ambulance", "hospital"
];

let state = {
  selectedDomains: [] as string[],
  errorMsg: '',
  loading: false,
  loadingStep: '',
  result: null as any,
  screen: 'form' as 'form' | 'results'
};

function setState(newState: Partial<typeof state>, render: () => void) {
  state = { ...state, ...newState };
  render();
}

export function renderProjectSuggest(container: HTMLElement) {
  const render = () => {
    if (state.screen === 'form') {
      container.innerHTML = getFormHTML();
      attachFormListeners(render);
    } else {
      container.innerHTML = getResultsHTML();
      attachResultsListeners(render);
    }
  };
  render();
}

function getFormHTML() {
  const themesHTML = DEFAULT_THEMES.map(t => {
    const isSel = state.selectedDomains.includes(t);
    return `<button class="ps-theme-btn ${isSel ? 'btn-outline selected' : 'btn-outline'}" data-theme="${t}">${t}</button>`;
  }).join(' ');

  const selDomainsHTML = state.selectedDomains.map(d =>
    `<span style="background: rgba(0, 255, 204, 0.1); color: #0891b2; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin-right: 6px; display: inline-block; margin-bottom: 4px; border: 1px solid rgba(0, 255, 204, 0.2);">${d}</span>`
  ).join('');

  return `
    <div class="fade-in" style="max-width: 680px; margin: 40px auto;">
      <h1 class="text-title"> Project Ideas Generator</h1>
      <p class="text-subtitle" style="margin-bottom: 32px;">
        Enter a theme or domain — the AI agent will suggest the best industry-grade projects for your resume and innovative ideas that win hackathons.
      </p>

      <div class="glass-card">
        <h3 style="color: #0891b2; margin-bottom: 20px;">Choose Your Theme</h3>
        
        <p style="font-size: 0.875rem; color: var(--text-muted); margin-bottom: 8px;">Select one or more themes:</p>
        <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px;">
          ${themesHTML}
        </div>

        ${state.selectedDomains.length > 0 ? `
          <div style="margin-bottom: 20px; padding: 10px; background: rgba(0, 136, 255, 0.05); border-radius: 8px; border: 1px solid rgba(0, 136, 255, 0.2);">
            <strong style="color: #0369a1; font-size: 0.875rem; margin-right: 8px;">Selected:</strong>
            ${selDomainsHTML}
          </div>
        ` : ''}

        ${state.errorMsg ? `<div class="alert-error" style="margin-bottom: 16px;">${state.errorMsg}</div>` : ''}

        <button id="ps-submit" class="btn-primary" style="width: 100%;" ${state.loading ? 'disabled' : ''}>
          ${state.loading ? ' Thinking... (may take 1-2 min)' : ' Generate Project Ideas'}
        </button>

        ${state.loading ? `
          <div class="alert-info" style="margin-top: 24px;">
            <strong>${state.loadingStep || 'Working...'}</strong><br>
            <span style="font-size: 0.8rem; color: var(--text-muted);">The AI is researching the best projects for your theme. Please keep this tab open!</span>
          </div>
        ` : ''}
      </div>
    </div>
  `;
}

function attachFormListeners(render: () => void) {
  document.querySelectorAll('.ps-theme-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const t = (e.target as HTMLElement).getAttribute('data-theme');
      if (t) {
        if (state.selectedDomains.includes(t)) {
          state.selectedDomains = state.selectedDomains.filter(x => x !== t);
        } else {
          state.selectedDomains.push(t);
        }
        render();
      }
    });
  });

  const submitBtn = document.getElementById('ps-submit');
  if (submitBtn) {
    submitBtn.addEventListener('click', async () => {
      if (state.selectedDomains.length === 0) {
        setState({ errorMsg: 'Please select at least one theme.' }, render);
        return;
      }
      setState({ loading: true, errorMsg: '', loadingStep: ' AI is brainstorming project ideas...' }, render);

      try {
        const res = await apiPost('/project-suggest/suggest', {
          themes: state.selectedDomains
        }, 300000);

        setState({
          loading: false,
          result: res,
          screen: 'results'
        }, render);
      } catch (err: any) {
        setState({ loading: false, errorMsg: err.message }, render);
      }
    });
  }
}

function getResultsHTML() {
  const r = state.result;
  if (!r) return '';

  const theme = r.theme || (r.themes && r.themes[0]) || 'Unknown';
  const resumeProjects = r.resume_projects || [];
  const hackathonProjects = r.hackathon_projects || [];

  const renderCard = (proj: any, accent: string, label: string, text: string, idx: number) => `
    <div class="glass-card" style="margin-bottom: 16px; border-top: 3px solid ${accent}; padding: 24px;">
      <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
        <div style="width: 32px; height: 32px; border-radius: 50%; background: ${accent}; display: flex; align-items: center; justify-content: center; font-weight: 800; color: #000;">${idx + 1}</div>
        <h3 style="font-size: 1.125rem; font-weight: 700; color: var(--text-main); margin: 0;">${proj.title}</h3>
      </div>
      <p style="font-size: 0.875rem; color: var(--text-muted); line-height: 1.6; margin-bottom: 12px;">${proj.description}</p>
      
      ${(proj.tech_stack || []).length > 0 ? `
        <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px;">
          ${proj.tech_stack.map((t: string) => `<span style="background: rgba(0, 136, 255, 0.1); border: 1px solid rgba(0, 136, 255, 0.2); border-radius: 20px; padding: 4px 12px; font-size: 0.75rem; color: #0369a1; font-weight: 600;">${t}</span>`).join('')}
        </div>
      ` : ''}

      ${text ? `
        <div style="padding: 10px 14px; border-radius: 10px; background: rgba(0, 255, 204, 0.06); border-left: 3px solid ${accent};">
          <div style="font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; color: ${accent}; font-weight: 700; margin-bottom: 4px;">${label}</div>
          <div style="font-size: 0.8rem; color: var(--text-muted);">${text}</div>
        </div>
      ` : ''}
    </div>
  `;

  return `
    <div class="fade-in" style="max-width: 900px; margin: 40px auto; padding-bottom: 60px;">
      <h1 class="text-title" style="margin-bottom: 8px;"> Project Ideas for: ${theme}</h1>
      <p style="color: #0891b2; font-size: 0.875rem; margin-bottom: 32px;">
        ${resumeProjects.length} resume projects • ${hackathonProjects.length} hackathon ideas
      </p>

      ${resumeProjects.length > 0 ? `
        <div style="margin-bottom: 40px;">
          <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px; border-bottom: 2px solid rgba(0,136,255,0.1); padding-bottom: 12px;">
            <div style="font-size: 1.5rem;"></div>
            <div>
              <h2 style="font-size: 1.5rem; color: var(--text-main);">Industry Resume Projects</h2>
              <div style="font-size: 0.8rem; color: var(--text-muted);">Projects that impress recruiters and demonstrate real engineering skills</div>
            </div>
          </div>
          ${resumeProjects.map((p: any, i: number) => renderCard(p, '#0088ff', 'Why Great for Resume', p.why_great_for_resume, i)).join('')}
        </div>
      ` : ''}

      ${hackathonProjects.length > 0 ? `
        <div style="margin-bottom: 40px;">
          <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px; border-bottom: 2px solid rgba(0,255,204,0.1); padding-bottom: 12px;">
            <div style="font-size: 1.5rem;"></div>
            <div>
              <h2 style="font-size: 1.5rem; color: var(--text-main);">Hackathon Winning Projects</h2>
              <div style="font-size: 0.8rem; color: var(--text-muted);">Creative ideas with wow-factor that judges love</div>
            </div>
          </div>
          ${hackathonProjects.map((p: any, i: number) => renderCard(p, '#00ffcc', 'Why It Wins', p.why_it_wins, i)).join('')}
        </div>
      ` : ''}

      ${r.recommended_hackathons && r.recommended_hackathons.length > 0 ? `
        <div class="glass-card" style="margin-bottom: 40px; border-left: 4px solid #f59e0b;">
          <h3 style="margin-bottom: 16px; color: #f59e0b;">🏆 Recommended Hackathons</h3>
          <p style="color: var(--text-muted); margin-bottom: 16px;">Based on your selected themes, you could submit these projects to these upcoming hackathons:</p>
          <div style="display: grid; gap: 16px;">
            ${r.recommended_hackathons.map((h: any) => `
              <div style="background: rgba(255,255,255,0.05); padding: 16px; border-radius: 8px;">
                <h4 style="color: var(--text-main); font-size: 1.1rem; margin-bottom: 4px;">${h.name}</h4>
                <div style="font-size: 0.85rem; color: #00ffcc; margin-bottom: 8px; font-weight: 700;">📅 Date: ${h.date}</div>
                <p style="font-size: 0.95rem; margin-bottom: 12px;">${h.description}</p>
                <a href="${h.registration_link}" target="_blank" class="btn-outline" style="display: inline-block; text-decoration: none; font-size: 0.85rem;">Register Here &rarr;</a>
              </div>
            `).join('')}
          </div>
        </div>
      ` : ''}

      <button id="ps-reset" class="btn-primary" style="width: 100%;">Try Another Theme</button>
    </div>
  `;
}

function attachResultsListeners(render: () => void) {
  const resetBtn = document.getElementById('ps-reset');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      setState({
        selectedDomains: [],
        errorMsg: '',
        result: null,
        screen: 'form'
      }, render);
    });
  }
}
