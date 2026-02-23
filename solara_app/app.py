import sys, os

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import solara
import solara.lab
from solara_app.pages import members, assessment, repo_judge


@solara.component
def Layout(children=[]):
    with solara.AppLayout(title="Group Maker", children=children):
        pass


routes = [
    solara.Route(
        path="/",
        component=members.Page,
        label="👥 Members",
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
]
