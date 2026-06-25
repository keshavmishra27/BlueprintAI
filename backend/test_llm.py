import asyncio
from backend.app.services.project_suggest_service import suggest_projects
def main():
    res = suggest_projects("Artificial Intelligence")
    print(res)
if __name__ == "__main__":
    main()