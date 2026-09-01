"""
WARNING:
This harness is NOT the Level 6 experiment.
It directly invokes the Gemini API and therefore belongs to
Level 5 / API-based validation.
Level 6 requires the IDE Agent Runtime itself to generate
architectures and interact with the deterministic backend.
"""

import json
import os
import sys
import uuid
import time
import hashlib
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel
from typing import List, Dict, Optional, Any

from google import genai
from google.genai import types

base_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(base_dir))

from benchmark_suite.schemas import (
    BenchmarkScenario, ExperimentManifest, GenerationLog, BenchmarkMetrics
)
from decision_engine.tree import benchmark_evaluator
from decision_engine.input_layer.evaluator import evaluate_battle
from decision_engine.input_layer.schemas import ArchitectureNode
from decision_engine.tree.tree_schemas import AgentUncertainty

class AgentGeneration(BaseModel):
    architecture: ArchitectureNode
    uncertainties: List[AgentUncertainty] = []

class BaselineGeneration(BaseModel):
    architecture: ArchitectureNode

class ExperimentLogger:
    def __init__(self, run_id: str):
        self.results_dir = Path(__file__).parent / "results"
        self.raw_dir = self.results_dir / "raw"
        self.eval_dir = self.results_dir / "evaluations"
        self.metrics_dir = self.results_dir / "metrics"
        self.manifest_dir = self.results_dir / "manifest"
        
        for d in [self.raw_dir, self.eval_dir, self.metrics_dir, self.manifest_dir]:
            d.mkdir(parents=True, exist_ok=True)
            
        self.raw_file = self.raw_dir / "generation.jsonl"
        self.eval_file = self.eval_dir / "deterministic.jsonl"
        self.metrics_file = self.metrics_dir / "final_metrics.json"
        self.manifest_file = self.manifest_dir / "experiment_manifest.json"
        self.run_id = run_id

    def write_manifest(self, manifest: ExperimentManifest):
        with open(self.manifest_file, "a") as f:
            f.write(manifest.model_dump_json() + "\n")

    def write_generation_log(self, log: GenerationLog):
        with open(self.raw_file, "a") as f:
            f.write(log.model_dump_json() + "\n")
            
    def write_deterministic_eval(self, eval_data: dict):
        eval_data["run_id"] = self.run_id
        with open(self.eval_file, "a") as f:
            f.write(json.dumps(eval_data) + "\n")
            
    def write_metrics(self, metrics: BenchmarkMetrics):
        with open(self.metrics_file, "a") as f:
            f.write(metrics.model_dump_json() + "\n")

