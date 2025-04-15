import subprocess, json

def detect_changed_lambdas():
    result = subprocess.run(["git", "diff", "--name-only", "origin/main...HEAD"], capture_output=True, text=True)
    changed_files = result.stdout.strip().split("\n")
    lambdas = set()

    for file in changed_files:
        if file.startswith("lambdas/") and "lambda_function.py" in file:
            lambdas.add(file.split("/")[1])
    print(json.dumps(list(lambdas)))

if __name__ == "__main__":
    detect_changed_lambdas()
