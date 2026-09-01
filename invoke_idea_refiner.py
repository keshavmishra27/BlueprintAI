import sys
from pathlib import Path

project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from product.db.models import Base
from product.service import ProductService
from decision_engine.tree.optimizer import PathNode
from decision_engine.input_layer.schemas import ArchitectureNode
from idea_refiner.parsers.base import BaseIdeaParser
import json

class HospitalPredictionParser(BaseIdeaParser):
    def parse_idea_to_graph(self, idea: str) -> list[PathNode]:
        arch_a = ArchitectureNode(
            inputs=[], processing=["Kafka", "Spark Streaming", "FastAPI"], decision=[], output=[], capabilities=["sub_second_latency", "high_throughput"],
            data_required=[], resources_required=[], constraints=[], semantic_dependencies=["requires_event_streaming", "requires_cluster_compute"], 
            evidence_provenance=[], architectural_decisions={}
        )
        node_a = PathNode(
            id="Cand_A_Streaming", parent_id="root",
            architecture=arch_a,
            status="TERMINAL", path_score=95.0, path_cost=25.0, operational_complexity=9.0
        )
        
        arch_b = ArchitectureNode(
            inputs=[], processing=["Airflow", "TimescaleDB", "FastAPI", "XGBoost"], decision=[], output=[], capabilities=["hourly_predictions", "time_series_aggregation"],
            data_required=[], resources_required=[], constraints=[], semantic_dependencies=["requires_relational_db", "requires_cron_scheduling"], 
            evidence_provenance=[], architectural_decisions={}
        )
        node_b = PathNode(
            id="Cand_B_Batch", parent_id="root",
            architecture=arch_b,
            status="TERMINAL", path_score=90.0, path_cost=5.0, operational_complexity=3.0
        )
        
        arch_c = ArchitectureNode(
            inputs=[], processing=["AWS Kinesis", "AWS Lambda", "DynamoDB"], decision=[], output=[], capabilities=["auto_scaling", "zero_ops"],
            data_required=[], resources_required=[], constraints=[], semantic_dependencies=["vendor_lock_in", "requires_cloud"], 
            evidence_provenance=[], architectural_decisions={}
        )
        node_c = PathNode(
            id="Cand_C_Serverless", parent_id="root",
            architecture=arch_c,
            status="TERMINAL", path_score=85.0, path_cost=15.0, operational_complexity=4.0
        )
        
        return [node_a, node_b, node_c]

def main():
    engine = create_engine(f"sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    product_service = ProductService(session)
    
    idea = "Build an offline mobile application that performs image classification on-device without internet connectivity and must work on low-end phones."
    
    print(f"Agent generating hypotheses for idea: {idea}")
    
    context_dict = {
        "optimizer_preferences": {
            "cost_lambda": 1.0, 
            "complexity_lambda": 1.0
        }
    }
    
    decision = product_service.analyze_idea(
        idea=idea,
        context=context_dict,
        parser=HospitalPredictionParser()
    )
    
    print("\n--- DETERMINISTIC OPTIMIZER RESULTS ---")
    print(f"Decision ID: {decision.id}")
    print(f"Decision Fingerprint: {decision.decision_fingerprint}")
    print(f"Selected Components: {[c.name for c in decision.architecture.components]}")
    
    with open("hospital_decision.json", "w", encoding="utf-8") as f:
        f.write(decision.model_dump_json(indent=2))
        
if __name__ == "__main__":
    main()
