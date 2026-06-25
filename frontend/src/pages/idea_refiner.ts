import { apiPost } from '../api';
let state = {
  userIdea: '',
  loading: false,
  errorMsg: '',
  similarProjects: [] as any[],
  checkResult: null as any,
  refinement: null as any,
  screen: 'input' as 'input' | 'results'
};
function setState(newState: Partial<typeof state>, render: () => void) {
  state = { ...state, ...newState };
  render();
}
export function renderIdeaRefiner(container: HTMLElement) {
  const render = () => {
    if (state.screen === 'input') {
      container.innerHTML = getInputHTML();
      attachInputListeners(render);
    } else {
      container.innerHTML = getResultsHTML();
      attachResultsListeners(render);
    }
  };
  render();
}
function getInputHTML() {
  return `
    <div class="fade-in" style="max-width: 860px; margin: 40px auto;">
      <h1 class="text-title"> Idea Validator & Refiner</h1>
      <p class="text-subtitle" style="margin-bottom: 40px;">
        Enter your project idea. We'll check if it already exists and help you find a unique angle with market loophole analysis.
      </p>
      <div style="margin-bottom: 24px;">
        <textarea id="ir-idea" class="input-field" rows="5" placeholder="Describe your project idea in detail...">${state.userIdea}</textarea>
      </div>
      ${state.errorMsg ? `<div class="alert-error" style="margin-bottom: 16px;">${state.errorMsg}</div>` : ''}
      <button id="ir-check" class="btn-primary" style="width: 100%; padding: 20px; font-size: 1.125rem;" ${state.loading ? 'disabled' : ''}>
        ${state.loading ? 'Searching...' : ' Check Similarities'}
      </button>
    </div>
  `;
}
function attachInputListeners(render: () => void) {
  const ideaInput = document.getElementById('ir-idea') as HTMLTextAreaElement;
  if (ideaInput) {
    ideaInput.addEventListener('input', (e) => {
      state.userIdea = (e.target as HTMLTextAreaElement).value;
    });
  }
  const checkBtn = document.getElementById('ir-check');
  if (checkBtn) {
    checkBtn.addEventListener('click', async () => {
      if (!state.userIdea.trim()) {
        setState({ errorMsg: 'Please describe your idea first.' }, render);
        return;
      }
      setState({ loading: true, errorMsg: '' }, render);
      try {
        const res = await apiPost('/idea-validator/check', { idea: state.userIdea }, 120000);
        setState({
          loading: false,
          similarProjects: res.similar_projects || [],
          checkResult: res,
          screen: 'results'
        }, render);
      } catch (err: any) {
        setState({ loading: false, errorMsg: err.message }, render);
      }
    });
  }
}
function getResultsHTML() {
  return `
    <div class="fade-in" style="max-width: 860px; margin: 40px auto; padding-bottom: 60px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px;">
        <h1 class="text-title" style="margin-bottom: 0;">Analysis Results</h1>
        <button id="ir-back" class="btn-outline">← Start Over</button>
      </div>
      <div style="margin-bottom: 40px; border-bottom: 1px solid rgba(0,0,0,0.05); padding-bottom: 32px;">
        <div style="font-size: 0.75rem; letter-spacing: 1px; color: var(--text-muted); margin-bottom: 8px;">YOUR IDEA:</div>
        <div style="font-size: 1rem; color: var(--text-main); font-style: italic; line-height: 1.6;">${state.userIdea}</div>
      </div>
      ${state.refinement ? renderRefinement(state.refinement) : ''}
      ${!state.refinement && state.checkResult ? renderCheckResult(state.checkResult) : ''}
      ${(!state.refinement && state.similarProjects.length > 0) ? `
        <h2 style="font-size: 1.25rem; font-weight: 800; color: #0ea5e9; margin: 40px 0 20px;">Similar Existing Projects</h2>
        ${state.similarProjects.map(renderProjectCard).join('')}
      ` : ''}
      ${(!state.refinement && !state.checkResult && state.similarProjects.length === 0) ? `
        <p style="color: #10b981; font-style: italic;">No similar projects found! Your idea might be very unique.</p>
      ` : ''}
      ${state.errorMsg ? `<div class="alert-error" style="margin-bottom: 16px;">${state.errorMsg}</div>` : ''}
      ${!state.refinement ? `
        <button id="ir-refine" class="btn-primary" style="width: 100%; margin-top: 40px; padding: 20px; font-size: 1.125rem;" ${state.loading ? 'disabled' : ''}>
          ${state.loading ? 'Analyzing...' : ' Refine & Find Gaps'}
        </button>
      ` : ''}
    </div>
  `;
}
function renderCheckResult(res: any) {
  const gap = res.gap_and_loopholes || res.gaps_and_loopholes;
  const sources = res.search_queries_and_sources_used || res.search_sources;
  return `
    <div class="glass-card" style="margin-bottom: 24px;">
      <h3 style="color: #0891b2; margin-bottom: 16px;">Market Comparison Summary</h3>
      ${gap ? `
        <strong style="display: block; margin-bottom: 8px;">Market Gaps & Loopholes</strong>
        <p style="color: var(--text-muted); line-height: 1.7; margin-bottom: 16px;">${gap}</p>
      ` : ''}
      ${sources ? `
        <strong style="display: block; margin-bottom: 8px;">Search Queries and Sources</strong>
        <pre style="color: var(--text-muted); white-space: pre-wrap; font-size: 0.875rem; font-family: inherit;">${Array.isArray(sources) ? sources.join('\n') : sources}</pre>
      ` : ''}
    </div>
  `;
}
function renderRefinement(ref: any) {
  const uniq = ref.uniqueness || {};
  const concept = ref.refined_concept || {};
  return `
    <div style="margin-top: 24px;">
      <div style="padding: 24px; border-radius: 16px; background: rgba(99,102,241,0.05); border: 1px solid rgba(99,102,241,0.1); margin-bottom: 24px; text-align: center;">
        <div style="font-size: 0.75rem; color: #4f46e5; letter-spacing: 2px; margin-bottom: 8px; text-transform: uppercase;">Uniqueness: ${uniq.verdict || 'Unknown'}</div>
        <div style="font-size: 1.5rem; font-weight: 800; color: var(--text-main); margin-bottom: 8px;">${uniq.score || '?'}% Novelty Score</div>
        <p style="color: var(--text-muted); font-size: 0.875rem; line-height: 1.6;">${uniq.rationale || ''}</p>
      </div>
      <div class="glass-card" style="border-left: 4px solid #0891b2; margin-bottom: 32px;">
        <h3 style="color: #0891b2; margin-bottom: 12px;"> Recommended Direction</h3>
        <p style="font-size: 1rem; line-height: 1.7; font-weight: 700; margin-bottom: 16px;">${concept.final_direction || ''}</p>
        ${concept.quick_win_variant ? `
          <div style="padding: 12px; background: rgba(0,0,0,0.02); border-radius: 8px; margin-bottom: 12px;">
            <strong style="color: #0284c7; font-size: 0.75rem; display: block; margin-bottom: 4px;">Quick Win Variant</strong>
            <p style="font-size: 0.875rem; color: var(--text-muted);">${concept.quick_win_variant.description || ''}</p>
          </div>
        ` : ''}
      </div>
    </div>
  `;
}
function renderProjectCard(proj: any) {
  return `
    <div class="glass-card" style="margin-bottom: 20px; padding: 20px;">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
        <div>
          <strong style="color: #0891b2; font-size: 1.125rem;">${proj.name || 'Unknown Project'}</strong>
          ${proj.type ? `<div style="font-size: 0.65rem; font-weight: 900; color: var(--text-muted); letter-spacing: 1px;">${proj.type.toUpperCase()}</div>` : ''}
        </div>
        ${proj.relevance_score ? `<div style="padding: 4px 12px; border-radius: 20px; background: rgba(8,145,178,0.1); border: 1px solid #0891b2; font-size: 0.75rem; font-weight: 800; color: #0891b2;">${proj.relevance_score}% Match</div>` : ''}
      </div>
      <p style="font-size: 0.875rem; color: var(--text-muted); line-height: 1.6; margin-bottom: 12px;">${proj.overview || ''}</p>
      ${proj.comparison ? `
        <div style="padding: 10px; background: rgba(8,145,178,0.05); border-radius: 8px; border-left: 3px solid #0891b2; margin-top: 12px;">
          <div style="font-size: 0.65rem; font-weight: 900; color: #0891b2; margin-bottom: 4px;">V/S YOUR IDEA:</div>
          <p style="font-size: 0.8rem; color: var(--text-muted); font-style: italic;">${proj.comparison}</p>
        </div>
      ` : ''}
    </div>
  `;
}
function attachResultsListeners(render: () => void) {
  const backBtn = document.getElementById('ir-back');
  if (backBtn) {
    backBtn.addEventListener('click', () => {
      setState({ screen: 'input', checkResult: null, refinement: null, similarProjects: [] }, render);
    });
  }
  const refineBtn = document.getElementById('ir-refine');
  if (refineBtn) {
    refineBtn.addEventListener('click', async () => {
      setState({ loading: true, errorMsg: '' }, render);
      try {
        const res = await apiPost('/idea-validator/refine', { idea: state.userIdea }, 180000);
        setState({
          loading: false,
          refinement: res
        }, render);
      } catch (err: any) {
        setState({ loading: false, errorMsg: err.message }, render);
      }
    });
  }
}
