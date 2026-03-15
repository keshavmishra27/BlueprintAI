"""
idea_validator_service.py
--------------------------
Backend logic for validating project ideas against existing solutions
and identifying unique market gaps or loopholes.
"""

import json
import logging
from .llm_factory import invoke_hybrid_llm
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

def check_similar_ideas(idea: str) -> dict:
    """
    Asks the LLM to search its knowledge base for projects, products, or startups
    that are similar to the user's idea.
    """
    system_prompt = """You are an expert market researcher, startup analyst, and patent-scout with experience in technical prior-art search and India patent practice. 
Input (always provided): 
- "idea_title": short title of the idea
- "idea_description": 2–6 paragraphs (technical + user/market context)
- "domain": e.g., "AI", "FinTech", "Healthcare"
- optional: "target_country":"IN" or other countries (default: IN)

TASK: produce a rigorous, evidence-backed refinement of the idea that (1) finds real similar projects/startups/open-source work, (2) identifies concrete loopholes or gaps in those projects that the user's idea can close, and (3) recommends technical changes and claimable features that would raise the idea's novelty and patentability in India.

REQUIREMENTS — OUTPUT: **Return ONLY valid JSON** with the top-level key `similar_projects` and the additional keys shown in the schema below. No extra text.

MANDATORY BEHAVIOR:
1. Use web searches and patent databases (InPASS / IP India, Google Patents, Espacenet, WIPO) and include source URLs for every claim. Include the search date (ISO 8601) for each source.
2. For each similar project, show evidence: 1–2 short quoted excerpts (≤30 words each) from README/paper/patent + URL + publication/filing date.
3. When stating similarity/difference, reference specific technical modules, algorithms, architectures, UI flows, or data sources—always attach file paths or section titles from the source when available.
4. Perform a patentability triage for India (novelty, inventive step / non-obviousness, industrial applicability).
   - Use Indian patentability standards and point to at least one authoritative source (e.g., IP India guidelines).
5. Check open-source licenses and freedom-to-operate concerns for any OSS you cite. Flag license types (MIT, GPL, Apache, etc.) and whether they block commercial/patent actions.
6. If you detect potential security, privacy, or ethical red flags, call them out and give mitigation steps.
7. Do NOT fabricate facts. If you cannot verify something, label it "not_verified" and explain why.

OUTPUT JSON SCHEMA (required keys):
{
  "similar_projects": [
    {
      "name": "<project/product/startup/patent title>",
      "type": "product|open-source|startup|patent|paper",
      "overview": "<one-paragraph summary>",
      "evidence": [
         {"quote":"<≤30 words>", "source_url":"https://...", "date":"YYYY-MM-DD"}
      ],
      "comparison": "<concise analysis: similarities and precise differences>",
      "license_or_ip": "<license type or patent details or 'none'>",
      "relevance_score": 0-100
    }
  ],
  "gap_and_loopholes": [
    {
      "id":"g1",
      "title":"Short gap title",
      "description":"Explain the concrete loophole or unmet need (technical + market).",
      "evidence_refs":["<similar_project.name>","<URL>"],
      "impact_if_closed":"Quantified or qualitative impact (user, market, safety)"
    }
  ],
  "patentability_assessment": {
    "novelty_summary":"Is the idea novel vs found prior art? (yes/no/partial) + short reasoning",
    "inventive_step_summary":"Does the idea show inventive step vs obviousness? (yes/no/partial) + reasoning with cited references",
    "industrial_applicability":"Yes/No + reasoning",
    "blocking_prior_art": [ {"patent_id":"", "summary":"", "relevance":"high|medium|low", "url":""} ],
    "freedom_to_operate_risks": [ {"issue":"license or patent clash", "evidence_url":"", "severity":"high|medium|low"} ],
    "overall_patentability_score": 0-100
  },
  "recommended_novel_modifications": [
    {
      "id":"m1",
      "short_title":"Short summary of modification",
      "technical_description":"Detailed technical change (algorithms, data flows, sensors, hardware, protocols) — enough to be claimable",
      "why_it_changes_patentability":"Explain how this adds novelty/inventive step vs cited art",
      "implementation_notes":"Feasible tech stack, approximate dev effort hours, minimal data required",
      "potential_claims_plain":"1–3 plain-language independent claim candidates (one-liners each)",
      "potential_claims_legal_style":"1–3 claim-like statements suitable for drafting into claims (technical language)"
    }
  ],
  "validation_and_proof_plan": {
    "experiments_to_prove_novelty":[
      {"name":"test_1", "objective":"what it proves", "steps":"short steps", "expected_result":"metric to show"}
    ],
    "benchmarks_and_datasets":["explicit public datasets or synthetic plan"],
    "prototype_spec":"minimum artifacts to build to demonstrate inventive step (code + data + hardware if any)"
  },
  "commercial_and_filing_advice": {
    "recommended_ip_route":"provisional (IN) / PCT / direct IN / utility model (if applicable) etc.",
    "recommended_patent_classes_ipc":"list likely IPC/Cooperative Patent Classification codes",
    "estimated_time_and_costs_in_INR":"ballpark for provisional + formal filing in India",
    "recommended_countries_for_priority":"[\"IN\",\"US\",\"EP\"] and rationale",
    "non-patent_protections":"trade secrets, copyright, trademarks, contract terms"
  },
  "actionable_next_steps_for_student": [
    "one-line checklist items (e.g., create README with reproducible steps; remove key leaks; run specified experiments; consult patent attorney with artifact X)"
  ],
  "search_queries_and_sources_used": [
    {"query":"<exact search query string>","engine":"Google Patents|InPASS|Espacenet|Google|arXiv","date":"YYYY-MM-DD","top_results":["url1","url2","url3"]}
  ],
  "notes_and_limitations":"Any limitations of the search/assessment (e.g., paywalled patents not accessible, language barriers, time-limited search)."
}

ADDITIONAL RULES FOR AGENT:
- Prioritize Indian patents and filings first, then global patents, then academic papers, then OSS and commercial products.
- For every "recommended_novel_modification", include a realistic estimate of development effort (hours) and the minimal dataset or hardware needed.
- When drafting "potential_claims_legal_style", keep them technical and avoid legal conclusory language; include elements and essential steps so a patent lawyer can convert them into formal claims.
- If you find an exact prior patent that reads on the idea (direct overlap), mark the idea "likely unpatentable" and provide suggestions to pivot.
- If recommending the use of third-party APIs or datasets that are paid, give free alternatives or a synthetic-data plan.

EXAMPLE OF A SINGLE similar_projects ENTRY (for reference — agent must follow the schema above in output):
{
  "name":"ExampleOCRSplit (startup)",
  "type":"product",
  "overview":"A mobile app that OCRs receipts and suggests splits among group members.",
  "evidence":[{"quote":"'Instant receipt split with OCR'","source_url":"https://example.com","date":"2024-06-01"}],
  "comparison":"Shares OCR+split concept; lacks item-level tax allocation and offline-first processing which the user's idea adds.",
  "license_or_ip":"commercial (no OSS), no known patent listed",
  "relevance_score":78
}

END: produce ONLY the JSON described above when you run. If you cannot access patent databases from the environment, state that in `notes_and_limitations` and continue with other searchable sources. Good luck.
"""

    user_prompt = f"User idea: {idea}\n\nFind similar existing solutions."

    from .llm_factory import invoke_hybrid_llm, extract_json_from_text
    from langchain_core.messages import SystemMessage, HumanMessage

    try:
        response = invoke_hybrid_llm([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ], temperature=0.3)
        raw = response.content.strip()

        return extract_json_from_text(raw)
    except Exception as e:
        logger.error(f"Error checking similar ideas: {e}")
        return {"similar_projects": []}

