import asyncio
from backend.app.services.github_judge_service import analyze_repo
from backend.app.database import engine, Base
def main():
    Base.metadata.create_all(bind=engine)
    res = analyze_repo("https://github.com/keshavmishra27/group_maker", "Test Student")
    print(res.get("scores"))
    print(res.get("repository_signals"))
if __name__ == "__main__":
    main()