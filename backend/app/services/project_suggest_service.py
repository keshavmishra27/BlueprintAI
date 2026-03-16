"""
project_suggest_service.py
--------------------------
Given a theme / domain, asks the local Ollama LLM to return
structured JSON with:
  • 5 industry-grade resume project ideas
  • 5 hackathon-winning project ideas
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def suggest_projects(theme: str) -> dict:
    """
    Call Ollama to generate project suggestions for the given theme.
    Returns a dict with keys `resume_projects` and `hackathon_projects`.
    """
    from .llm_factory import invoke_hybrid_llm
    from langchain_core.messages import SystemMessage, HumanMessage

    system_prompt = """{
"resume_projects": [
{
"name": "ML System with Measurable Impact",
"enhanced_prompt": "You are an expert career-project generator. Produce a single project idea suitable for a FAANG resume. Requirements: include a catchy title; a 2-3 sentence concrete description that explains the problem, approach, and measurable outcome; a modern tech stack (libraries, infra, languages); a one-line USP (why it stands out); 2 example resume bullets with quantified impact (use real-looking metrics like latency reduction %, model AUC, cost saved, throughput gains); minimum viable product (MVP) deliverables; suggested stretch goals for production-readiness (monitoring, CI/CD, A/B tests). Ensure the idea is realistic to implement by a single developer or small team within 2-6 months and demonstrates system design, scalability, and ownership."
},
{
"name": "End-to-End Data Engineering Pipeline",
"enhanced_prompt": "Generate a FAANG-ready data engineering project. Include: title; 2-3 sentence description (data sources, pipeline architecture, transformations, intended business insight); modern stack (ingestion, orchestration, storage, query layer); USP focusing on scale/cost/latency tradeoffs; 2 resume bullets with exact KPIs (e.g., reduced ETL runtime from X to Y, enabled Z analysts to query data, cost per TB); MVP checklist (sample dataset, orchestration DAG, dashboard); production enhancements (partitioning, schema evolution, DR, infra-as-code). Keep it feasible and demonstrative of distributed systems knowledge."
},
{
"name": "Latency-Sensitive Distributed System",
"enhanced_prompt": "Produce a systems project tailored for FAANG interviews. Require: title; concise description of a distributed service (API gateway, caching, load-balancing) and the problem it solves; recommended stack (language, RPC framework, caching, observability tools); USP highlighting latency, availability, or throughput wins; 2 resume bullets with measured improvements (p99 latency lowered from Xms to Yms, SLO attainment, capacity improved); architecture diagram summary in text; MVP components (benchmarks, failure-injection tests, deployment script). Emphasize design decisions and trade-offs."
},
{
"name": "Real-world NLP Application with Evaluation",
"enhanced_prompt": "Create an NLP project that looks strong on a FAANG resume. Include: title; 2-3 sentence description (task, data, business value); stack (pretrained models, tokenizers, fine-tuning infra, evaluation metrics); USP (novel data augmentation, latency-accuracy tradeoff, domain adaptation); 2 resume bullets with metrics (F1/AUC improvement vs baseline, inference latency, throughput); deliverables (cleaned dataset, training pipeline, evaluation notebooks, small web demo); production hardening suggestions (quantization, monitoring, explainability)."
},
{
"name": "End-to-End MLOps Workflow",
"enhanced_prompt": "Design an MLOps project ideal for FAANG resumes. Provide: title; 2-3 sentence description (from data to deployment to monitoring); stack (data versioning, model registry, CI/CD, serving); USP (reproducibility, automated rollback, data drift detection); 2 resume bullets (reduced model deployment time, percent of models with automated tests, rollback frequency reduction); MVP (train pipeline, model registry entry, simple REST endpoint); production add-ons (canary rollout, feature store integration, SLI/SLO setup)."
},
{
"name": "Security/Privacy-Focused Engineering Project",
"enhanced_prompt": "Propose a privacy/security project suitable for FAANG resumes. Must include: title; 2-3 sentence description of the threat or privacy problem and the solution (e.g., differential privacy, secure enclaves, threat detection pipeline); tech stack (crypto libs, secure infra, SIEM, logging); USP (provable guarantees, low overhead, compliance support); 2 resume bullets with measurable outcomes (reduced risk score, latency overhead, compliance readiness); MVP (PoC, threat model, tests); production steps (audit process, key management)."
},
{
"name": "Productivity/Tooling Project that Scales",
"enhanced_prompt": "Create a developer-productivity or tooling project for FAANG resumes. Include: title; 2-3 sentence description (what developer/productivity pain it removes and how); stack (IDE plugin, CLI, web dashboard, backend); USP (measurable developer time saved, integrates with common infra); 2 resume bullets with impact metrics (reduced onboarding time, CI failure rate drop); deliverables (installer, usage docs, telemetry); productionization (auth, metrics, rollout plan)."
},
{
"name": "Full-Stack Impact Product with Users",
"enhanced_prompt": "Suggest a full-stack product suitable for resumes. Contains: title; 2-3 sentence description (user problem, key features, business metric targeted); tech stack (frontend framework, backend, DB, deployment); USP (user adoption, retention mechanism, data-driven feature); 2 resume bullets with user-focused KPIs (MAUs, retention %, conversion lift); MVP (auth, core feature, basic analytics); enhancements (AB testing, scalability, analytics pipeline). Ensure project demonstrates product sense and measurable business impact."
}
],
"hackathon_projects": [
{
"name": "Rapid-Proof-of-Concept AI Demo",
"enhanced_prompt": "You are a hackathon mentor producing high-impact 24–48 hour project prompts. For each idea output: title; 2-3 sentence description (what the demo does and why it's novel); tech stack optimized for quick wins (hostable serverless or lightweight docker stack, pretrained models if applicable); USP (what makes it demo-worthy and judge-appealing); MVP checklist (3 demoable features); pitch points (one-line elevator pitch, 30-second demo script); stretch features for additional points. Prioritize visual/audible demos, simple datasets, low setup friction."
},
{
"name": "Social Good + ML Hack",
"enhanced_prompt": "Produce a hackathon-ready social-impact project idea. Include: title; 2-3 sentence description emphasizing social benefit and novelty; stack choices for rapid development; USP (clear impact + measurable demo metric); MVP features (data ingestion, model/demo, visualization); judge pitch (impact metric, scalability, feasibility); suggestions to collect quick user validation or simulated data. Make the problem simple to understand and emotionally compelling."
},
{
"name": "Hardware + Software Combo (Prototype)",
"enhanced_prompt": "Generate a hardware-software hackathon idea suitable for prototypes. Provide: title; 2-3 sentence description (device + cloud/mobile integration); recommended components (cheap sensors, microcontroller, gateway); stack for quick demonstration (edge inference, mobile dashboard); USP (novel real-world sensing or control loop); MVP checklist (prototype wiring, demo app, short validation); pitch angle focused on novelty and real-world applicability. Keep cost and complexity low for 48-hour build."
},
{
"name": "Collaboration/Productivity Hack with Viral Potential",
"enhanced_prompt": "Come up with a hackathon project that demonstrates product-market fit and is viral. Include: title; 2-3 sentence description (core loop for sharing/collaboration); stack (real-time sync, auth, web/mobile); USP (why it could go viral or be adopted internally by teams); MVP features (real-time demo, share link, basic analytics); pitch script emphasizing user growth and retention. Prioritize easy onboarding for judges to try during demo."
},
{
"name": "Optimization/Operations Automation",
"enhanced_prompt": "Propose an ops/automation hackathon project that shows measurable efficiencies. Provide: title; 2-3 sentence description (what process is automated and expected savings); stack (workflow engine, cron, serverless); USP (clear time/cost reduction metric demonstrable in demo); MVP (automation script, dashboard, before/after metric); demo pitch and steps to validate gains. Make the automation concrete and believable in a short demo."
},
{
"name": "Data Visualization & Insight Generator",
"enhanced_prompt": "Create a hackathon project centered on rapid insights. Include: title; 2-3 sentence description (data source and novel insight generation); stack (ETL-lite, visualization libs, simple ML); USP (interactive insight that non-technical judges can understand); MVP checklist (sample dataset, interactive dashboard, one derived insight); elevator pitch and 60-second demo script. Emphasize storytelling with data in the demo."
},
{
"name": "Open API / Integration Builder",
"enhanced_prompt": "Design a hackathon project that showcases integration skills and practical value. Provide: title; 2-3 sentence description (which platforms are integrated and the workflow automated); stack (OAuth flows, backend glue, serverless functions); USP (solves a common cross-tool friction and is easily demoable); MVP (auth with one platform, workflow run, UI to trigger); pitch focusing on time saved and extensibility. Keep authentication and rate-limit handling minimal for quick build."
},
{
"name": "Explainability & Debugging Tool for ML",
"enhanced_prompt": "Suggest a hackathon project that builds a small explainability/debugging tool for ML models. Include: title; 2-3 sentence description (what model types it supports and the core UX); stack (model inspection libs, small backend, visualization); USP (helps non-experts understand model failures in the demo); MVP features (upload model, visualize attributions, show failure case); pitch and 30-second demo steps. Prioritize clarity and judge-understandable outputs."
}
]
}
"""

    user_prompt = f"""Use this prompt with an LLM to generate high-quality project ideas. Replace {theme} with the actual theme(s) you want (e.g., "edge ML", "sustainable manufacturing", "fintech", "healthcare AI").

