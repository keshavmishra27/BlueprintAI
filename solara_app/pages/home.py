from pathlib import Path
import solara
from solara_app.components import CountdownTerminal
HOME_CSS = """
.feature-section:hover {
    transform: translateX(10px) !important;
}
.feature-section {
    transition: transform 0.3s ease;
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
    background: linear-gradient(to right bottom, #1e293b 20%, #64748b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.text-gradient-teal {
    background: linear-gradient(135deg, #00ffcc 0%, #0088ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 15px rgba(0,255,204,0.4));
}
.bg-grid {
    position: fixed; inset: 0; z-index: -2;
    background-size: 40px 40px;
    background-image:
        linear-gradient(to right, rgba(0, 0, 0, 0.05) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(0, 0, 0, 0.05) 1px, transparent 1px);
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
    opacity: 0.3;
}
.orb-1 { width: 300px; height: 300px; background: rgba(0, 255, 204, 0.2); top: 10%; left: 15%; animation-delay: 0s; }
.orb-2 { width: 400px; height: 400px; background: rgba(0, 136, 255, 0.15); bottom: 10%; right: 10%; animation-delay: -5s; }
.orb-3 { width: 250px; height: 250px; background: rgba(139, 92, 246, 0.15); top: 40%; left: 50%; transform: translateX(-50%); animation: float 15s ease-in-out infinite reverse; }
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
    background: rgba(0,0,0,0.05); color: #1e293b;
    border: 1px solid rgba(0,0,0,0.1);
    backdrop-filter: blur(10px);
}
.cta-secondary:hover {
    background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.4);
    transform: translateY(-2px);
}
"""
@solara.component
def FeatureSection(index: int, title: str, description: str, highlight_text: str, accent: str, route: str):
    with solara.v.Html(
        tag="div",
        class_="feature-section fade-in-up",
        attributes={"onclick": f"window.location.href='{route}'"},
        style_=(
            f"animation-delay:{index * 0.1}s;"
            "margin-bottom:60px; width:100%; display:block;"
            "cursor:pointer; padding-left:20px;"
            f"border-left: 4px solid {accent};"
            "background: transparent;"
        ),
    ):
        solara.v.Html(
            tag="h2",
            style_=f"font-size:32px; font-weight:800; color:{accent}; margin-bottom:16px; letter-spacing:-0.5px;",
            children=[title]
        )
        solara.v.Html(
            tag="p",
            style_="font-size:18px; color:#475569; line-height:1.6; margin-bottom:24px; max-width:800px;",
            children=[description]
        )
        with solara.v.Html(
            tag="div",
        ):
            solara.v.Html(
                tag="h3",
                style_="font-size:20px; font-weight:700; color:#1e293b; margin-bottom:12px;",
                children=["Why it's unique:"]
            )
            solara.v.Html(
                tag="p",
                style_="font-size:16px; color:#64748b; line-height:1.6; max-width:800px;",
                children=[highlight_text]
            )
