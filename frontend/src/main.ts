import './style.css';
import { Router } from './router';
import { renderHome } from './pages/home';
import { renderAssessment } from './pages/assessment';
import { renderRepoJudge } from './pages/repo_judge';
import { renderProjectSuggest } from './pages/project_suggest';
import { renderIdeaRefiner } from './pages/idea_refiner';
import { initBackgroundAnimation } from './backgroundAnimation';

initBackgroundAnimation();

const appDiv = document.getElementById('app')!;

appDiv.innerHTML = `
  <header class="app-bar">
    <div class="app-title">Group Maker</div>
    <nav class="nav-links">
      <a href="#/" class="nav-home">Home</a>
      <a href="#/assessment" class="nav-assessment">Assessment</a>
      <a href="#/repo-judge" class="nav-repo">Repo Judge</a>
      <a href="#/project-suggest" class="nav-projects">Project Ideas</a>
      <a href="#/idea-refiner" class="nav-ideas">Idea Refiner</a>
    </nav>
  </header>
  <main class="container" id="main-content">
  </main>
`;

const router = new Router('main-content');

router.addRoute({ path: '/', render: renderHome });
router.addRoute({ path: '/assessment', render: renderAssessment });
router.addRoute({ path: '/repo-judge', render: renderRepoJudge });
router.addRoute({ path: '/project-suggest', render: renderProjectSuggest });
router.addRoute({ path: '/idea-refiner', render: renderIdeaRefiner });

// Initial route
router.handleRoute();