---
You are a creative, practical project-idea generator and career/hackathon mentor. For the theme(s): {theme}, generate **5 resume-grade projects** and **5 hackathon-winning projects** that are realistic, high-impact, and tailored to either (a) appear on a FAANG-level resume or (b) win major international hackathons.

Return ONLY this exact JSON structure (no extra text, no commentary):

{{
  "resume_projects": [
    {{
      "title": "...",
      "description": "...",
      "tech_stack": ["...", "..."],
      "why_great_for_resume": "..."
    }}
    // 5 objects total
  ],
  "hackathon_projects": [
    {{
      "title": "...",
      "description": "...",
      "tech_stack": ["...", "..."],
      "why_it_wins": "..."
    }}
    // 5 objects total
  ]
}}

Strict content rules (must follow these exactly):
1. Output must be valid JSON UTF-8, parseable, and match the schema above. No extra keys, no comments.
2. Each list must contain exactly 5 objects.
3. Fields:
   - title: a catchy, ≤8-word title.
   - description: 2–3 sentences (concise, concrete). For resume_projects, include the problem, approach, and one measurable or demonstrable outcome (e.g., latency reduced X%, model AUC, users served, cost saved). For hackathon_projects, include what will be demoed in ≤48–72 hours and the visible metric or UX that impresses judges.
   - tech_stack: 3–6 realistic, modern tools/frameworks/languages (order by importance).
   - why_great_for_resume / why_it_wins: 1–2 sentences. For resume items, explain precisely which FAANG skills it showcases (system design, scalability, ML ops, production infra, edge cases, metrics you can cite in bullets). For hackathon items, explain the judge-winning USP (novelty, social impact, demoability, visual wow factor, business viability).