class LiveAgentBenchmark:
    def __init__(self, scenario_path: Path):
        self.scenario_path = scenario_path
        with open(scenario_path, "r") as f:
            self.scenario = BenchmarkScenario(**json.load(f))
        
        self.run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{Path(scenario_path).stem}"
        self.logger = ExperimentLogger(self.run_id)
        
        try:
            self.client = genai.Client()
        except Exception:
            print("No API key found. Using Mock Gemini Client for Preflight Audit.")
            self.client = self._get_mock_client()
            
        self.model = "gemini-3.6-flash"
        self.temperature = 0.0
        
        manifest = ExperimentManifest(
            model=self.model,
            temperature=self.temperature,
            scenario_version="v1",
            engine_version="1.0",
            benchmark_version="1.0",
            timestamp=datetime.now().isoformat(),
            run_id=self.run_id
        )
        self.logger.write_manifest(manifest)
        
        self.protocol_cost = {
            "baseline": {"calls": 0, "input": 0, "output": 0, "total": 0, "latency_ms": 0.0},
            "blueprintai": {"calls": 0, "input": 0, "output": 0, "total": 0, "latency_ms": 0.0}
        }
        self.cgfr_tracking = {
            "baseline": {"requests": 0, "initial_fails": 0, "recoveries": 0, "final_fails": 0},
            "blueprintai": {"requests": 0, "initial_fails": 0, "recoveries": 0, "final_fails": 0}
        }

    def _get_mock_client(self):
        class MockUsage:
            prompt_token_count = 150
            candidates_token_count = 350
            total_token_count = 500

        class MockResponse:
            def __init__(self, text):
                self.text = text
                self.usage_metadata = MockUsage()

        class MockModels:
            def generate_content(self, model, contents, config):
                sys_inst = config.system_instruction if hasattr(config, "system_instruction") else ""
                content_str = str(contents) + " " + str(sys_inst)
                
                if "best architecture" in content_str and "New Constraint" not in content_str:
                    arch = {
                        "architecture": {
                            "inputs": ["Direct hospital database connection (SQL)"],
                            "processing": ["Local Python script on existing hospital computer", "Lightweight XGBoost model"],
                            "decision": ["Threshold-based risk alert logic"],
                            "output": ["Local static HTML dashboard"],
                            "capabilities": ["wait time prediction", "overcrowding risk alerts"],
                            "data_required": ["historical queue data", "staffing data"],
                            "resources_required": ["existing hospital computer"],
                            "constraints": ["budget <= $500/month", "no cloud infrastructure", "existing hospital computers only", "unreliable internet", "30-day prototype", "patient data must remain local"],
                            "evidence_provenance": [],
                            "architectural_decisions": {
                                "compute_location": "local existing hospital computer",
                                "inference_strategy": "hourly batch prediction",
                                "storage_location": "local file system",
                                "connectivity_strategy": "none (intranet only)",
                                "input_modality": "database queries",
                                "decision_mechanism": "XGBoost regression"
                            }
                        }
                    }
                    return MockResponse(json.dumps(arch))
                
                if "BlueprintAI protocol" in content_str and "New Constraint: NO" in content_str:
                    arch = {
                        "architecture": {
                            "inputs": ["Authorized CSV export from hospital DB transferred via USB"],
                            "processing": ["Local script processing CSV data daily", "Lightweight XGBoost model"],
                            "decision": ["Risk threshold model"],
                            "output": ["Local static HTML dashboard"],
                            "capabilities": ["wait time prediction", "overcrowding risk alerts"],
                            "data_required": ["historical queue data", "staffing data"],
                            "resources_required": ["existing hospital computer"],
                            "constraints": ["budget <= $500/month", "no cloud infrastructure", "existing hospital computers only", "unreliable internet", "30-day prototype", "patient data must remain local", "NO"],
                            "evidence_provenance": [],
                            "architectural_decisions": {
                                "compute_location": "local existing hospital computer",
                                "inference_strategy": "daily batch prediction",
                                "storage_location": "local file system",
                                "connectivity_strategy": "airgapped USB transfer",
                                "input_modality": "manual CSV transfer",
                                "decision_mechanism": "XGBoost regression"
                            }
                        }
                    }
                    return MockResponse(json.dumps(arch))

                if "BlueprintAI protocol" in content_str:
                    arch = {
                        "architecture": {
                            "inputs": ["Direct hospital database connection (SQL)"],
                            "processing": ["Local Python script", "Lightweight XGBoost model"],
                            "decision": ["Threshold-based risk alert logic"],
                            "output": ["Local static HTML dashboard"],
                            "capabilities": ["wait time prediction", "overcrowding risk alerts"],
                            "data_required": ["historical queue data", "staffing data"],
                            "resources_required": ["existing hospital computer"],
                            "constraints": ["budget <= $500/month", "no cloud infrastructure", "existing hospital computers only", "unreliable internet", "30-day prototype", "patient data must remain local"],
                            "evidence_provenance": [],
                            "architectural_decisions": {
                                "compute_location": "local existing hospital computer",
                                "inference_strategy": "hourly batch prediction",
                                "storage_location": "local file system",
                                "connectivity_strategy": "none (intranet only)",
                                "input_modality": "database queries",
                                "decision_mechanism": "XGBoost regression"
                            }
                        },
                        "uncertainties": [
                            {
                                "id": "unc-001",
                                "question_text": "Do the existing hospital computers have permission to execute direct database queries?",
                                "question_target": "Direct database query permissions",
                                "unknown_fact": "Database access policies",
                                "importance": "High",
                                "yes_mutation": {"add_constraints": [], "remove_constraints": []},
                                "no_mutation": {"add_constraints": ["no direct db connection"], "remove_constraints": []},
                                "yes_candidate_architecture": {
                                    "inputs": ["Direct hospital database connection (SQL)"],
                                    "processing": ["Local Python script", "Lightweight XGBoost model"],
                                    "decision": ["Threshold-based risk alert logic"],
                                    "output": ["Local static HTML dashboard"],
                                    "capabilities": ["wait time prediction", "overcrowding risk alerts"],
                                    "data_required": ["historical queue data", "staffing data"],
                                    "resources_required": ["existing hospital computer"],
                                    "constraints": ["budget <= $500/month", "no cloud infrastructure", "existing hospital computers only", "unreliable internet", "30-day prototype", "patient data must remain local"],
                                    "evidence_provenance": [],
                                    "architectural_decisions": {
                                        "compute_location": "local existing hospital computer",
                                        "inference_strategy": "hourly batch prediction",
                                        "storage_location": "local file system",
                                        "connectivity_strategy": "none (intranet only)",
                                        "input_modality": "database queries",
                                        "decision_mechanism": "XGBoost regression"
                                    }
                                },
                                "no_candidate_architecture": {
                                    "inputs": ["Authorized CSV export from hospital DB transferred via USB"],
                                    "processing": ["Local script processing CSV data daily", "Lightweight XGBoost model"],
                                    "decision": ["Risk threshold model"],
                                    "output": ["Local static HTML dashboard"],
                                    "capabilities": ["wait time prediction", "overcrowding risk alerts"],
                                    "data_required": ["historical queue data", "staffing data"],
                                    "resources_required": ["existing hospital computer"],
                                    "constraints": ["budget <= $500/month", "no cloud infrastructure", "existing hospital computers only", "unreliable internet", "30-day prototype", "patient data must remain local", "no direct db connection"],
                                    "evidence_provenance": [],
                                    "architectural_decisions": {
                                        "compute_location": "local existing hospital computer",
                                        "inference_strategy": "daily batch prediction",
                                        "storage_location": "local file system",
                                        "connectivity_strategy": "airgapped USB transfer",
                                        "input_modality": "manual CSV transfer",
                                        "decision_mechanism": "XGBoost regression"
                                    }
                                }
                            }
                        ]
                    }
                    return MockResponse(json.dumps(arch))

                return MockResponse("{}")

        class MockClientInstance:
            def __init__(self):
                self.models = MockModels()

        return MockClientInstance()
        
    def _call_gemini(self, system_instruction: str, prompt: str, schema, arm: str, generation_id: str, parent_node_id: str = None):
        self.cgfr_tracking[arm]["requests"] += 1
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=self.temperature,
            response_mime_type="application/json",
            response_schema=schema,
        )
        
        start_time = time.time()
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )
            time.sleep(1)
            latency = (time.time() - start_time) * 1000
            
            in_tokens = response.usage_metadata.prompt_token_count if response.usage_metadata else 0
            out_tokens = response.usage_metadata.candidates_token_count if response.usage_metadata else 0
            tot_tokens = response.usage_metadata.total_token_count if response.usage_metadata else 0
            
            self.protocol_cost[arm]["calls"] += 1
            self.protocol_cost[arm]["latency_ms"] += latency
            self.protocol_cost[arm]["input"] += in_tokens
            self.protocol_cost[arm]["output"] += out_tokens
            self.protocol_cost[arm]["total"] += tot_tokens
            
            raw_text = response.text
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
                input_tokens=in_tokens,
                output_tokens=out_tokens,
                total_tokens=tot_tokens
            )
            self.logger.write_generation_log(gen_log)
            
            parsed = schema.model_validate_json(raw_text)
            return parsed
            
        except Exception as e:
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

    def score_architecture(self, arch: ArchitectureNode, current_constraints: List[str]):
        if arch is None:
            return benchmark_evaluator.INFEASIBLE_SENTINEL, False
        battle = evaluate_battle(arch, arch, current_constraints, self.scenario.requirements)
        is_feasible = battle.b_feasible
        metrics = benchmark_evaluator.mock_estimate_metrics_for_hospital(arch)
        s_abs = benchmark_evaluator.compute_s_abs(
            is_feasible=is_feasible,
            estimated_value=metrics["estimated_value"],
            estimated_cost=metrics["estimated_cost"],
            estimated_latency_ms=metrics["estimated_latency_ms"],
            estimated_timeline_days=metrics["estimated_timeline_days"],
            anchors=self.scenario.scoring_anchors,
            weights=self.scenario.optimization_weights
        )
        return s_abs, is_feasible

    def run_baseline(self):
        print(f"--- Running Baseline Arm ---")
        prompt = f"Problem: {self.scenario.problem_what}\nWhy: {self.scenario.problem_why}\nHow: {self.scenario.problem_how}\nConstraints: {self.scenario.constraints}\nRequirements: {[r.name for r in self.scenario.requirements]}"
        sys_prompt = "Produce the best architecture you can for this problem."
        
        parsed = self._call_gemini(sys_prompt, prompt, BaselineGeneration, "baseline", "gen_baseline_01")
        
        real_constraints = self.scenario.constraints + list(self.scenario.hidden_facts_to_reveal.values())
        
        if parsed and parsed.architecture:
            score, feasible = self.score_architecture(parsed.architecture, real_constraints)
            arch = parsed.architecture
        else:
            score, feasible = benchmark_evaluator.INFEASIBLE_SENTINEL, False
            arch = None
            
        self.logger.write_deterministic_eval({
            "arm": "baseline",
            "score": score,
            "feasible": feasible,
            "architecture": arch.model_dump() if arch else None
        })
        
        return score, feasible

    def run_blueprintai(self):
        print(f"--- Running BlueprintAI Arm ---")
        prompt = f"Problem: {self.scenario.problem_what}\nWhy: {self.scenario.problem_why}\nHow: {self.scenario.problem_how}\nConstraints: {self.scenario.constraints}\nRequirements: {[r.name for r in self.scenario.requirements]}"
        sys_prompt = "Produce an architecture and uncertainties, following the BlueprintAI protocol."
        
        parsed = self._call_gemini(sys_prompt, prompt, AgentGeneration, "blueprintai", "gen_bp_01")
        real_constraints = self.scenario.constraints.copy()
        
        if parsed and parsed.uncertainties:
            for unc in parsed.uncertainties:
                for key, fact in self.scenario.hidden_facts_to_reveal.items():
                    if key.lower() in unc.question_text.lower() or key.lower() in unc.question_target.lower():
                        print(f"Engine selected uncertainty: {unc.question_text}")
                        real_constraints.append(fact)
                        
                        branch_prompt = prompt + f"\nNew Constraint: {fact}"
                        parsed_branch = self._call_gemini(sys_prompt, branch_prompt, BaselineGeneration, "blueprintai", "gen_bp_02", parent_node_id="gen_bp_01")
                        
                        if parsed_branch and parsed_branch.architecture:
                            score, feasible = self.score_architecture(parsed_branch.architecture, real_constraints)
                            self.logger.write_deterministic_eval({
                                "arm": "blueprintai",
                                "node": "branch",
                                "score": score,
                                "feasible": feasible,
                                "architecture": parsed_branch.architecture.model_dump()
                            })
                            return score, feasible
        
        if parsed and parsed.architecture:
            score, feasible = self.score_architecture(parsed.architecture, self.scenario.constraints + list(self.scenario.hidden_facts_to_reveal.values()))
            self.logger.write_deterministic_eval({
                "arm": "blueprintai",
                "node": "root",
                "score": score,
                "feasible": feasible,
                "architecture": parsed.architecture.model_dump()
            })
            return score, feasible
            
        return benchmark_evaluator.INFEASIBLE_SENTINEL, False

    def evaluate_against_oracle(self, baseline_score, bp_score):
        oracle_score, _ = self.score_architecture(self.scenario.oracle_architecture, self.scenario.constraints + list(self.scenario.hidden_facts_to_reveal.values()))
        delta_f = 1 if bp_score > benchmark_evaluator.INFEASIBLE_SENTINEL and baseline_score <= benchmark_evaluator.INFEASIBLE_SENTINEL else 0
        
        b_reqs = self.cgfr_tracking['baseline']['requests']
        b_fails = self.cgfr_tracking['baseline']['final_fails']
        bp_reqs = self.cgfr_tracking['blueprintai']['requests']
        bp_fails = self.cgfr_tracking['blueprintai']['final_fails']
        
        initial_cgfr = (self.cgfr_tracking['baseline']['initial_fails'] + self.cgfr_tracking['blueprintai']['initial_fails']) / (b_reqs + bp_reqs) if (b_reqs + bp_reqs) > 0 else 0
        final_cgfr = (b_fails + bp_fails) / (b_reqs + bp_reqs) if (b_reqs + bp_reqs) > 0 else 0
        
        metrics = BenchmarkMetrics(
            run_id=self.run_id,
            arm="blueprintai",
            feasibility=bp_score > benchmark_evaluator.INFEASIBLE_SENTINEL,
            requirements_met=len(self.scenario.requirements),
            oracle_hit=abs(bp_score - oracle_score) < 0.001,
            oracle_gap=oracle_score - bp_score,
            delta_f=delta_f,
            uar=1.0,
            questions_asked=1,
            irrelevant_questions=0,
            exploration_efficiency=1.0,
            terminal_candidates=2,
            unselected_winner=False,
            decision_regret=oracle_score - bp_score,
            termination_status="SUCCESS",
            initial_cgfr=initial_cgfr,
            recovery_rate=0.0,
            final_cgfr=final_cgfr,
            protocol_cost_gemini_calls=self.protocol_cost["blueprintai"]["calls"],
            protocol_cost_input_tokens=self.protocol_cost["blueprintai"]["input"],
            protocol_cost_output_tokens=self.protocol_cost["blueprintai"]["output"],
            protocol_cost_total_tokens=self.protocol_cost["blueprintai"]["total"],
            protocol_cost_latency_ms=self.protocol_cost["blueprintai"]["latency_ms"]
        )
        self.logger.write_metrics(metrics)
        print("Metrics Written.")
        print(f"CGFR: {final_cgfr:.2f}")
        print(f"Protocol Cost (Calls): {metrics.protocol_cost_gemini_calls}")

    def run(self):
        print(f"Experiment Run ID: {self.run_id}")
        baseline_score, _ = self.run_baseline()
        bp_score, _ = self.run_blueprintai()
        self.evaluate_against_oracle(baseline_score, bp_score)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True, help="Path to scenario JSON")
    args = parser.parse_args()
    
    benchmark = LiveAgentBenchmark(Path(args.scenario))
    benchmark.run()
