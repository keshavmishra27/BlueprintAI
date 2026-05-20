from sqlalchemy.orm import Session

from backend.app.models import AssessmentSession


def compute_real_percentile(
    db: Session,
    domains: list[str],
    weighted_score: int,
    max_weighted: int,
    exclude_session_id: int | None = None,
) -> dict:
    """
    Percentile vs other completed sessions sharing at least one domain.
    Falls back to cohort size message when sample is too small.
    """
    if max_weighted <= 0:
        return {
            "percentile": 50,
            "cohort_size": 0,
            "percentile_source": "insufficient_data",
            "message": "Not enough scored sessions yet — showing neutral baseline.",
        }

    ratio = weighted_score / max_weighted
    sessions = (
        db.query(AssessmentSession)
        .filter(AssessmentSession.status == "scored")
        .filter(AssessmentSession.scores.isnot(None))
        .all()
    )

    domain_set = set(domains or [])
    cohort_ratios: list[float] = []
    for s in sessions:
        if exclude_session_id and s.id == exclude_session_id:
            continue
        s_domains = set(s.domains or [])
        if domain_set and not (domain_set & s_domains):
            continue
        sc = s.scores or {}
        mw = sc.get("max_weighted") or 0
        ws = sc.get("weighted_score") or 0
        if mw > 0:
            cohort_ratios.append(ws / mw)

    cohort_size = len(cohort_ratios)
    if cohort_size < 3:
        return {
            "percentile": max(1, min(99, int(ratio * 100))),
            "cohort_size": cohort_size,
            "percentile_source": "self_score_estimate",
            "message": (
                f"Only {cohort_size} prior scored session(s) in this domain — "
                "percentile will improve as more developers take the quiz."
            ),
        }

    below = sum(1 for r in cohort_ratios if r < ratio)
    percentile = int((below / cohort_size) * 100)
    percentile = max(1, min(99, percentile))
    return {
        "percentile": percentile,
        "cohort_size": cohort_size,
        "percentile_source": "database_cohort",
        "message": (
            f"Compared against {cohort_size} developers who completed quizzes "
            f"in overlapping domain(s): {', '.join(sorted(domain_set)) or 'any'}."
        ),
    }