4. Feasibility constraints:
   - Each resume project MUST be implementable by a single developer or a small team within ~2–6 months and must demonstrate ownership + system-level thinking.
   - Each hackathon project MUST be demoable in a 24–72 hour build window with a clear MVP and a short demo script implied by the description.
5. Content quality constraints:
   - Avoid vague buzzwords. Every project must include at least one concrete metric/claim the builder could realistically achieve or demonstrate in a portfolio (if numeric, keep reasonable magnitudes).
   - Cover diverse subtopics inside {theme} (different problem types / technical angles).
   - Make tech stacks practical and complementary (don’t pair mutually exclusive or redundant tools).
   - Do not use filler options like "TBD" or "many options".
6. Tone & language: concise, professional, unambiguous. Use active verbs and measurable outcomes.
7. Example replacements: if {theme} is multi-topic (e.g., "edge ML + privacy") spread the 10 projects across those subthemes.

Do not output anything other than the JSON object above."""

    response = invoke_hybrid_llm([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ], temperature=0.7)
    raw = response.content.strip()

    # Strip markdown fences if the model wraps them
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()

    try:
        data = json.loads(raw)
        if "resume_projects" in data and "hackathon_projects" in data:
            return data
    except Exception:
        pass

    # Fallback when parsing fails
    return {
        "resume_projects": [
            {
                "title": "Could not parse — please retry",
                "description": raw[:300] if raw else "No response from model.",
                "tech_stack": [],
                "why_great_for_resume": "",
            }
        ],
        "hackathon_projects": [
            {
                "title": "Could not parse — please retry",
                "description": raw[:300] if raw else "No response from model.",
                "tech_stack": [],
                "why_it_wins": "",
            }
        ],
    }
