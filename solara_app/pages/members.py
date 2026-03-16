import solara
import requests
import os
from typing import List

API = os.getenv("API_URL", "http://localhost:8000")

# Reactive state
domains           = solara.reactive([])         # [{id, name}, ...]
selected_domain   = solara.reactive(None)       # None = all; or {id, name}

members_in_domain = solara.reactive([])         # when a domain is selected
all_by_domain     = solara.reactive([])         # [{domain_name, members:[...]}, ...]

# Add-member form
name_input        = solara.reactive("")
category_input    = solara.reactive("")
new_member_domains= solara.reactive([])    # list of domain IDs chosen for new member
status_msg        = solara.reactive("")
loading           = solara.reactive(False)


# Data fetchers
def fetch_domains():
    try:
        r = requests.get(f"{API}/members/domains", timeout=5)
        domains.set(r.json())
    except Exception as e:
        status_msg.set(f"❌ Could not load domains: {e}")


def fetch_for_domain(domain_id: int):
    loading.set(True)
    try:
        r = requests.get(f"{API}/members/", params={"domain_id": domain_id}, timeout=5)
        members_in_domain.set(r.json())
    except Exception as e:
        status_msg.set(f"❌ {e}")
    finally:
        loading.set(False)


def fetch_all_by_domain():
    loading.set(True)
    try:
        r = requests.get(f"{API}/members/by-domain", timeout=5)
        all_by_domain.set(r.json())
    except Exception as e:
        status_msg.set(f"❌ {e}")
    finally:
        loading.set(False)


def refresh():
    """Re-fetch whatever view is currently active."""
    status_msg.set("")
    if selected_domain.value:
        fetch_for_domain(selected_domain.value["id"])
    else:
        fetch_all_by_domain()


def select_domain(domain):
    """Called when user clicks a domain chip."""
    selected_domain.set(domain)
    status_msg.set("")
    if domain:
        fetch_for_domain(domain["id"])


def clear_domain():
    selected_domain.set(None)
    fetch_all_by_domain()


def add_member():
    if not name_input.value.strip() or not category_input.value.strip():
        status_msg.set("⚠️ Please fill in both Name and Category.")
        return
    loading.set(True)
    try:
        body = {
            "name": name_input.value.strip(),
            "category": category_input.value.strip(),
            "domain_ids": new_member_domains.value,
        }
        r = requests.post(f"{API}/members/", json=body, timeout=5)
        if r.status_code == 200:
            d = r.json()
            domain_names = ", ".join(x["name"] for x in d.get("domains", []))
            msg = f"✅ '{d['name']}' added!"
            if domain_names:
                msg += f" Domains: {domain_names}"
            status_msg.set(msg)
            name_input.set("")
            category_input.set("")
            new_member_domains.set([])
            refresh()
        else:
            status_msg.set(f"❌ {r.json().get('detail', r.text)}")
    except Exception as e:
        status_msg.set(f"❌ {e}")
    finally:
        loading.set(False)


def delete_member(member_id: int, member_name: str):
    try:
        r = requests.delete(f"{API}/members/{member_id}", timeout=5)
        if r.status_code == 200:
            status_msg.set(f"🗑️ '{member_name}' deleted.")
            refresh()
        else:
            status_msg.set(f"❌ {r.text}")
    except Exception as e:
        status_msg.set(f"❌ {e}")


# Sub components

CATEGORY_COLOR = {
    "senior":       "#ff00cc",
    "intermediate": "#ff9a9e",
    "junior":       "#fecfef",
}


@solara.component
def MemberRow(member: dict):
    cat   = member.get("category", "?")
    color = CATEGORY_COLOR.get(cat.lower(), "#cbd5e1")
    with solara.v.Html(
        tag="div",
        style_="display:flex; justify-content:space-between; align-items:center; padding:12px 16px; border-bottom:1px solid rgba(255,255,255,0.1); transition:background 0.2s ease;",
    ):
        with solara.v.Html(tag="div", style_="display:flex; align-items:center; gap:16px;"):
            solara.Text(member["name"], style={"font-weight": "600", "font-size": "15px", "color": "#ffffff"})
            solara.Text(
                cat,
                style={
                    "font-size": "11px", "padding": "4px 10px", "border-radius": "12px",
                    "background": f"rgba(255, 255, 255, 0.15)", "color": color, "font-weight": "700",
                    "text-transform": "uppercase", "letter-spacing": "0.5px"
                },
            )
        solara.Button(
            "✕",
            on_click=lambda: delete_member(member["id"], member["name"]),
            small=True,
            icon=True,
            color="error",
            style="min-width:32px; height:32px; border-radius:50%; background:rgba(239, 68, 68, 0.1); border:1px solid rgba(239, 68, 68, 0.3);",
        )


