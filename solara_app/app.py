import sys, os
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
import solara
import solara.lab
from solara_app.pages import home, assessment, repo_judge, project_suggest, idea_refiner, swot
from pathlib import Path
NAV_CSS = """
#app header.v-app-bar,
.v-application header.v-app-bar,
.v-application .primary.v-app-bar {
    background: linear-gradient(90deg, #FF0076, #590FB7, #256EFF) !important;
    background-color: #F6FFF8 !important;
    background-size: 200% 200% !important;
    animation: gradientBG 6s ease infinite !important;
    box-shadow: 0 4px 20px rgba(89, 15, 183, 0.4) !important;
    border-bottom: 2px solid rgba(255, 255, 255, 0.1) !important;
}
#app header.v-app-bar .v-toolbar__title {
    font-size: 1.5rem !important;
    font-weight: 900 !important;
    background: linear-gradient(to right, #ffffff, #e0e0e0) !important;
    -webkit-background-clip: text !important;
    background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    text-shadow: none !important;
    filter: drop-shadow(0px 2px 4px rgba(0,0,0,0.3)) !important;
    letter-spacing: 1px !important;
}
#app header.v-app-bar .v-tab {
    color: rgba(255, 255, 255, 0.7) !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    transition: all 0.3s ease !important;
    text-transform: uppercase !important;
}
#app header.v-app-bar .v-tab--active {
    color: #ffffff !important;
    text-shadow: 0 0 15px rgba(255, 255, 255, 0.9) !important;
    background: rgba(255, 255, 255, 0.1) !important;
}
#app header.v-app-bar .v-tab:hover {
    color: #ffffff !important;
    background: rgba(255, 255, 255, 0.15) !important;
    text-shadow: 0 0 10px rgba(255, 255, 255, 0.6) !important;
}
#app header.v-app-bar .v-tabs-slider {
    background-color: #F6FFF8 !important;
    height: 4px !important;
    box-shadow: 0 0 15px #00FFD1, 0 0 5px #00FFD1 !important;
}
#app header.v-app-bar .v-btn {
    color: white !important;
    font-weight: bold !important;
}
"""
@solara.component
def Layout(children=[]):
    solara.Style(Path(__file__).parent / "assets" / "custom.css")
    solara.HTML(tag="style", unsafe_innerHTML=NAV_CSS)
    with solara.AppLayout(title="Group Maker", children=children, color="transparent", classes=["custom-nav-bar"]):
        pass
routes = [
    solara.Route(
        path="/",
        component=home.Page,
        label="🏠 Home",
    ),
    solara.Route(
        path="assessment",
        component=assessment.Page,
        label="📝 Assessment",
    ),
    solara.Route(
        path="repo-judge",
        component=repo_judge.Page,
        label="🧑‍⚖️ Repo Judge",
    ),
    solara.Route(
        path="project-suggest",
        component=project_suggest.Page,
        label="🚀 Project Ideas",
    ),
    solara.Route(
        path="idea-refiner",
        component=idea_refiner.Page,
        label="💡 Idea Refiner",
    ),
    solara.Route(
        path="swot",
        component=swot.Page,
        label="📊 SWOT",
    ),
]