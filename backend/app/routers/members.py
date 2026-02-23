from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from backend.app.database import get_db
from backend.app.models import Member, Domain
from backend.app.schemas import MemberBulkCreate, MemberCreateWithDomains
router = APIRouter(prefix="/members", tags=["Members"])


@router.get("/domains")
def get_domains(db: Session = Depends(get_db)):
    """Return all domains with id and name."""
    from backend.app.models import Domain
    domains = db.query(Domain).all()
    return [{"id": d.id, "name": d.name} for d in domains]


@router.get("/by-domain")
def get_members_by_domain(db: Session = Depends(get_db)):
    """Return all domains, each with a list of their members."""
    from backend.app.models import Domain
    domains = db.query(Domain).all()
    return [
        {
            "domain_id": d.id,
            "domain_name": d.name,
            "members": [
                {"id": m.id, "name": m.name, "category": m.category}
                for m in d.members
            ],
        }
        for d in domains
    ]

@router.get("/")
def get_members(domain_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    if domain_id:
        
        domain = db.query(Domain).filter(Domain.id == domain_id).first()
        if not domain:
            return []
        
        return [
            {
                "id": m.id,
                "name": m.name,
                "category": m.category
            }
            for m in domain.members
        ]
    else:
        
        members = db.query(Member).all()
        return [
            {
                "id": m.id,
                "name": m.name,
                "category": m.category
            }
            for m in members
        ]

@router.post("/")
def create_member(payload: MemberCreateWithDomains, db: Session = Depends(get_db)):
    """
    Create a new member and optionally assign them to one or more domains.
    Pass domain_ids as a list of existing Domain IDs.
    """
    member = Member(name=payload.name, category=payload.category)
    db.add(member)
    db.flush()

    # Assign to domains
    if payload.domain_ids:
        domains = db.query(Domain).filter(Domain.id.in_(payload.domain_ids)).all()
        if len(domains) != len(payload.domain_ids):
            found_ids = {d.id for d in domains}
            missing = [i for i in payload.domain_ids if i not in found_ids]
            raise HTTPException(status_code=404, detail=f"Domain IDs not found: {missing}")
        member.domains.extend(domains)

    db.commit()
    db.refresh(member)
    return {
        "id": member.id,
        "name": member.name,
        "category": member.category,
        "domains": [{"id": d.id, "name": d.name} for d in member.domains],
    }

@router.post("/bulk")
def create_members_bulk(payload: MemberBulkCreate, db: Session = Depends(get_db)):
    new_members = []
    for m_data in payload.members:
        member = Member(name=m_data.name, category=m_data.category)
        db.add(member)
        new_members.append(member)
    
    db.commit()
    for member in new_members:
        db.refresh(member)
        
    return [
        {
            "id": m.id,
            "name": m.name,
            "category": m.category
        }
        for m in new_members
    ]

@router.put("/{member_id}")
def update_member(member_id: int, name: Optional[str] = None, category: Optional[str] = None, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        return {"error": "Member not found"}
    if name:
        member.name = name
    if category:
        member.category = category
    db.commit()
    db.refresh(member)
    return {
        "id": member.id,
        "name": member.name,
        "category": member.category
    }

@router.delete("/{member_id}")
def delete_member(member_id: int, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        return {"error": "Member not found"}
    db.delete(member)
    db.commit()
    return {"message": "Member deleted successfully"}