@solara.component
def DomainSection(domain_name: str, members: list, is_unassigned: bool = False):
    total = len(members)
    header_color = "#fecfef" if is_unassigned else "#ff9a9e"
    icon = "📋" if is_unassigned else "🏷️"
    with solara.v.Html(
        tag="div",
        style_=(
            "margin-bottom:24px; padding:24px; border-radius:16px;"
            "background:rgba(10, 25, 40, 0.4); backdrop-filter:blur(16px);"
            "border:1px solid rgba(255, 154, 158, 0.2); box-shadow:0 8px 32px rgba(255, 154, 158, 0.1);"
        )
    ):
        with solara.v.Html(tag="div", style_="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:12px;"):
            solara.Text(
                f"{icon} {domain_name}",
                style={"font-weight": "800", "font-size": "18px", "color": header_color, "letter-spacing": "0.5px"},
            )
            solara.Text(
                f"{total} member{'s' if total != 1 else ''}",
                style={"font-size": "13px", "color": "rgba(255,255,255,0.6)", "font-weight": "600"},
            )
        if not members:
            solara.Text("No members in this domain.", style={"color": "rgba(255,255,255,0.5)", "font-size": "14px", "font-style": "italic"})
        else:
            for m in members:
                MemberRow(m)


@solara.component
def DomainChips():
    """Domain filter chips at the top."""
    with solara.v.Html(tag="div", style_="display:flex; flex-wrap:wrap; gap:12px; margin-bottom:32px;"):
        # "All" chip
        all_active = selected_domain.value is None
        solara.Button(
            "🌐 All Domains",
            on_click=clear_domain,
            color="primary" if all_active else "default",
            small=True,
            outlined=not all_active,
            style=f"border-radius:20px; font-weight:700; {'background:linear-gradient(90deg, #ff416c, #ff4b2b); border:none; color:#fff;' if all_active else 'background:rgba(255,255,255,0.1); color:#fff;'}"
        )
        for d in domains.value:
            is_active = (
                selected_domain.value is not None
                and selected_domain.value["id"] == d["id"]
            )
            solara.Button(
                d["name"],
                on_click=lambda dom=d: select_domain(dom),
                color="primary" if is_active else "default",
                small=True,
                outlined=not is_active,
                style=f"border-radius:20px; font-weight:700; {'background:linear-gradient(90deg, #ff416c, #ff4b2b); border:none; color:#fff;' if is_active else 'background:rgba(255,255,255,0.1); color:#fff;'}"
            )


# Main Page

