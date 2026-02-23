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
    "senior":       "#7c3aed",
    "intermediate": "#0891b2",
    "junior":       "#059669",
}


@solara.component
def MemberRow(member: dict):
    cat   = member.get("category", "?")
    color = CATEGORY_COLOR.get(cat.lower(), "#6b7280")
    with solara.Row(
        justify="space-between",
        style="padding:8px 4px; border-bottom:1px solid #f0f0f0;",
    ):
        with solara.Row(style="gap:12px;"):
            solara.Text(member["name"], style="font-weight:500; font-size:14px;")
            solara.Text(
                cat,
                style=(
                    f"font-size:11px; padding:2px 8px; border-radius:12px;"
                    f"background:{color}22; color:{color}; font-weight:600;"
                ),
            )
        solara.Button(
            "✕",
            on_click=lambda: delete_member(member["id"], member["name"]),
            small=True,
            icon=True,
            style="color:#ef4444;",
        )


@solara.component
def DomainSection(domain_name: str, members: list):
    total = len(members)
    with solara.Card(style="margin-bottom:16px;"):
        with solara.Row(justify="space-between"):
            solara.Text(
                f"🏷️ {domain_name}",
                style="font-weight:700; font-size:16px; color:#4f46e5;",
            )
            solara.Text(
                f"{total} member{'s' if total != 1 else ''}",
                style="font-size:12px; color:#888;",
            )
        if not members:
            solara.Text("No members in this domain.", style="color:#aaa; font-size:13px;")
        else:
            for m in members:
                MemberRow(m)


@solara.component
def DomainChips():
    """Domain filter chips at the top."""
    with solara.Row(style="flex-wrap:wrap; gap:8px; margin-bottom:16px;"):
        # "All" chip
        all_active = selected_domain.value is None
        solara.Button(
            "🌐 All Domains",
            on_click=clear_domain,
            color="primary" if all_active else "default",
            small=True,
            outlined=not all_active,
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
            )


# Main Page

@solara.component
def Page():
    solara.Title("Members")

    def on_mount():
        fetch_domains()
        fetch_all_by_domain()

    solara.use_effect(on_mount, [])

    with solara.Column(style="max-width:860px; margin:0 auto; padding:24px;"):
        solara.Markdown("# 👥 Members")

        # Domain filter chips
        DomainChips()

        # Add Member Form
        with solara.Card("➕ Add New Member"):
            with solara.Row():
                solara.InputText("Name", value=name_input, style="flex:1;")
                solara.InputText(
                    "Category  (senior / intermediate / junior)",
                    value=category_input,
                    style="flex:1;",
                )

            # Domain selection
            if domains.value:
                solara.Text("Assign to Domain(s):", style="font-weight:600; font-size:13px; margin-top:8px;")
                with solara.Div(style="display:flex; flex-wrap:wrap; gap:6px; margin:6px 0;"):
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
                        )
            else:
                solara.Text("No domains available yet.", style="color:#aaa; font-size:12px;")

            solara.Button(
                "Add Member",
                color="primary",
                on_click=add_member,
                disabled=loading.value,
                style="margin-top:8px;",
            )

        if status_msg.value:
            solara.Text(status_msg.value, style="margin:6px 0;")

        # Refresh button
        with solara.Row(justify="space-between", style="margin-top:8px;"):
            if selected_domain.value:
                solara.Markdown(
                    f"### Members of **{selected_domain.value['name']}**"
                    f" ({len(members_in_domain.value)})"
                )
            else:
                total = sum(len(d["members"]) for d in all_by_domain.value)
                solara.Markdown(f"### All Members ({total})")
            solara.Button("🔄 Refresh", on_click=refresh, outlined=True, small=True)

        if loading.value:
            solara.Text("Loading…", style="color:#888;")
            return

        # Single domain view
        if selected_domain.value:
            if not members_in_domain.value:
                solara.Text(
                    "No members in this domain yet.",
                    style="color:#aaa; font-size:14px;",
                )
            else:
                for m in members_in_domain.value:
                    MemberRow(m)

        # All domains view
        else:
            if not all_by_domain.value:
                solara.Text(
                    "No domains found. Add members and assign them to domains first.",
                    style="color:#aaa;",
                )
            else:
                for domain_data in all_by_domain.value:
                    DomainSection(
                        domain_data["domain_name"],
                        domain_data["members"],
                    )
