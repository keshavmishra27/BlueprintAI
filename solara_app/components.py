import solara
import threading
import time

@solara.component
def CountdownTerminal():
    count = solara.use_reactive(3)
    visible = solara.use_reactive(True)

    def start_countdown():
        if not visible.value:
            return
            
        def run():
            for i in range(3, 0, -1):
                count.set(i)
                time.sleep(1)
            visible.set(False)
            
        threading.Thread(target=run, daemon=True).start()

    solara.use_effect(start_countdown, [])

    if not visible.value:
        return solara.v.Html(tag="span")

    solara.HTML(tag="style", unsafe_innerHTML="""
        .countdown-container {
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            display: flex; justify-content: center; align-items: center;
            background-color: #030812; font-family: 'Courier New', Courier, monospace;
            z-index: 99999;
        }
        .countdown-window {
            width: 500px; background-color: rgba(10, 15, 20, 0.95);
            border: 1px solid #33ffdb; border-radius: 8px;
            box-shadow: 0 0 20px rgba(0, 255, 204, 0.2); overflow: hidden;
            backdrop-filter: blur(10px);
        }
        .countdown-header {
            background-color: #1a202c; padding: 10px 16px;
            display: flex; gap: 8px; align-items: center;
            border-bottom: 1px solid #2d3748;
        }
        .term-dot { width: 12px; height: 12px; border-radius: 50%; }
        .term-dot.red { background-color: #ff5f56; }
        .term-dot.yellow { background-color: #ffbd2e; }
        .term-dot.green { background-color: #27c93f; }
        .countdown-body {
            padding: 30px; color: #00ffcc; font-size: 16px; line-height: 1.8;
            text-align: center;
        }
        .countdown-number {
            font-size: 48px; font-weight: bold; color: #33ffdb;
            margin: 20px 0; display: block;
            text-shadow: 0 0 15px rgba(51, 255, 219, 0.5);
            animation: pulse-num 1s infinite;
        }
        @keyframes pulse-num {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.1); opacity: 0.8; }
            100% { transform: scale(1); opacity: 1; }
        }
    """)

    with solara.v.Html(tag="div", class_="countdown-container"):
        with solara.v.Html(tag="div", class_="countdown-window"):
            with solara.v.Html(tag="div", class_="countdown-header"):
                solara.v.Html(tag="div", class_="term-dot red")
                solara.v.Html(tag="div", class_="term-dot yellow")
                solara.v.Html(tag="div", class_="term-dot green")
                solara.Text("system@group_maker: ~", style={"color": "#a0aec0", "font-size": "14px", "margin-left": "10px"})
            
            with solara.v.Html(tag="div", class_="countdown-body"):
                solara.Text("Initializing Secure Environment...", style={"display": "block", "font-weight": "bold", "margin-bottom": "8px"})
                solara.Text("Starting in", style={"display": "block"})
                solara.v.Html(tag="span", class_="countdown-number", children=[str(count.value)])
                solara.Text("Please wait...", style={"display": "block", "color": "rgba(0, 255, 204, 0.6)"})