@solara.component
def Page():
    solara.Title("Group Maker | Home")
    CountdownTerminal()
    solara.Style(Path(__file__).parent.parent / 'assets' / 'custom.css')
    solara.HTML(tag="style", unsafe_innerHTML=f"""
        .v-application, .v-application--wrap, .v-main, .v-main__wrap, .v-sheet {{
            background-color: #A4C3B2 !important;
            background: #A4C3B2 !important;
        }}
        .theme--light.v-sheet {{ background-color: #A4C3B2 !important; }}
        body {{
            background-color: #A4C3B2 !important;
            background: #A4C3B2 !important;
            margin: 0;
            min-height: 100vh;
        }}
        {HOME_CSS}
    """)
    with solara.v.Html(
        tag="div",
        style_=(
            "min-height:100vh;"
            "background: #A4C3B2;"
            "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"
            "color:#1e293b;"
            "padding-bottom:100px;"
            "box-sizing:border-box;"
            "position:relative;"
            "overflow-x:hidden;"
        ),
    ):
        solara.v.Html(tag="div", class_="bg-grid")
        solara.v.Html(tag="div", class_="glowing-orb orb-1")
        solara.v.Html(tag="div", class_="glowing-orb orb-2")
        solara.v.Html(tag="div", class_="glowing-orb orb-3")
        with solara.v.Html(tag="div", style_="max-width:1000px; margin:0 auto; padding:80px 24px 40px; position:relative; z-index:1;"):
            with solara.v.Html(tag="div", style_="text-align:center; margin-bottom:80px;", class_="fade-in-up", attributes={"style": "animation-delay: 0.1s;"}):
                with solara.v.Html(tag="div", class_="pill-badge"):
                    solara.v.Html(tag="span", children=["The Ultimate AI Engineering Platform"])
                with solara.v.Html(tag="h1", style_="font-size: clamp(48px, 8vw, 84px); font-weight: 800; line-height: 1.1; margin-bottom: 24px; letter-spacing:-1px;"):
                    solara.v.Html(tag="span", class_="text-gradient", children=["Build Better Teams. "])
                    solara.v.Html(tag="br")
                    solara.v.Html(tag="span", class_="text-gradient-teal", children=["Ship Faster Code."])
                solara.Text(
                    "Manage top developer profiles, auto-grade technical skills with our AI Assessment, "
                    "and review complex codebases instantly just like a real hackathon judge.",
                    style={
                        "color": "#475569", "font-size": "clamp(18px, 2vw, 22px)",
                        "line-height": "1.6", "margin-bottom": "40px", "display": "block",
                        "max-width": "800px", "margin-left": "auto", "margin-right": "auto",
                        "font-weight": "400"
                    },
                )
                with solara.v.Html(tag="div", style_="display:flex; justify-content:center; gap:20px; flex-wrap:wrap;"):
                    solara.v.Html(
                        tag="button",
                        class_="cta-button cta-primary",
                        attributes={"onclick": "window.location.href='/assessment'"},
                        children=["Start Your Assessment "]
                    )
                    solara.v.Html(
                        tag="button",
                        class_="cta-button cta-secondary",
                        attributes={"onclick": "window.location.href='/members'"},
                        children=["Explore Member Hub"]
                    )
            with solara.v.Html(
                tag="div",
                style_=(
                    "display:flex; align-items:center; gap:16px; margin-bottom:32px;"
                    "padding-bottom:16px; border-bottom:1px solid rgba(0,0,0,0.05);"
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
                )
            with solara.v.Html(tag="div", style_="display:flex; flex-direction:column; gap:8px; margin-top:40px;"):
                FeatureSection(
                    index=1,
                    title="AI MCQ Assessment",
                    description="CrewAI writes and reviews 15 MCQs (5 easy / 5 medium / 5 hard) for your domain.",
                    highlight_text="Percentile is computed against real prior quiz scores in the same domain—not a fake formula.",
                    accent="#0088ff",
                    route="/assessment"
                )
                FeatureSection(
                    index=2,
                    title="Member Management",
                    description="Organise perfect hackathon teams. Create profiles and assign domains to sync your entire team's skills in one place.",
                    highlight_text="Acts as a central nervous system for your hackathon, cleanly separating frontend, backend, and AI specialists.",
                    accent="#00ffcc",
                    route="/members"
                )
                FeatureSection(
                    index=3,
                    title="Repo Judge",
                    description="GitHub archive + ruff/bandit static analysis, then a 3-agent CrewAI jury (code, security, mentor).",
                    highlight_text="Static-only review with persisted results—includes coding-style summary in the verdict JSON.",
                    accent="#0088ff",
                    route="/repo-judge"
                )
                FeatureSection(
                    index=4,
                    title="Project Ideas Generator",
                    description="CrewAI resume and hackathon mentors search the web for competitors, then propose 5+5 ideas.",
                    highlight_text="Structured JSON with tech stacks and differentiation vs named existing products.",
                    accent="#00ffcc",
                    route="/project-suggest"
                )
                FeatureSection(
                    index=5,
                    title="SWOT Analysis",
                    description="Run a CrewAI SWOT for your startup idea or portfolio project with live search context.",
                    highlight_text="Strategist + reviewer agents produce strengths, weaknesses, opportunities, threats, and action items.",
                    accent="#7c3aed",
                    route="/swot"
                )