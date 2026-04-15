import subprocess
import sys
import os
from pathlib import Path

def main():
    """
    Entry point for the 'bc-app' script.
    Runs the Chainlit application from the project root but preserves the user's CWD.
    """
    project_root = Path(__file__).parent.parent.resolve()
    app_path = project_root / "app.py"
    
    if not app_path.exists():
        print(f"Error: Could not find app.py at {app_path}")
        sys.exit(1)

    original_cwd = os.getcwd()
    
    os.environ["BC_APP_CWD"] = original_cwd

    print(f"Starting Chainlit app from: {project_root}")
    print(f"Agent working directory: {original_cwd}")
    
    os.chdir(project_root)
    
    try:
        subprocess.run(["chainlit", "run", "app.py"] + sys.argv[1:], check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()
