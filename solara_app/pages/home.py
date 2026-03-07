"""
home.py — Landing page for Group Maker
Horizontal layout flashcards matching the project suggestion theme.
"""

import solara

CARD_STYLE = (
    "background:rgba(10, 25, 40, 0.65); backdrop-filter:blur(16px);"
    "border:1px solid rgba(0, 255, 204, 0.25); border-radius:16px;"
    "padding:24px; box-shadow:0 8px 32px rgba(0, 136, 255, 0.15);"
    "transition:transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;"
    "cursor:pointer;"
)

CARD_HOVER_CSS = """
.home-card:hover {
    transform: translateY(-4px) !important;
    box-shadow: 0 12px 40px rgba(0, 255, 204, 0.25) !important;
    border-color: rgba(0, 255, 204, 0.5) !important;
}
.home-card { transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease; }

@keyframes fadeInUp {
    from { opacity:0; transform:translateY(20px); }
    to   { opacity:1; transform:translateY(0); }
}
.fade-in-up { animation: fadeInUp 0.5s ease forwards; }

.text-gradient {
    background: linear-gradient(to right bottom, #ffffff 30%, #94a3b8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.text-gradient-teal {
    background: linear-gradient(135deg, #00ffcc 0%, #0088ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
"""


@solara.component
def FeatureCard(index: int, title: str, description: str, highlight_label: str, highlight_text: str, accent: str, route: str):
    """A horizontal flashcard component."""
    with solara.v.Html(
        tag="div",
        class_="home-card fade-in-up",
        attributes={"onclick": f"window.location.href='{route}'"},
        style_=(
            f"{CARD_STYLE}"
            f"animation-delay:{index * 0.1}s; opacity:0;"
            f"border-top:3px solid {accent};"
            "margin-bottom:24px; width:100%; display:block;"
        ),
    ):
        # Header
        with solara.v.Html(
            tag="div",
            style_="display:flex; align-items:center; gap:12px; margin-bottom:12px;",
        ):
            solara.v.Html(
                tag="div",
                style_=(
                    f"width:32px; height:32px; border-radius:50%; background:{accent};"
                    "display:flex; align-items:center; justify-content:center;"
                    "font-weight:800; font-size:14px; color:#000; flex-shrink:0;"
                ),
                children=[str(index)]
            )
            solara.v.Html(
                tag="span",
                style_="font-size:20px; font-weight:700; color:#ffffff; line-height:1.3;",
                children=[title]
            )
        
        # Description
        solara.v.Html(
            tag="span",
            style_="font-size:15px; color:rgba(255,255,255,0.8); line-height:1.6; display:block; margin-bottom:16px;",
            children=[description]
        )
        
        # Highlight Section
        with solara.v.Html(
            tag="div",
            style_=(
                f"margin-top:14px; padding:12px 16px; border-radius:10px;"
                f"background:rgba(0, 255, 204, 0.06); border-left:3px solid {accent};"
            ),
        ):
            solara.v.Html(
                tag="span",
                style_=f"font-size:12px; text-transform:uppercase; letter-spacing:1px; color:{accent}; font-weight:700; display:block; margin-bottom:6px;",
                children=[highlight_label]
            )
            solara.v.Html(
                tag="span",
                style_="font-size:14px; color:rgba(255,255,255,0.85); line-height:1.5; display:block;",
                children=[highlight_text]
            )

@solara.component
def Page():
    solara.Title("Group Maker | Home")

    solara.HTML(tag="style", unsafe_innerHTML=f"""
        .v-application, .v-application--wrap, .v-main__wrap {{
            background: transparent !important;
        }}
        body {{
            background-color: #030a16 !important;
            margin: 0;
            min-height: 100vh;
        }}
        @keyframes gradientBG {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
        {CARD_HOVER_CSS}
    """)

    with solara.v.Html(
        tag="div",
        style_=(
            "min-height:100vh;"
            "background: linear-gradient(-45deg, #0f2027, #203a43, #153243, #0a192f);"
            "background-size: 400% 400%;"
            "animation: gradientBG 15s ease infinite;"
            "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"
            "color:#ffffff;"
            "padding-bottom:60px;"
            "box-sizing:border-box;"
        ),
    ):
        with solara.v.Html(tag="div", style_="max-width:900px; margin:40px auto; padding:0 24px;"):
            # Hero section
            with solara.v.Html(tag="h1", style_="font-size: clamp(36px, 6vw, 54px); font-weight: 800; text-align: center; margin-bottom: 16px;"):
                solara.v.Html(tag="span", attributes={"class": "text-gradient"}, children=["Group "])
                solara.v.Html(tag="span", attributes={"class": "text-gradient-teal"}, children=["Maker"])
            
            solara.Text(
                "The ultimate AI ecosystem for engineering teams. Manage developer profiles, assess technical skills instantly, and get expert feedback on your codebases.",
                style={
                    "color": "rgba(255,255,255,0.8)", "font-size": "18px",
                    "line-height": "1.6", "margin-bottom": "48px", "display": "block",
                    "text-align": "center", "max-width": "750px", "margin-left": "auto", "margin-right": "auto"
                },
            )

            solara.Text(
                "Explore Our Features",
                style={
                    "font-size": "22px", "font-weight": "700", "color": "#00ffcc",
                    "margin-bottom": "24px", "display": "block", "border-bottom": "1px solid rgba(0, 255, 204, 0.3)", "padding-bottom": "12px"
                },
            )

            FeatureCard(
                index=1,
                title="AI MCQ Assessment",
                description="Test developer skills accurately. Our LLM generates 15 questions across 3 difficulty levels based on the selected domain.",
                highlight_label="✨ WHY IT'S UNIQUE",
                highlight_text="Instantly computes a global developer percentile based on a weighted scoring curve, replacing subjective interviews with objective metrics.",
                accent="#0088ff", # Blue
                route="/assessment"
            )

            FeatureCard(
                index=2,
                title="Member Management",
                description="Organise perfect hackathon teams. Create profiles and assign domains to sync your entire team's skills in one place.",
                highlight_label="✨ WHY IT'S UNIQUE",
                highlight_text="Acts as a central nervous system for your hackathon, cleanly separating frontend, backend, and AI specialists.",
                accent="#00ffcc", # Teal
                route="/members"
            )

            FeatureCard(
                index=3,
                title="Repo Judge",
                description="Share your GitHub repository and get an international hackathon judge's critical feedback. Understand exactly where your code needs improvement.",
                highlight_label="✨ WHY IT'S UNIQUE",
                highlight_text="Simulates a real hackathon judge's perspective, pointing out exact architectural flaws and code quality issues before you submit.",
                accent="#0088ff", # Blue
                route="/repo-judge"
            )
            
            FeatureCard(
                index=4,
                title="Project Ideas Generator",
                description="Stuck on what to build? Enter a theme and get the top 5 industry-standard resume projects and 5 winning hackathon ideas instantly.",
                highlight_label="✨ WHY IT'S UNIQUE",
                highlight_text="Uses LangChain and Ollama to guarantee highly relevant, structured, and technically impressive ideas tailored precisely to your input.",
                accent="#00ffcc", # Teal
                route="/project-suggest"
            )
