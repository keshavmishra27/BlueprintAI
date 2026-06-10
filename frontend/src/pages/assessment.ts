import { apiGet, apiPost } from '../api';

let state = {
  studentName: '',
  selectedDomains: [] as string[],
  allDomains: [] as string[],
  setupError: '',
  sessionId: null as string | null,
  questions: [] as any[],
  userAnswers: {} as Record<string, string>,
  loading: false,
  loadingStep: '',
  scores: null as any,
  screen: 'setup' as 'setup' | 'quiz' | 'submitting' | 'results'
};

function setState(newState: Partial<typeof state>, render: () => void) {
  state = { ...state, ...newState };
  render();
}

export function renderAssessment(container: HTMLElement) {
  const render = () => {
    if (state.screen === 'setup') {
      container.innerHTML = getSetupHTML();
      attachSetupListeners(render);
    } else if (state.screen === 'quiz') {
      container.innerHTML = getQuizHTML();
      attachQuizListeners(render);
    } else if (state.screen === 'submitting') {
      container.innerHTML = `<div class="fade-in" style="text-align: center; margin-top: 100px;"><h2>Grading your quiz...</h2></div>`;
    } else {
      container.innerHTML = getResultsHTML();
      attachResultsListeners(render);
    }
  };

  // Initial load domains
  if (state.allDomains.length === 0 && !state.setupError) {
    apiGet('/assess/domains').then(domains => {
      setState({ allDomains: domains }, render);
    }).catch(err => {
      setState({ setupError: err.message || 'Failed to load domains' }, render);
    });
  }

  render();
}

function getSetupHTML() {
  const domainsHTML = state.allDomains.map(d => {
    const isSel = state.selectedDomains.includes(d);
    return `<button class="domain-btn ${isSel ? 'btn-outline selected' : 'btn-outline'}" data-domain="${d}">${isSel ? '✓ ' : ''}${d}</button>`;
  }).join(' ');

  return `
    <div class="fade-in" style="max-width: 680px; margin: 40px auto;">
      <h1 class="text-title"> AI Developer Assessment</h1>
      <p class="text-subtitle" style="margin-bottom: 32px;">
        Select a domain to generate an adaptive, 15-question technical exam.
      </p>

      <div class="glass-card">
        <h3 style="color: #0891b2; margin-bottom: 16px;">Your Details</h3>
        <div style="margin-bottom: 16px;">
          <label class="input-label">Full Name</label>
          <input type="text" id="as-name" class="input-field" value="${state.studentName}">
        </div>

        <div style="margin-bottom: 16px;">
          <label class="input-label">Select Domains</label>
          ${state.allDomains.length === 0 && !state.setupError ? '<p>Loading domains...</p>' : ''}
          <div style="display: flex; flex-wrap: wrap; gap: 8px;">
            ${domainsHTML}
          </div>
        </div>

        ${state.setupError ? `<div class="alert-error" style="margin-bottom: 16px;">${state.setupError}</div>` : ''}

        <button id="as-start" class="btn-primary" style="width: 100%; margin-top: 16px;" ${state.loading ? 'disabled' : ''}>
          ${state.loading ? 'Generating questions...' : 'Start Quiz'}
        </button>
      </div>
    </div>
  `;
}

function attachSetupListeners(render: () => void) {
  const nameInput = document.getElementById('as-name') as HTMLInputElement;
  if (nameInput) {
    nameInput.addEventListener('input', (e) => {
      state.studentName = (e.target as HTMLInputElement).value;
    });
  }

  document.querySelectorAll('.domain-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const d = (e.target as HTMLElement).getAttribute('data-domain');
      if (d) {
        if (state.selectedDomains.includes(d)) {
          state.selectedDomains = state.selectedDomains.filter(x => x !== d);
        } else {
          state.selectedDomains.push(d);
        }
        render();
      }
    });
  });

  const startBtn = document.getElementById('as-start');
  if (startBtn) {
    startBtn.addEventListener('click', async () => {
      if (!state.studentName || state.selectedDomains.length === 0) {
        setState({ setupError: 'Please enter name and select at least one domain.' }, render);
        return;
      }
      setState({ loading: true, setupError: '' }, render);

      try {
        const res = await apiPost('/assess/generate-mcq', {
          student_name: state.studentName,
          domains: state.selectedDomains
        }, 180000);

        setState({
          loading: false,
          sessionId: res.session_id,
          questions: res.questions,
          userAnswers: {},
          screen: 'quiz'
        }, render);
      } catch (err: any) {
        setState({ loading: false, setupError: err.message }, render);
      }
    });
  }
}

