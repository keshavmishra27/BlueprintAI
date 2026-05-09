import solara
from pathlib import Path

NAV_CSS = """
#app header.v-app-bar,
.v-application header.v-app-bar,
.v-application .primary.v-app-bar {
    background: linear-gradient(90deg, #0A0F1C, #0F2046, #0A0F1C, #1A3673) !important;
    background-color: transparent !important;
    background-size: 300% 300% !important;
    animation: gradientBG 8s ease infinite !important;
    box-shadow: 0 4px 20px rgba(15, 32, 70, 0.6) !important;
    border-bottom: 2px solid rgba(0, 240, 255, 0.15) !important;
}

#app header.v-app-bar .v-toolbar__title {
    font-size: 1.5rem !important;
    font-weight: 900 !important;
    background: linear-gradient(to right, #ffffff, #00f0ff) !important;
    -webkit-background-clip: text !important;
    background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    text-shadow: none !important;
    filter: drop-shadow(0px 2px 4px rgba(0,0,0,0.5)) !important;
    letter-spacing: 1.5px !important;
}

#app header.v-app-bar .v-tab {
    color: rgba(255, 255, 255, 0.6) !important;
    font-weight: 700 !important;
    letter-spacing: 1.5px !important;
    transition: all 0.3s ease !important;
    text-transform: uppercase !important;
}

#app header.v-app-bar .v-tab--active {
    color: #ffffff !important;
    text-shadow: 0 0 15px rgba(0, 240, 255, 0.8) !important;
    background: rgba(0, 240, 255, 0.05) !important;
}

#app header.v-app-bar .v-tab:hover {
    color: #ffffff !important;
    background: rgba(0, 240, 255, 0.1) !important;
    text-shadow: 0 0 10px rgba(0, 240, 255, 0.5) !important;
}

#app header.v-app-bar .v-tabs-slider {
    background: linear-gradient(90deg, transparent, #00f0ff, transparent) !important; 
    height: 3px !important;
    box-shadow: 0 0 15px #00f0ff, 0 0 5px #00f0ff !important;
}

#app header.v-app-bar .v-btn {
    color: white !important;
    font-weight: bold !important;
}

.custom-nav-bar {
}

html, body, #app, .v-application, .v-application--wrap, .v-main, .v-main__wrap, .v-sheet {
    background-color: #A4C3B2 !important;
    background: #A4C3B2 !important;
}

.theme--light.v-sheet {
    background-color: #A4C3B2 !important;
    border-color: rgba(255, 255, 255, 0.1) !important;
}
"""

@solara.component
def Layout(children=[]):
    solara.HTML(tag="style", unsafe_innerHTML=NAV_CSS)
    assets_dir = Path(__file__).parent.parent / "assets"
    if (assets_dir / "custom.css").exists():
        solara.Style(assets_dir / "custom.css")
        
    with solara.AppLayout(title="Group Maker", children=children, color="transparent", classes=["custom-nav-bar"]):
        pass
