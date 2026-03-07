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

HOME_CSS = """
.home-card:hover {
    transform: translateY(-4px) !important;
    box-shadow: 0 12px 40px rgba(0, 255, 204, 0.25) !important;
    border-color: rgba(0, 255, 204, 0.5) !important;
}
.home-card { transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease; }

.tech-chip {
    display: inline-block;
    background: rgba(0, 136, 255, 0.2);
    border: 1px solid rgba(0, 136, 255, 0.4);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    color: #7dd3fc;
    margin: 3px 4px 3px 0;
    font-weight: 600;
    letter-spacing: 0.3px;
}

@keyframes fadeInUp {
    from { opacity:0; transform:translateY(30px); }
    to   { opacity:1; transform:translateY(0); }
}
.fade-in-up { 
    opacity: 0;
    animation: fadeInUp 0.7s cubic-bezier(0.2, 0.8, 0.2, 1) forwards; 
}

.text-gradient {
    background: linear-gradient(to right bottom, #ffffff 20%, #94a3b8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.text-gradient-teal {
    background: linear-gradient(135deg, #00ffcc 0%, #0088ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 15px rgba(0,255,204,0.4));
}

/* 🎇 Premium Background Animations */
.bg-grid {
    position: fixed; inset: 0; z-index: -2;
    background-size: 40px 40px;
    background-image: 
        linear-gradient(to right, rgba(255, 255, 255, 0.05) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
    mask-image: radial-gradient(ellipse at center, black 40%, transparent 80%);
    -webkit-mask-image: radial-gradient(ellipse at center, black 40%, transparent 80%);
}

@keyframes float {
    0% { transform: translateY(0px) translateX(0px); }
    50% { transform: translateY(-30px) translateX(20px); }
    100% { transform: translateY(0px) translateX(0px); }
}
.glowing-orb {
    position: fixed; border-radius: 50%; filter: blur(80px);
    z-index: -1; animation: float 10s ease-in-out infinite;
    opacity: 0.6;
}
.orb-1 { width: 300px; height: 300px; background: rgba(0, 255, 204, 0.4); top: 10%; left: 15%; animation-delay: 0s; }
.orb-2 { width: 400px; height: 400px; background: rgba(0, 136, 255, 0.3); bottom: 10%; right: 10%; animation-delay: -5s; }
.orb-3 { width: 250px; height: 250px; background: rgba(139, 92, 246, 0.3); top: 40%; left: 50%; transform: translateX(-50%); animation: float 15s ease-in-out infinite reverse; }

/* 🚀 Hero Elements */
.pill-badge {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 6px 16px; border-radius: 30px;
    background: rgba(0, 255, 204, 0.1);
    border: 1px solid rgba(0, 255, 204, 0.3);
    color: #00ffcc; font-size: 14px; font-weight: 600;
    margin-bottom: 24px; box-shadow: 0 0 20px rgba(0,255,204,0.1);
}

.cta-button {
    padding: 14px 32px; border-radius: 12px; font-size: 16px; font-weight: 700;
    cursor: pointer; transition: all 0.3s ease; border: none;
    letter-spacing: 0.5px;
}
.cta-primary {
    background: linear-gradient(135deg, #00ffcc 0%, #0088ff 100%);
    color: #000; box-shadow: 0 4px 15px rgba(0, 255, 204, 0.3);
}
.cta-primary:hover {
    transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0, 255, 204, 0.5);
    background: linear-gradient(135deg, #33ffdb 0%, #33a1ff 100%);
}
.cta-secondary {
    background: rgba(255,255,255,0.05); color: #fff;
    border: 1px solid rgba(255,255,255,0.2);
    backdrop-filter: blur(10px);
}
.cta-secondary:hover {
    background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.4);
    transform: translateY(-2px);
}
"""


@solara.component
def TechChips(techs: list):
    """Render tech stack as small pill badges."""
    if not techs:
        return
    with solara.v.Html(tag="div", style_="display:flex; flex-wrap:wrap; gap:4px; margin-bottom:16px;"):
        for tech in techs:
            solara.v.Html(
                tag="span",
                class_="tech-chip",
                children=[tech],
            )

