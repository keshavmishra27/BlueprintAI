export function renderHome(container: HTMLElement) {
  container.innerHTML = `
    <div class="fade-in" style="text-align: center; padding: 60px 20px;">
      <h1 class="text-title text-gradient" style="text-shadow: 0 4px 20px rgba(0,0,0,0.8);">Welcome to BlueprintAI</h1>
      <p class="text-subtitle" style="margin-bottom: 40px; max-width: 600px; margin-inline: auto; text-shadow: 0 2px 10px rgba(0,0,0,0.8);">
        Your ultimate AI architecture and learning platform. Assess developer skills, discover project ideas, refine concepts, and judge repositories.
      </p>
      
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 24px; max-width: 900px; margin: 0 auto;">
        
        <a href="#/assessment" style="text-decoration: none; color: inherit;">
          <div class="glass-card" style="padding: 24px; text-align: left; height: 100%; display: flex; flex-direction: column;">
            <h3 style="font-size: 1.25rem; font-weight: 800; color: #0891b2; margin-bottom: 8px;"> Assessment</h3>
            <p style="color: var(--text-muted); font-size: 0.9rem; flex: 1;">Take an AI-generated multiple choice quiz on your preferred domains.</p>
          </div>
        </a>

        <a href="#/repo-judge" style="text-decoration: none; color: inherit;">
          <div class="glass-card" style="padding: 24px; text-align: left; height: 100%; display: flex; flex-direction: column;">
            <h3 style="font-size: 1.25rem; font-weight: 800; color: var(--accent); margin-bottom: 8px;"> Repo Judge</h3>
            <p style="color: var(--text-muted); font-size: 0.9rem; flex: 1;">Analyze GitHub repositories and rate their quality and maintainability.</p>
          </div>
        </a>

        <a href="#/project-suggest" style="text-decoration: none; color: inherit;">
          <div class="glass-card" style="padding: 24px; text-align: left; height: 100%; display: flex; flex-direction: column;">
            <h3 style="font-size: 1.25rem; font-weight: 800; color: var(--accent2); margin-bottom: 8px;"> Project Ideas</h3>
            <p style="color: var(--text-muted); font-size: 0.9rem; flex: 1;">Get tailored project suggestions based on your tech stack.</p>
          </div>
        </a>

        <a href="#/idea-refiner" style="text-decoration: none; color: inherit;">
          <div class="glass-card" style="padding: 24px; text-align: left; height: 100%; display: flex; flex-direction: column;">
            <h3 style="font-size: 1.25rem; font-weight: 800; color: var(--primary); margin-bottom: 8px;"> Idea Refiner</h3>
            <p style="color: var(--text-muted); font-size: 0.9rem; flex: 1;">Validate and flesh out your raw product ideas with AI feedback.</p>
          </div>
        </a>

      </div>
    </div>
  `;
}
