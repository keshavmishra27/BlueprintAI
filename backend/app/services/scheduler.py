"""
Option C – APScheduler-based nightly skill-gap curator.
On startup the scheduler adds a cron job that runs at midnight UTC.
It gathers all completed assessments + repo analyses from the DB,
builds per-student summaries, feeds them to the CrewAI skill-gap crew,
and persists the report.
Manual trigger is also available via `run_skill_gap_job()`.
"""
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from backend.app.database import SessionLocal
from backend.app.models import AssessmentSession, RepoAnalysis, SkillGapReport
logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None
def _build_student_summaries(db) -> list[dict]:
    """Aggregate per-student quiz + repo scores into summaries."""
    sessions = (
        db.query(AssessmentSession)
        .filter(AssessmentSession.status == "scored")
        .all()
    )
    repos = db.query(RepoAnalysis).all()
    students: dict[str, dict] = {}
    for s in sessions:
        name = s.student_name
        if name not in students:
            students[name] = {
                "student_name": name,
                "domains": [],
                "quiz_scores": [],
                "repo_scores": [],
            }
        students[name]["domains"].extend(s.domains or [])
        sc = s.scores or {}
        ws = sc.get("weighted_score", 0)
        mw = sc.get("max_weighted", 1)
        if mw > 0:
            students[name]["quiz_scores"].append(round(ws / mw * 100, 1))
    for r in repos:
        name = r.student_name
        if name not in students:
            students[name] = {
                "student_name": name,
                "domains": [],
                "quiz_scores": [],
                "repo_scores": [],
            }
        rj = r.result_json or {}
        total = rj.get("total_score")
        if total is not None:
            students[name]["repo_scores"].append(total)
    summaries = []
    for name, data in students.items():
        domains = list(set(data["domains"]))
        quiz_avg = (
            round(sum(data["quiz_scores"]) / len(data["quiz_scores"]), 1)
            if data["quiz_scores"]
            else None
        )
        repo_avg = (
            round(sum(data["repo_scores"]) / len(data["repo_scores"]), 1)
            if data["repo_scores"]
            else None
        )
        summaries.append({
            "student_name": name,
            "domains": domains,
            "quiz_avg_pct": quiz_avg,
            "repo_avg_score": repo_avg,
            "quiz_count": len(data["quiz_scores"]),
            "repo_count": len(data["repo_scores"]),
        })
    return summaries
def run_skill_gap_job():
    """Run the skill-gap analysis and persist the report. Callable manually."""
    logger.info("⏰ Skill-gap scheduled job starting...")
    db = SessionLocal()
    try:
        summaries = _build_student_summaries(db)
        if not summaries:
            logger.info("No student data found — skipping skill-gap analysis.")
            return
        logger.info("Analyzing %d students for skill gaps...", len(summaries))
        from backend.app.services.crews.skill_gap_crew import run_skill_gap_crew
        report = run_skill_gap_crew(summaries)
        report["generated_at"] = datetime.now(timezone.utc).isoformat()
        report["students_analyzed"] = len(summaries)
        row = SkillGapReport(report_json=report)
        db.add(row)
        db.commit()
        logger.info("✅ Skill-gap report #%d saved.", row.id)
    except Exception:
        logger.exception("Skill-gap job failed")
    finally:
        db.close()
def start_scheduler():
    """Start the APScheduler background scheduler with the nightly job."""
    global _scheduler
    if _scheduler is not None:
        logger.info("Scheduler already running.")
        return
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        run_skill_gap_job,
        trigger=CronTrigger(hour=0, minute=0),   
        id="nightly_skill_gap",
        name="Nightly Skill-Gap Curator",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("🕛 Scheduler started — nightly skill-gap job registered at 00:00 UTC.")
def stop_scheduler():
    """Gracefully shut down the scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped.")
def get_scheduler_status() -> dict:
    """Return info about scheduled jobs."""
    if not _scheduler:
        return {"running": False, "jobs": []}
    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else None,
        })
    return {"running": True, "jobs": jobs}
