import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.services.github_judge_service import _gather_code
def test_zipball_fetch(url):
    print(f"Testing EXTREME (Zipball) fetch for {url}...")
    owner = "psf"
    repo = "requests"
    start_time = time.time()
    code_dump = _gather_code(owner, repo)
    end_time = time.time()
    duration = end_time - start_time
    print(f"Successfully gathered code.")
    print(f"Time taken (Zip download + Extraction): {duration:.2f} seconds")
    print(f"Total characters gathered: {len(code_dump)}")
    if "### FILE: README.md" in code_dump:
        print("Confirmed: README.md prioritized and included.")
if __name__ == "__main__":
    test_zipball_fetch("https://github.com/psf/requests")