@solara.component
def FeatureCard(index: int, title: str, description: str, tech_stack: list, highlight_label: str, highlight_text: str, accent: str, route: str):
    """A horizontal flashcard component."""
    with solara.v.Html(
        tag="div",
        class_="home-card fade-in-up",
        attributes={"onclick": f"window.location.href='{route}'"},
        style_=(
            f"{CARD_STYLE}"
            f"animation-delay:{index * 0.1}s;"
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
            style_="font-size:15px; color:rgba(255,255,255,0.8); line-height:1.6; display:block; margin-bottom:12px;",
            children=[description]
        )
        
        # Tech stack chips
        TechChips(tech_stack)
        
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
            background-color: #030812 !important;
            margin: 0;
            min-height: 100vh;
        }}
        {HOME_CSS}
    """)

    with solara.v.Html(
        tag="div",
        style_=(
            "min-height:100vh;"
            "background: #030812;"
            "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"
            "color:#ffffff;"
            "padding-bottom:100px;"
            "box-sizing:border-box;"
            "position:relative;"
            "overflow-x:hidden;"
        ),
    ):
        # Background Elements
        solara.v.Html(tag="div", class_="bg-grid")
        solara.v.Html(tag="div", class_="glowing-orb orb-1")
        solara.v.Html(tag="div", class_="glowing-orb orb-2")
        solara.v.Html(tag="div", class_="glowing-orb orb-3")

        with solara.v.Html(tag="div", style_="max-width:1000px; margin:0 auto; padding:80px 24px 40px; position:relative; z-index:1;"):
            
            # 🚀 Hero section
            with solara.v.Html(tag="div", style_="text-align:center; margin-bottom:80px;", class_="fade-in-up", attributes={"style": "animation-delay: 0.1s;"}):
                # Pill Badge
                with solara.v.Html(tag="div", class_="pill-badge"):
                    solara.v.Html(tag="span", children=["✨"])
                    solara.v.Html(tag="span", children=["The Ultimate AI Engineering Platform"])
                
                # Massive Heading
                with solara.v.Html(tag="h1", style_="font-size: clamp(48px, 8vw, 84px); font-weight: 800; line-height: 1.1; margin-bottom: 24px; letter-spacing:-1px;"):
                    solara.v.Html(tag="span", class_="text-gradient", children=["Build Better Teams. "])
                    solara.v.Html(tag="br")
                    solara.v.Html(tag="span", class_="text-gradient-teal", children=["Ship Faster Code."])
                
                # Description
                solara.Text(
                    "Manage top developer profiles, auto-grade technical skills with our AI Assessment, "
                    "and review complex codebases instantly just like a real hackathon judge.",
                    style={
                        "color": "rgba(255,255,255,0.7)", "font-size": "clamp(18px, 2vw, 22px)",
                        "line-height": "1.6", "margin-bottom": "40px", "display": "block",
                        "max-width": "800px", "margin-left": "auto", "margin-right": "auto",
                        "font-weight": "400"
                    },
                )
                
                # CTA Buttons
                with solara.v.Html(tag="div", style_="display:flex; justify-content:center; gap:20px; flex-wrap:wrap;"):
                    solara.v.Html(
                        tag="button",
                        class_="cta-button cta-primary",
                        attributes={"onclick": "window.location.href='/assessment'"},
                        children=["Start Your Assessment 🚀"]
                    )
                    solara.v.Html(
                        tag="button",
                        class_="cta-button cta-secondary",
                        attributes={"onclick": "window.location.href='/members'"},
                        children=["Explore Member Hub"]
                    )

            # 🧭 Features Section Transition
            with solara.v.Html(
                tag="div",
                style_=(
                    "display:flex; align-items:center; gap:16px; margin-bottom:32px;"
                    "padding-bottom:16px; border-bottom:1px solid rgba(255,255,255,0.1);"
                ),
                class_="fade-in-up",
                attributes={"style": "animation-delay: 0.3s;"}
            ):
                solara.v.Html(
                    tag="div",
                    style_=(
                        "width:56px; height:56px; border-radius:16px;"
                        "background:rgba(0, 255, 204, 0.1);"
                        "border: 1px solid rgba(0, 255, 204, 0.3);"
                        "display:flex; align-items:center; justify-content:center;"
                        "font-size:28px; box-shadow: 0 0 20px rgba(0, 255, 204, 0.2) inset;"
                    ),
                    # children=["⚡"]
                )
                # with solara.v.Html(tag="div"):
                #     solara.Text(
                #         "Powerful Features",
                #         style={"font-size": "28px", "font-weight": "800", "color": "#ffffff", "display": "block", "letter-spacing":"-0.5px"},
                #     )
                #     solara.Text(
                #         "Everything you need to run high-efficiency hackathons and engineering sprints.",
                #         style={"font-size": "15px", "color": "rgba(255,255,255,0.6)", "display": "block"},
                #     )

            with solara.v.Html(tag="div", style_="display:flex; flex-direction:column; gap:24px;"):
                FeatureCard(
                    index=1,
                    title="AI MCQ Assessment",
                    description="Test developer skills accurately. Our LLM generates 15 questions across 3 difficulty levels based on the selected domain.",
                    tech_stack=["LLM Integration", "Automated Grading", "Dynamic Difficulty"],
                    highlight_label="✨ WHY IT'S UNIQUE",
                    highlight_text="Instantly computes a global developer percentile based on a weighted scoring curve, replacing subjective interviews with objective metrics.",
                    accent="#0088ff", # Blue
                    route="/assessment"
                )

                FeatureCard(
                    index=2,
                    title="Member Management",
                    description="Organise perfect hackathon teams. Create profiles and assign domains to sync your entire team's skills in one place.",
                    tech_stack=["Team Sync", "Role Management", "Centralized DB"],
                    highlight_label="✨ WHY IT'S UNIQUE",
                    highlight_text="Acts as a central nervous system for your hackathon, cleanly separating frontend, backend, and AI specialists.",
                    accent="#00ffcc", # Teal
                    route="/members"
                )

                FeatureCard(
                    index=3,
                    title="Repo Judge",
                    description="Share your GitHub repository and get an international hackathon judge's critical feedback. Understand exactly where your code needs improvement.",
                    tech_stack=["GitHub Actions", "Static Analysis", "AI Code Review"],
                    highlight_label="✨ WHY IT'S UNIQUE",
                    highlight_text="Simulates a real hackathon judge's perspective, pointing out exact architectural flaws and code quality issues before you submit.",
                    accent="#0088ff", # Blue
                    route="/repo-judge"
                )
                
                FeatureCard(
                    index=4,
                    title="Project Ideas Generator",
                    description="Stuck on what to build? Enter a theme and get the top 5 industry-standard resume projects and 5 winning hackathon ideas instantly.",
                    tech_stack=["LangChain", "Ollama", "Structured Output"],
                    highlight_label="✨ WHY IT'S UNIQUE",
                    highlight_text="Uses LangChain and Ollama to guarantee highly relevant, structured, and technically impressive ideas tailored precisely to your input.",
                    accent="#00ffcc", # Teal
                    route="/project-suggest"
                )