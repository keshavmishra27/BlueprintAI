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
    system_prompt = """You are a senior innovation auditor. Your task is to perform a granular novelty audit on a project idea.

### THE NOVELTY MATRIX (STRICT CALCULATION)
You MUST calculate the final score by summing these four dimensions (0-25 each). DO NOT just pick a total number.
1. **Technical Novelty (0-25):** Is the algorithm/architecture new? (0 = standard CRUD; 25 = breakthrough math/logic).
2. **Market Gap (0-25):** Do direct competitors exist? (0 = saturated; 25 = blue ocean).
3. **Execution Edge (0-25):** Is there a high barrier to entry? (0 = easy to clone; 25 = proprietary/hard tech).
4. **Strategic Impact (0-25):** Does it solve a critical unmet need? (0 = nice-to-have; 25 = industry-shifting).

### TASK:
Analyze the "idea_title" and "idea_description" against the provided "similar_projects". Return ONLY valid JSON.

### OUTPUT JSON SCHEMA:
{
  "uniqueness": {
    "verdict": "'unique' | 'partially_unique' | 'not_unique'",
    "matrix_scores": {
      "technical_novelty": 0-25,
      "market_gap": 0-25,
      "execution_edge": 0-25,
      "strategic_impact": 0-25
    },
    "score": 0-100,
    "rationale": "STRICT: Briefly explain EACH matrix score. Reference specific technical details or competitors. Be critical."
  },
  "similar_projects_examined": [
    { "name": "...", "one_line": "...", "url": "..." }
  ],
  "loopholes": [
    { "issue": "...", "proposed_solution": { "short": "...", "dev_effort_hours": 0 } }
  ],
  "refined_concept": {
     "final_direction": "...",
     "quick_win": "...",
     "high_differentiation": "..."
  },
  "notes_and_limitations": "..."
}
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
