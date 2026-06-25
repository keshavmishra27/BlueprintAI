import { showLoadingScreen, hideLoadingScreen } from './loadingAnimation';
export interface Route {
  path: string;
  render: (container: HTMLElement) => void | Promise<void>;
  label?: string;
}
export class Router {
  private routes: Route[] = [];
  private container: HTMLElement;
  constructor(containerId: string) {
    const el = document.getElementById(containerId);
    if (!el) throw new Error(`Container #${containerId} not found`);
    this.container = el;
    window.addEventListener('hashchange', () => this.handleRoute());
  }
  addRoute(route: Route) {
    this.routes.push(route);
  }
  getRoutes() {
    return this.routes;
  }
  async handleRoute() {
    const hash = window.location.hash.slice(1) || '/';
    let matchedRoute = this.routes.find(r => r.path === hash);
    if (!matchedRoute) {
      matchedRoute = this.routes.find(r => r.path === '/'); 
    }
    if (matchedRoute) {
      await showLoadingScreen();
      this.container.innerHTML = '';
      await matchedRoute.render(this.container);
      this.updateActiveNav(matchedRoute.path);
      hideLoadingScreen();
    }
  }
  navigate(path: string) {
    window.location.hash = path;
  }
  private updateActiveNav(path: string) {
    document.querySelectorAll('nav a').forEach(a => {
      if (a.getAttribute('href') === `#${path}`) {
        a.classList.add('active');
      } else {
        a.classList.remove('active');
      }
    });
  }
}