function getQuizHTML() {
  const qHtml = state.questions.map((q, i) => {
    const chosen = state.userAnswers[i] || '';
    const opts = (q.options || []).map((opt: string) => {
      const isSel = chosen === opt[0];
      return `<button class="opt-btn btn-outline ${isSel ? 'selected' : ''}" data-qi="${i}" data-val="${opt[0]}" style="display: block; width: 100%; text-align: left; margin-bottom: 8px; border-radius: 8px;">${opt}</button>`;
    }).join('');

    return `
      <div class="glass-card" style="margin-bottom: 24px; padding: 24px;">
        <div style="font-weight: 700; color: #64748b; margin-bottom: 8px; text-transform: uppercase;">Question ${i + 1} <span style="float: right; font-size: 0.75rem; background: rgba(0,0,0,0.05); padding: 2px 8px; border-radius: 12px;">${q.difficulty}</span></div>
        <div style="font-size: 1.1rem; margin-bottom: 16px;">${q.question}</div>
        ${opts}
      </div>
    `;
  }).join('');

  const answered = Object.keys(state.userAnswers).length;
  const total = state.questions.length;
  const canSubmit = answered === total;

  return `
    <div class="fade-in" style="max-width: 760px; margin: 40px auto;">
      <div style="display: flex; justify-content: space-between; margin-bottom: 24px;">
        <h2>Quiz: ${state.selectedDomains.join(', ')}</h2>
        <div style="background: rgba(0,0,0,0.05); padding: 4px 12px; border-radius: 12px; font-weight: 700;">${answered}/${total} answered</div>
      </div>
      ${qHtml}
      
      ${state.setupError ? `<div class="alert-error" style="margin-bottom: 16px;">${state.setupError}</div>` : ''}

      <button id="as-submit" class="btn-primary" style="width: 100%;" ${!canSubmit ? 'disabled' : ''}>
        Submit Quiz
      </button>
    </div>
  `;
}

function attachQuizListeners(render: () => void) {
  document.querySelectorAll('.opt-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const target = e.currentTarget as HTMLElement;
      const qi = target.getAttribute('data-qi');
      const val = target.getAttribute('data-val');
      if (qi && val) {
        state.userAnswers[qi] = val;
        render();
      }
    });
  });

  const subBtn = document.getElementById('as-submit');
  if (subBtn) {
    subBtn.addEventListener('click', async () => {
      setState({ screen: 'submitting' }, render);
      try {
        const res = await apiPost('/assess/submit-mcq', {
          session_id: state.sessionId,
          answers: state.userAnswers
        });
        setState({ scores: res.scores, screen: 'results' }, render);
      } catch (err: any) {
        setState({ setupError: err.message, screen: 'quiz' }, render);
      }
    });
  }
}

function getResultsHTML() {
  const s = state.scores;
  if (!s) return '';
  const correct = s.correct || 0;
  const total = s.total || 1;
  const pct = Math.round((correct / total) * 100);
  const color = pct >= 80 ? '#34d399' : pct >= 50 ? '#f59e0b' : '#ef4444';

  return `
    <div class="fade-in" style="max-width: 760px; margin: 40px auto; text-align: center;">
      <h1 class="text-title"> Results for ${state.studentName}</h1>
      
      <div class="glass-card" style="border-top: 4px solid ${color}; margin-bottom: 24px;">
        <div style="font-size: 0.875rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px;">Your Score</div>
        <div style="font-size: 4rem; font-weight: 900; color: ${color};">${correct}/${total}</div>
        <div style="font-weight: 700; color: ${color};">${pct}% correct</div>
      </div>

      <div class="glass-card" style="margin-bottom: 24px;">
        <div style="font-size: 0.875rem; color: var(--text-muted); text-transform: uppercase;">Domain Percentile</div>
        <div style="font-size: 3.5rem; font-weight: 900; color: #0891b2;">${s.percentile || 50}%</div>
        <p>${s.percentile_message || 'Estimated percentile'}</p>
      </div>

      <button id="as-reset" class="btn-primary" style="width: 100%;">Take Another Quiz</button>
    </div>
  `;
}

function attachResultsListeners(render: () => void) {
  const resetBtn = document.getElementById('as-reset');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      setState({
        sessionId: null,
        questions: [],
        userAnswers: {},
        scores: null,
        screen: 'setup'
      }, render);
    });
  }
}
