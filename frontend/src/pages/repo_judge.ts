import { apiPost } from '../api';
let state = {
  githubUrl: '',
  studentName: '',
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
export function renderRepoJudge(container: HTMLElement) {
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
  return `
    <div class="fade-in" style="max-width: 680px; margin: 40px auto;">
      <h1 class="text-title" style="color: var(--text-main);">GitHub Repo Judge</h1>
      <p class="text-subtitle" style="margin-bottom: 32px;">
        Paste your student's public GitHub repository URL. The AI will read the entire codebase and return a hackathon judge verdict — scores, strengths, and concrete improvements.
      </p>
      <div class="glass-card">
        <h2 style="font-size: 1.25rem; font-weight: 700; color: #0891b2; margin-bottom: 24px;">Judge a Repository</h2>
        <div style="margin-bottom: 16px;">
          <label class="input-label">Student Name</label>
          <input type="text" id="rj-name" class="input-field" value="${state.studentName}">
        </div>
        <div style="margin-bottom: 24px;">
          <label class="input-label">GitHub Repository URL</label>
          <input type="url" id="rj-url" class="input-field" value="${state.githubUrl}" placeholder="https://github.com/owner/repo">
        </div>
        ${state.errorMsg ? `<div class="alert-error" style="margin-bottom: 16px;">Error: ${state.errorMsg}</div>` : ''}
        <button id="rj-submit" class="btn-primary" style="width: 100%;" ${state.loading ? 'disabled' : ''}>
          ${state.loading ? 'Analyzing... (may take 5-15 min)' : 'Analyze Repository'}
        </button>
        ${state.loading ? `
          <div class="alert-info" style="margin-top: 24px;">
            <strong>${state.loadingStep || 'Working...'}</strong><br>
            <span style="font-size: 0.8rem; color: var(--text-muted);">This can take 5-15 minutes for large repos — please keep this tab open!</span>
          </div>
        ` : ''}
      </div>
    </div>
  `;
}
function attachFormListeners(render: () => void) {
  const submitBtn = document.getElementById('rj-submit');
  const nameInput = document.getElementById('rj-name') as HTMLInputElement;
  const urlInput = document.getElementById('rj-url') as HTMLInputElement;
  if (nameInput) {
    nameInput.addEventListener('input', (e) => {
      state.studentName = (e.target as HTMLInputElement).value;
    });
  }
  if (urlInput) {
    urlInput.addEventListener('input', (e) => {
      state.githubUrl = (e.target as HTMLInputElement).value;
    });
  }
  if (submitBtn) {
    submitBtn.addEventListener('click', async () => {
      if (!state.studentName || !state.githubUrl) {
        setState({ errorMsg: 'Please fill in both fields.' }, render);
        return;
      }
      if (!state.githubUrl.includes('github.com')) {
        setState({ errorMsg: 'URL must be a valid github.com link.' }, render);
        return;
      }
      setState({
        loading: true,
        errorMsg: '',
        loadingStep: 'Downloading repo + running static analysis...'
      }, render);
      try {
        const res = await apiPost('/repo-judge/analyze', {
          github_url: state.githubUrl,
          student_name: state.studentName
        }, 900000); 
        setState({
          loading: false,
          result: res,
          screen: 'results'
        }, render);
      } catch (err: any) {
        setState({
          loading: false,
          errorMsg: err.message || 'Analysis failed'
        }, render);
      }
    });
  }
}
function getResultsHTML() {
  const r = state.result;
  if (!r) return '';
  const total = r.total_score || r.overall_score || 0;
  const color = total >= 75 ? 'var(--primary)' : total >= 50 ? '#f59e0b' : '#ef4444';
  const renderScoreBar = (label: string, scoreData: any, scColor: string) => {
    const score = scoreData?.score || 0;
    const reasons = scoreData?.reasons || [];
    const reasonText = reasons.length > 0 ? reasons[0] : 'No reasons provided.';
    return `
    <div style="background: rgba(255,255,255,0.05); padding: 16px; border-radius: 12px; margin-bottom: 16px;">
      <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
        <strong>${label}</strong>
        <strong style="color: ${scColor}">${score}/10</strong>
      </div>
      <div style="background: rgba(0,0,0,0.1); height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 12px;">
        <div style="background: ${scColor}; height: 100%; width: ${score * 10}%;"></div>
      </div>
      <div style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.4;">
        ${reasonText}
      </div>
    </div>
  `;
  };
  return `
    <div class="fade-in" style="max-width: 860px; margin: 40px auto; padding-bottom: 100px;">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 32px;">
        <div>
          <h1 class="text-title" style="margin-bottom: 4px;">Expert Verdict: ${r.student_name}</h1>
          <a href="${r.repo_url || r.repository}" target="_blank" style="color: #4f46e5;">${r.repo_url || r.repository}</a>
        </div>
        <div style="text-align: right; border-right: 4px solid ${color}; padding-right: 20px;">
          <div style="font-size: 0.75rem; color: var(--text-muted); letter-spacing: 2px;">TOTAL SCORE</div>
          <div style="font-size: 3rem; font-weight: 900; color: ${color}; line-height: 1;">${Math.round(total)}/100</div>
        </div>
      </div>
      <div class="glass-card" style="margin-bottom: 32px;">
        <h3 style="margin-bottom: 16px; color: #4f46e5;">Scores</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px;">
          ${renderScoreBar('Functionality', r.scores?.functionality, '#00ffcc')}
          ${renderScoreBar('Code Quality', r.scores?.code_quality, '#0088ff')}
          ${renderScoreBar('Documentation', r.scores?.documentation, '#00ff66')}
          ${renderScoreBar('Architecture', r.scores?.architecture, '#f59e0b')}
          ${renderScoreBar('Testing & CI', r.scores?.testing_ci, '#ef4444')}
          ${renderScoreBar('Innovation & UX', r.scores?.innovation_ux, '#a855f7')}
        </div>
      </div>
      ${r.mentor_notes ? `
        <div class="glass-card" style="margin-bottom: 32px; border-left: 4px solid #4f46e5;">
          <h3 style="margin-bottom: 12px; color: #4f46e5;">🎙️ Mentor Verdict</h3>
          <p style="font-style: italic; line-height: 1.6;">${r.mentor_notes}</p>
        </div>
      ` : ''}
      ${r.strengths && r.strengths.length > 0 ? `
        <div class="glass-card" style="margin-bottom: 32px; border-left: 4px solid #00ff66;">
          <h3 style="margin-bottom: 12px; color: #00ff66;">👍 Strengths</h3>
          <ul style="padding-left: 20px; color: var(--text-main); line-height: 1.6;">
            ${r.strengths.map((s: string) => `<li style="margin-bottom: 8px;">${s}</li>`).join('')}
          </ul>
        </div>
      ` : ''}
      ${r.top_issues && r.top_issues.length > 0 ? `
        <div class="glass-card" style="margin-bottom: 32px; border-left: 4px solid #ef4444;">
          <h3 style="margin-bottom: 12px; color: #ef4444;">👎 Areas for Improvement</h3>
          <ul style="padding-left: 20px; color: var(--text-main); line-height: 1.6;">
            ${r.top_issues.map((i: any) => `
              <li style="margin-bottom: 12px;">
                <strong>${i.title || 'Issue'}:</strong> ${i.description || i}
              </li>
            `).join('')}
          </ul>
        </div>
      ` : ''}
      ${r.hackathon_recommendations && r.hackathon_recommendations.length > 0 ? `
        <div class="glass-card" style="margin-bottom: 32px; border-left: 4px solid #f59e0b;">
          <h3 style="margin-bottom: 16px; color: #f59e0b;">🏆 Recommended Hackathons</h3>
          <p style="color: var(--text-muted); margin-bottom: 16px;">Based on your project's domain, you could submit this repository to these upcoming hackathons:</p>
          <div style="display: grid; gap: 16px;">
            ${r.hackathon_recommendations.map((h: any) => `
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
      <button id="rj-reset" class="btn-primary" style="width: 100%;">Judge Another Project</button>
    </div>
  `;
}
function attachResultsListeners(render: () => void) {
  const resetBtn = document.getElementById('rj-reset');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      setState({
        githubUrl: '',
        studentName: '',
        errorMsg: '',
        result: null,
        screen: 'form'
      }, render);
    });
  }
}
