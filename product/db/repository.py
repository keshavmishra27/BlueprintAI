from typing import List, Optional
from sqlalchemy.orm import Session
from .models import DecisionRecord, GapReportRecord, RefinementRecord

class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_decision(self, decision: DecisionRecord) -> DecisionRecord:
        self.db.add(decision)
        self.db.commit()
        self.db.refresh(decision)
        return decision

    def update_decision_status(self, decision_id: str, new_status: str) -> Optional[DecisionRecord]:
        decision = self.get_decision(decision_id)
        if decision:
            decision.status = new_status
            self.db.commit()
            self.db.refresh(decision)
        return decision

    def get_decision(self, decision_id: str) -> Optional[DecisionRecord]:
        return self.db.query(DecisionRecord).filter(DecisionRecord.id == decision_id).first()

    def get_decision_history(self, decision_id: str) -> List[DecisionRecord]:
        """
        Retrieves the history of decisions leading up to this one, in chronological order.
        For example: D0 -> D1 -> D2 (where D2 is the decision_id passed in).
        """
        history = []
        current_id = decision_id
        
        while current_id is not None:
            decision = self.get_decision(current_id)
            if not decision:
                break
            history.insert(0, decision)
            current_id = decision.parent_id
            
        return history

    def get_recent_decisions(self, limit: int = 10) -> List[DecisionRecord]:
        """
        Retrieves the most recent decisions.
        """
        return self.db.query(DecisionRecord).order_by(DecisionRecord.created_at.desc()).limit(limit).all()

    def get_decision_children(self, decision_id: str) -> List[DecisionRecord]:
        return self.db.query(DecisionRecord).filter(DecisionRecord.parent_id == decision_id).all()

    def get_decisions_by_root(self, root_decision_id: str, status: Optional[str] = None) -> List[DecisionRecord]:
        all_nodes = {}
        
        to_process = [root_decision_id]
        
        while to_process:
            curr_id = to_process.pop(0)
            if curr_id in all_nodes:
                continue
            
            node = self.get_decision(curr_id)
            if not node:
                continue
                
            all_nodes[curr_id] = node
            
            children = self.get_decision_children(curr_id)
            to_process.extend([c.id for c in children])
            
        results = list(all_nodes.values())
        if status:
            results = [r for r in results if r.status == status]
            
        return results

    def save_gap_report(self, gap_report: GapReportRecord) -> GapReportRecord:
        self.db.add(gap_report)
        self.db.commit()
        self.db.refresh(gap_report)
        return gap_report

    def get_gap_report(self, report_id: str) -> Optional[GapReportRecord]:
        return self.db.query(GapReportRecord).filter(GapReportRecord.id == report_id).first()
        
    def get_gap_reports_by_decision(self, decision_id: str) -> List[GapReportRecord]:
        return self.db.query(GapReportRecord).filter(GapReportRecord.decision_id == decision_id).all()

    def save_refinement(self, refinement: RefinementRecord) -> RefinementRecord:
        self.db.add(refinement)
        self.db.commit()
        self.db.refresh(refinement)
        return refinement
        
    def get_refinement(self, refinement_id: str) -> Optional[RefinementRecord]:
        return self.db.query(RefinementRecord).filter(RefinementRecord.id == refinement_id).first()
