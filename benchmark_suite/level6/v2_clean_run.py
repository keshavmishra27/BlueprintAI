import json
import os
import sys
import time
import hashlib
import requests
import re
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import glob
from dotenv import load_dotenv

load_dotenv(override=True)

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_dir))

from benchmark_suite.schemas import (
    BenchmarkScenario, ExperimentManifest, GenerationLog, BenchmarkMetrics
)
from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.tree.tree_schemas import AgentUncertainty

class AgentGeneration(BaseModel):
    architecture: ArchitectureNode
    uncertainties: List[AgentUncertainty] = []

class BaselineGeneration(BaseModel):
    architecture: ArchitectureNode

def extract_json_from_text(text: str) -> dict:
    if not text:
        return {}
    def clean_json_str(s: str) -> str:
        s = re.sub(r',\s*\}', '}', s)
        s = re.sub(r',\s*\]', ']', s)
        return s
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(clean_json_str(json_match.group(1)))
        except json.JSONDecodeError:
            pass
    start = text.find("{")
    if start != -1:
        end = text.rfind("}")
        if end != -1 and end > start:
            json_str = text[start:end+1]
            json_str_clean = clean_json_str(json_str)
            try:
                return json.loads(json_str_clean)
            except json.JSONDecodeError:
                pass
    return {}

class ExperimentLogger:
    def __init__(self, run_id: str):
        self.results_dir = Path(__file__).parent / "results"
        self.raw_dir = self.results_dir / "raw" / "v2"
        self.metrics_dir = self.results_dir / "metrics"
        self.manifest_dir = self.results_dir / "manifest"
        
        for d in [self.raw_dir, self.metrics_dir, self.manifest_dir]:
            d.mkdir(parents=True, exist_ok=True)
            
        self.raw_file = self.raw_dir / f"generation_{run_id}.jsonl"
        self.metrics_file = self.results_dir / "v2_clean_live_run.csv"
        self.manifest_file = self.manifest_dir / "experiment_manifest.json"
        self.run_id = run_id

        if not self.metrics_file.exists():
            with open(self.metrics_file, "w") as f:
                f.write("Scenario,Baseline_Public_F,Baseline_Real_F,BP_F,Delta_F,UAR,Questions,Irr_Q,Terminals,Oracle_Hit,Unselected_Winner,CGFR,Final_Status\n")

    def write_manifest(self, manifest: ExperimentManifest):
        with open(self.manifest_file, "a") as f:
            f.write(manifest.model_dump_json() + "\n")

    def write_generation_log(self, log: GenerationLog):
        with open(self.raw_file, "a") as f:
            f.write(log.model_dump_json() + "\n")