@solara.component
def Page():
    solara.Title("Members")

    # Ultra-aggressive CSS strictly for this page to destroy Vuetify's background
    solara.HTML(tag="style", unsafe_innerHTML="""
        .v-application, .v-application--wrap, .v-main__wrap {
            background: transparent !important;
        }
        body {
            background-color: #1a0b16 !important;
            margin: 0;
            min-height: 100vh;
        }
        @keyframes gradientMembers {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .custom-status-msg {
            margin-top:20px;
            padding:12px 16px;
            border-radius:8px;
            font-weight:600;
            font-size:14px;
            color:#ffffff;
        }
        .custom-status-success {
            background: rgba(16, 185, 129, 0.2);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .custom-status-error {
            background: rgba(239, 68, 68, 0.2);
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
    """)

    def on_mount():
        fetch_domains()
        fetch_all_by_domain()

    solara.use_effect(on_mount, [])

    with solara.v.Html(
        tag="div",
        style_=(
            "min-height:100vh;"
            "background: linear-gradient(-45deg, #4b134f, #c94b4b, #ff416c, #ff4b2b);"
            "background-size: 400% 400%;"
            "animation: gradientMembers 15s ease infinite;"
            "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"
            "color:#ffffff;"
            "padding-bottom:60px;"
            "box-sizing:border-box;"
        )
    ):
        with solara.v.Html(tag="div", style_="max-width:860px; margin:40px auto; padding:0 24px;"):
            solara.Text("👥 Team Members", style={"font-size": "36px", "font-weight": "900", "color": "#ffffff", "margin-bottom": "32px", "display": "block", "text-shadow": "0 2px 15px rgba(255,65,108,0.5)"})

            # Domain filter chips
            DomainChips()

            # Add Member Form
            with solara.v.Html(
                tag="div",
                style_=(
                    "background:rgba(10, 25, 40, 0.5); backdrop-filter:blur(20px);"
                    "border:1px solid rgba(255, 65, 108, 0.4); border-radius:20px;"
                    "padding:32px; box-shadow:0 12px 40px rgba(255, 75, 43, 0.25);"
                    "margin-bottom:40px;"
                )
            ):
                solara.Text("➕ Add New Member", style={"font-size": "22px", "font-weight": "800", "color": "#ffb199", "margin-bottom": "24px", "display": "block"})
                
                with solara.v.Html(tag="div", style_="display:flex; gap:20px; flex-wrap:wrap; margin-bottom:20px;"):
                    with solara.v.Html(tag="div", style_="flex:1; min-width:250px;"):
                        solara.InputText("Name", value=name_input, style="width:100%;")
                    with solara.v.Html(tag="div", style_="flex:1; min-width:250px;"):
                        solara.InputText(
                            "Category (senior/intermediate/junior)",
                            value=category_input,
                            style="width:100%;",
                        )

                # Domain selection
                if domains.value:
                    solara.Text("Assign to Domain(s):", style={"font-weight": "700", "font-size": "14px", "color": "rgba(255,255,255,0.7)", "margin-bottom": "12px", "display": "block"})
                    with solara.v.Html(tag="div", style_="display:flex; flex-wrap:wrap; gap:10px; margin-bottom:24px;"):
                        for d in domains.value:
                            is_sel = d["id"] in new_member_domains.value
                            def toggle(dom=d):
                                cur = list(new_member_domains.value)
                                if dom["id"] in cur:
                                    cur.remove(dom["id"])
                                else:
                                    cur.append(dom["id"])
                                new_member_domains.set(cur)
                            solara.Button(
                                ("✓ " if is_sel else "") + d["name"],
                                on_click=toggle,
                                color="primary" if is_sel else "default",
                                outlined=not is_sel,
                                small=True,
                                style=f"border-radius:12px; font-weight:600; {'background:linear-gradient(90deg, #ff416c, #ff4b2b); border:none; color:#fff;' if is_sel else 'background:rgba(255,255,255,0.1); color:#fff;'}"
                            )
                else:
                    solara.Text("No domains available yet.", style={"color": "rgba(255,255,255,0.5)", "font-size": "13px", "font-style": "italic", "display": "block"})

                solara.Button(
                    "➕ Add Member",
                    color="primary",
                    on_click=add_member,
                    disabled=loading.value,
                    style="width:100%; padding:14px; font-weight:800; font-size:16px; letter-spacing:1px; border-radius:12px; background:linear-gradient(90deg, #fc4a1a, #f7b733); border:none; color:#000; box-shadow:0 4px 15px rgba(252,74,26,0.4);",
                )

                if status_msg.value:
                    with solara.v.Html(
                        tag="div",
                        attributes={"class": "custom-status-msg " + ("custom-status-success" if '✅' in status_msg.value else "custom-status-error")},
                    ):
                        solara.Text(status_msg.value)

            # Refresh button
            with solara.v.Html(tag="div", style_="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:24px; border-bottom:2px solid rgba(255,255,255,0.1); padding-bottom:16px;"):
                if selected_domain.value:
                    solara.Text(
                        f"Members of {selected_domain.value['name']} ({len(members_in_domain.value)})",
                        style={"font-size": "24px", "font-weight": "800", "color": "#ffb199", "display": "block"}
                    )
                else:
                    total = sum(len(d["members"]) for d in all_by_domain.value)
                    solara.Text(f"All Members ({total} total)", style={"font-size": "24px", "font-weight": "800", "color": "#ffb199", "display": "block"})
                
                solara.Button("🔄 Refresh", on_click=refresh, outlined=True, small=True, style="background:rgba(255,255,255,0.1); color:#fff; border:1px solid rgba(255,255,255,0.3); border-radius:8px;")

            if loading.value:
                solara.Text("⚡ Loading data...", style={"color": "rgba(255,255,255,0.7)", "font-size": "16px", "font-weight": "600", "text-align": "center", "display": "block", "margin-top": "40px"})
                return

            # Single domain view
            if selected_domain.value:
                if not members_in_domain.value:
                    with solara.v.Html(tag="div", style_="text-align:center; padding:40px; background:rgba(0,0,0,0.2); border-radius:16px; border:1px dashed rgba(255,255,255,0.2);"):
                        solara.Text(
                            "No members in this domain yet.",
                            style={"color": "rgba(255,255,255,0.6)", "font-size": "16px", "font-style": "italic", "display": "block"},
                        )
                else:
                    with solara.v.Html(tag="div", style_="background:rgba(10, 25, 40, 0.4); backdrop-filter:blur(16px); border:1px solid rgba(255, 154, 158, 0.2); border-radius:16px; overflow:hidden;"):
                        for m in members_in_domain.value:
                            MemberRow(m)

            # All domains view
            else:
                if not all_by_domain.value:
                    solara.Text(
                        "Loading members… if this persists, check your API connection.",
                        style={"color": "rgba(255,255,255,0.6)", "text-align": "center", "display": "block", "margin-top": "40px"},
                    )
                else:
                    for domain_data in all_by_domain.value:
                        is_unassigned = domain_data.get("domain_id") is None
                        DomainSection(
                            domain_data["domain_name"],
                            domain_data["members"],
                            is_unassigned=is_unassigned,
                        )