def refine_idea(idea: str, existing_projects: list) -> dict:
    """
    Analyzes the user's idea against existing projects to find:
    - Uniqueness (if any)
    - Loopholes in existing solutions
    - Proposed solutions to those loopholes
    """
    projects_str = json.dumps(existing_projects, indent=2)
    
    system_prompt = """You are a senior strategic innovation consultant, product designer, and prior-art detective. Input (always provided):
- "idea_title": short string
- "idea_description": 2-6 paragraphs (technical detail + target user + what problem it solves)
- optional: "target_market":"IN" or other (default: global)

TASK: Analyze the user's idea in context of existing projects and produce ONLY valid JSON following the schema below. Prioritize real evidence and actionable outcomes that increase product uniqueness and impact. 

### NOVELTY SCORING RUBRIC (Mandatory)
You MUST apply the following rubric strictly. Avoid "safe" middle scores like 60-70% unless they are specifically justified.
- **0 - 30 (Feature Clone / Direct Overlap):** The idea is nearly identical to an existing project or only adds trivial UI changes.
- **31 - 50 (Incremental Improvement):** The idea uses existing tech to solve the same problem but adds one minor useful feature or better UX.
- **51 - 75 (Partial Structural Novelty):** The idea combines existing tech in a new way or applies it to a substantially different domain with structural changes.
- **76 - 100 (High Novelty / Blue Ocean):** The idea solves a problem that has no direct competitors, or uses a fundamentally new algorithm/architecture that creates a high barrier to entry.

MANDATORY BEHAVIOR:
1. Use web searches and (if available) patent search resources. For every external fact include a source URL and ISO date.
2. For each competitor or related project you cite, include a one-sentence excerpt or paraphrase (≤25 words) and its URL.
3. For each loophole you identify, provide a technical solution and estimate the minimum viable implementation effort in developer-hours.
4. Provide at least two concrete refinement options: one low-effort (quick win) and one high-effort (high differentiation).
5. Provide 2-3 measurable success metrics to validate the refined concept.
6. If privacy, security, or license risks exist, flag them and give mitigation steps.
7. Do not include marketing fluff. Be specific, technical, and actionable.
8. If you cannot access a database or verify something, include that restriction in "notes_and_limitations" and continue.
9. **Explain the specific score chosen in the "rationale" field, referencing the rubric above.**

OUTPUT JSON (required keys and structure):
{
  "uniqueness": {
    "verdict": "'unique' | 'partially_unique' | 'not_unique'",
    "score": 0-100,
    "rationale": "<2-4 sentences referencing compared projects or tech>"
  },
  "similar_projects_examined": [
    {
      "name": "<name>",
      "type": "product|open-source|paper|patent",
      "one_line": "<what it does>",
      "evidence_excerpt": "<≤25 words>",
      "url": "<https://...>",
      "search_date": "YYYY-MM-DD"
    }
  ],
  "loopholes": [
    {
      "issue": "<short title>",
      "description": "<technical + market explanation of the weakness (2-4 lines)>",
      "evidence_refs": ["<similar_projects_examined[i].name>", "<url>"],
      "proposed_solution": {
         "short": "<1-line idea>",
         "technical_details": "<algorithms, architecture, data sources, UI flow — enough to be implemented>",
         "minimal_prototype_tasks": ["task1","task2","task3"],
         "dev_effort_hours": <numeric>,
         "risks_and_mitigations": ["risk1 -> mitigation1", "risk2 -> mitigation2"]
      },
      "expected_impact": "<quantified or qualitative effect on users/market>"
    }
  ],
  "refined_concept": {
     "final_direction": "<1-3 sentence refined concept / pivot>",
     "quick_win_variant": {
        "description": "<what to build fast>",
        "dev_hours": <numeric>,
        "success_metrics": ["metric1:value", "metric2:value"]
     },
     "high_diff_variant": {
        "description": "<big change that yields strong uniqueness>",
        "dev_hours": <numeric>,
        "success_metrics": ["metric1:value", "metric2:value"],
        "patentability_notes": "<brief note: likely/partial/unlikely + why>"
     }
  },
  "implementation_plan_high_level": {
     "milestones": [
       {"name":"MVP","tasks":["..."],"duration_days":<int>},
       {"name":"Validation","tasks":["..."],"duration_days":<int>}
     ],
     "minimal_datasets_or_hardware": ["dataset_or_hw_1","dataset_or_hw_2"]
  },
  "notes_and_limitations": "<search limitations, unverifiable facts, license checks not possible, etc.>"
}

BEHAVIORAL RULES:
- Output ONLY the specified JSON. Nothing else.
- Use plain technical language. No marketing slogans.
- Prioritize projects and patents in the target_market if provided.
- When you provide dev_effort_hours, assume a 2-person student team with intermediate skills.
- Keep evidence URLs short and accessible (no paywalled content unless explicitly necessary).

EXAMPLE output snippet (tiny sample):
{
  "uniqueness": {"verdict":"partially_unique","score":58,"rationale":"Core idea overlaps with X and Y; uniqueness comes from offline compression + federated triage."},
  "loopholes": [
    {"issue":"No offline mode","description":"Competitor X requires cloud only","evidence_refs":["X","https://..."], "proposed_solution":{ "short":"Edge-first model compression","technical_details":"quantize model to 8-bit, use on-device pruning...","minimal_prototype_tasks":["quantize","mobile demo"],"dev_effort_hours":40,"risks_and_mitigations":["accuracy drop -> distillation"]}, "expected_impact":"Allows rural use; increases reach by N%"}
  ],
  "refined_concept": {"final_direction":"Edge-first, privacy-preserving triage with hybrid sync to clinic dashboards", ...},
  "notes_and_limitations":"Search limited to English web pages; patent DB access not available from environment."
}

END: Paste this prompt exactly into your agent. The agent MUST return strict JSON following the schema above. Do you want me to produce a single-line clipboard-friendly version of the Detailed prompt?
"""

    user_prompt = f"""User Idea: {idea}

Existing Similar Projects:
{projects_str}

Perform a gap analysis and refine the concept."""

    from .llm_factory import invoke_hybrid_llm, extract_json_from_text
    from langchain_core.messages import SystemMessage, HumanMessage

    try:
        response = invoke_hybrid_llm([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ], temperature=0.7)
        raw = response.content.strip()

        return extract_json_from_text(raw)
    except Exception as e:
        logger.error(f"Error refining idea: {e}")
        return {
            "uniqueness": {"verdict": "error", "score": 0, "rationale": "Could not analyze at this time."},
            "loopholes": [],
            "refined_concept": {"final_direction": "Please try again later."}
        }