class LiveAgentBenchmark:
    def __init__(self, scenario_path: Path):
        self.scenario_path = scenario_path
        with open(scenario_path, "r") as f:
            self.scenario = BenchmarkScenario(**json.load(f))
        
        self.scenario_name = Path(scenario_path).stem
        self.run_id = f"v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.scenario_name}"
        self.logger = ExperimentLogger(self.run_id)
        
        self.model = "llama3-70b-8192"
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            print("NO GROQ API KEY FOUND!")
            sys.exit(1)
            
        self.temperature = 0.0
        
        self.cgfr_tracking = {
            "baseline": {"requests": 0, "initial_fails": 0, "recoveries": 0, "final_fails": 0},
            "blueprintai": {"requests": 0, "initial_fails": 0, "recoveries": 0, "final_fails": 0}
        }
        self.ENGINE_URL = "http://127.0.0.1:8000/api/journey"

    def _call_llm(self, system_instruction: str, prompt: str, schema_class, arm: str, generation_id: str, parent_node_id: str = None):
        self.cgfr_tracking[arm]["requests"] += 1
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        sys_prompt = f"{system_instruction}\nOutput ONLY valid JSON according to this schema, with no markdown formatting:\n{schema_class.model_json_schema()}"
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "response_format": {"type": "json_object"}
        }
        
        start_time = time.time()
        try:
            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
            response.raise_for_status()
            res_json = response.json()
            raw_text = res_json['choices'][0]['message']['content']
            latency = (time.time() - start_time) * 1000
            
            response_hash = hashlib.sha256(raw_text.encode()).hexdigest()
            
            gen_log = GenerationLog(
                run_id=self.run_id,
                scenario_id=self.scenario.name,
                arm=arm,
                generation_id=generation_id,
                parent_node_id=parent_node_id,
                model=self.model,
                prompt_hash=prompt_hash,
                response_hash=response_hash,
                raw_response=raw_text,
                attempt=1,
                result="VALID",
                latency_ms=latency,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0
            )
            self.logger.write_generation_log(gen_log)
            
            parsed_dict = json.loads(raw_text)
            parsed = schema_class.model_validate(parsed_dict)
            return parsed
            
        except Exception as e:
            print(f"Error calling LLM: {e}")
            if 'response' in locals() and hasattr(response, 'text'):
                print(f"Response: {response.text}")
            latency = (time.time() - start_time) * 1000
            self.cgfr_tracking[arm]["initial_fails"] += 1
            self.cgfr_tracking[arm]["final_fails"] += 1
            
            gen_log = GenerationLog(
                run_id=self.run_id,
                scenario_id=self.scenario.name,
                arm=arm,
                generation_id=generation_id,
                parent_node_id=parent_node_id,
                model=self.model,
                prompt_hash=prompt_hash,
                raw_response=str(e),
                attempt=1,
                result="GENERATION_FAILURE",
                latency_ms=latency
            )
            self.logger.write_generation_log(gen_log)
            return None

    def run_baseline(self):
        print(f"--- Running Baseline Arm ---")
        prompt = f"Problem: {self.scenario.problem_what}\nWhy: {self.scenario.problem_why}\nHow: {self.scenario.problem_how}\nConstraints: {self.scenario.constraints}\nRequirements: {[r.name for r in self.scenario.requirements]}"
        sys_prompt = "Produce the best architecture you can for this problem."
        
        parsed = self._call_llm(sys_prompt, prompt, BaselineGeneration, "baseline", "gen_baseline_01")
        
        if not parsed or not parsed.architecture:
            return False, False
            
        arch = parsed.architecture.model_dump()
        
        payload_pub = {
            "project_state": {
                "user_idea": {
                    "what": self.scenario.problem_what,
                    "why": self.scenario.problem_why,
                    "how_raw": self.scenario.problem_how,
                    "how_structured": {}
                },
                "current_constraints": self.scenario.constraints,
                "current_requirements": [{"name": r.name, "required": True} for r in self.scenario.requirements]
            },
            "architecture": arch
        }
        res_pub = requests.post(f"{self.ENGINE_URL}/evaluate", json=payload_pub).json()
        base_pub_f = res_pub.get("feasible", False)
        
        real_constraints = self.scenario.constraints + list(self.scenario.hidden_facts_to_reveal.values())
        payload_real = dict(payload_pub)
        payload_real["project_state"]["current_constraints"] = real_constraints
        res_real = requests.post(f"{self.ENGINE_URL}/evaluate", json=payload_real).json()
        base_real_f = res_real.get("feasible", False)
        
        print(f"Baseline Public F: {base_pub_f}, Real F: {base_real_f}")
        return base_pub_f, base_real_f

    def run_blueprintai(self):
        print(f"--- Running BlueprintAI Arm ---")
        prompt = f"Problem: {self.scenario.problem_what}\nWhy: {self.scenario.problem_why}\nHow: {self.scenario.problem_how}\nConstraints: {self.scenario.constraints}\nRequirements: {[r.name for r in self.scenario.requirements]}"
        sys_prompt = "Produce an architecture and candidate uncertainties. The uncertainties should represent assumptions that need clarification from the user."
        
        parsed = self._call_llm(sys_prompt, prompt, AgentGeneration, "blueprintai", "gen_bp_01")
        
        if not parsed or not parsed.architecture:
            return "FAILED", False, False, 0, 0, 0
            
        payload = {
            "session_id": f"{self.scenario_name}-session-v2",
            "project_state": {
                "user_idea": {
                    "what": self.scenario.problem_what,
                    "why": self.scenario.problem_why,
                    "how_raw": self.scenario.problem_how,
                    "how_structured": {}
                },
                "current_constraints": self.scenario.constraints,
                "current_requirements": [{"name": r.name, "required": True} for r in self.scenario.requirements]
            },
            "initial_architecture": parsed.architecture.model_dump(),
            "candidate_uncertainties": [u.model_dump() for u in parsed.uncertainties]
        }
        
        start_res = requests.post(f"{self.ENGINE_URL}/start", json=payload).json()
        
        questions_asked = 0
        irr_q = 0
        gen_counter = 2
        
        while start_res.get("status") == "CONTINUE":
            qtext = start_res.get("selected_uncertainty_text")
            
            if not qtext:
                state = requests.get(f"{self.ENGINE_URL}/{payload['session_id']}/state").json()
                unexplored = [n for n in state["decision_graph"] if n["status"] == "UNEXPLORED_HYPOTHESIS"]
                if not unexplored:
                    break
                node = unexplored[0]
                node_id = node["id"]
                req_question = node.get("question_that_produced_it", "")
                req_answer = node.get("user_answer", "")
                
                branch_prompt = prompt + f"\n[SYSTEM: The user answered {req_answer} to '{req_question}'. Generate the alternative architecture.]"
                parsed_branch = self._call_llm("Generate an alternative architecture reflecting this new reality. No uncertainties needed.", branch_prompt, AgentGeneration, "blueprintai", f"gen_bp_{gen_counter:02d}", parent_node_id=node_id)
                gen_counter += 1
                
                branch_payload = {
                    "session_id": payload["session_id"],
                    "parent_node_id": node_id,
                    "answer": req_answer,
                    "generated_architecture": parsed_branch.architecture.model_dump() if parsed_branch else {},
                    "candidate_uncertainties": [],
                    "is_user_selected": False
                }
                start_res = requests.post(f"{self.ENGINE_URL}/answer", json=branch_payload).json()
                continue

            questions_asked += 1
            print(f"Engine asked: {qtext}")
            
            answer = "I don't have a specific policy on that. Proceed with your best judgment."
            matched = False
            for fact_key, fact_val in self.scenario.hidden_facts_to_reveal.items():
                if fact_key.lower() in qtext.lower() or any(word in qtext.lower() for word in fact_key.lower().split() if len(word) > 4):
                    answer = fact_val
                    matched = True
                    break
                    
            if not matched:
                irr_q += 1
                
            state = requests.get(f"{self.ENGINE_URL}/{payload['session_id']}/state").json()
            waiting = [n for n in state["decision_graph"] if n["status"] == "WAITING_FOR_USER"]
            if not waiting:
                break
            parent_node_id = waiting[0]["id"]
                
            branch_prompt = prompt + f"\nNew Fact Revealed: {answer}"
            parsed_branch = self._call_llm("Update architecture given this new fact.", branch_prompt, AgentGeneration, "blueprintai", f"gen_bp_{gen_counter:02d}", parent_node_id=parent_node_id)
            gen_counter += 1
            
            branch_payload = {
                "session_id": payload["session_id"],
                "parent_node_id": parent_node_id,
                "answer": answer,
                "generated_architecture": parsed_branch.architecture.model_dump() if parsed_branch and parsed_branch.architecture else {},
                "candidate_uncertainties": [u.model_dump() for u in parsed_branch.uncertainties] if parsed_branch and parsed_branch.uncertainties else [],
                "is_user_selected": True
            }
            start_res = requests.post(f"{self.ENGINE_URL}/answer", json=branch_payload).json()
            
        print("Journey Complete.")
        final_status = start_res.get("status", "UNKNOWN")
        bp_best_id = start_res.get("best_path_id")
        
        state = requests.get(f"{self.ENGINE_URL}/{payload['session_id']}/state").json()
        terminals = [n for n in state.get("decision_graph", []) if n.get("status") == "TERMINAL"]
        
        bp_f = False
        oracle_hit = False
        
        for t in terminals:
            if t["id"] == bp_best_id and t.get("architecture", {}).get("candidate_status") == "FEASIBLE":
                bp_f = True
                if "oracle_architecture" in self.scenario.model_dump():
                    o_decisions = self.scenario.oracle_architecture.architectural_decisions
                    t_decisions = t["architecture"].get("architectural_decisions", {})
                    if list(o_decisions.values()) == list(t_decisions.values()):
                        oracle_hit = True
                break
                
        return final_status, bp_f, oracle_hit, questions_asked, irr_q, len(terminals)

    def run(self):
        base_pub_f, base_real_f = self.run_baseline()
        final_status, bp_f, oracle_hit, q_asked, irr_q, terminals = self.run_blueprintai()
        
        delta_f = 1 if (bp_f and not base_real_f) else 0
        uar = 1 if q_asked > 0 and (q_asked - irr_q) > 0 else 0
        
        reqs = self.cgfr_tracking["baseline"]["requests"] + self.cgfr_tracking["blueprintai"]["requests"]
        fails = self.cgfr_tracking["baseline"]["final_fails"] + self.cgfr_tracking["blueprintai"]["final_fails"]
        cgfr = fails / reqs if reqs > 0 else 0.0
        
        unselected_winner = (final_status == "UNSELECTED_WINNER")
        
        res_line = f"{self.scenario_name},{base_pub_f},{base_real_f},{bp_f},{delta_f},{uar},{q_asked},{irr_q},{terminals},{oracle_hit},{unselected_winner},{cgfr:.2f},{final_status}\n"
        print(f"RESULT: {res_line}")
        
        with open(self.logger.metrics_file, "a") as f:
            f.write(res_line)

if __name__ == "__main__":
    scenarios = sorted(glob.glob(str(Path(__file__).parent.parent / "scenarios" / "*.json")))
    for s in scenarios:
        print(f"\n======================================")
        print(f"STARTING SCENARIO: {Path(s).stem}")
        print(f"======================================")
        bench = LiveAgentBenchmark(Path(s))
        bench.run()
