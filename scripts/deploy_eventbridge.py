import os
import sys
import json
import boto3
from pathlib import Path
from botocore.exceptions import ClientError

# --- Read CLI Args ---
if len(sys.argv) != 4:
    print("Usage: python deploy_eventbridge.py <region> <env_name> <bucket_name>")
    sys.exit(1)

REGION = sys.argv[1]
ENV_NAME = sys.argv[2]
BUCKET_NAME = sys.argv[3]  # Added Bucket Name argument
EVENT_BUS_NAME = "default"

# --- Paths ---
RULES_DIR = Path("eventbridge/rules")
TARGETS_DIR = Path("eventbridge/targets")

# --- AWS Clients ---
events_client = boto3.client("events", region_name=REGION)
lambda_client = boto3.client("lambda", region_name=REGION)
sts_client = boto3.client("sts", region_name=REGION)

# --- Get current account ID dynamically ---
ACCOUNT_ID = sts_client.get_caller_identity()["Account"]

# --- Helper Functions ---
def load_json_with_substitution(file_path):
    """Load JSON file and substitute placeholders like {{BUCKET_NAME}}"""
    with open(file_path, "r") as f:
        content = f.read()

    # Replace placeholders with actual values
    content = content.replace("{{BUCKET_NAME}}", BUCKET_NAME)

    return json.loads(content)


def deploy_eventbridge_rule(rule_file):
    rule_name = rule_file.stem
    event_pattern = load_json_with_substitution(rule_file)  # Using the updated method

    print(f"\n🔁 Deploying rule: {rule_name}")

    response = events_client.put_rule(
        Name=rule_name,
        EventPattern=json.dumps(event_pattern),
        State="ENABLED",
        Description=f"Deployed by GitHub Actions for ENV: {ENV_NAME}",
        EventBusName=EVENT_BUS_NAME,
    )

    rule_arn = response["RuleArn"]
    print(f"✅ Rule created: {rule_name} ({rule_arn})")
    return rule_name, rule_arn


def attach_targets(rule_name, rule_arn, target_file):
    targets_data = load_json_with_substitution(target_file)  # Using updated method

    for target in targets_data:
        target_id = target["Id"]
        lambda_fn_name = target["function"]

        lambda_arn = f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:{lambda_fn_name}"

        print(f"🎯 Attaching Lambda target: {lambda_fn_name} to rule: {rule_name}")
        events_client.put_targets(
            Rule=rule_name,
            EventBusName=EVENT_BUS_NAME,
            Targets=[
                {
                    "Id": target_id,
                    "Arn": lambda_arn
                }
            ],
        )

        try:
            lambda_client.add_permission(
                FunctionName=lambda_fn_name,
                StatementId=f"{rule_name}-{target_id}-Invoke",
                Action="lambda:InvokeFunction",
                Principal="events.amazonaws.com",
                SourceArn=rule_arn,
            )
            print(f"🔓 Permission granted to invoke Lambda: {lambda_fn_name}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceConflictException':
                print(f"⚠️ Permission already exists for {lambda_fn_name}, skipping.")
            else:
                raise


def deploy_all_eventbridge_rules():
    print(f"🚀 Deploying EventBridge rules in REGION: {REGION} | ENV: {ENV_NAME}")

    for rule_file in RULES_DIR.glob("*.json"):
        rule_name = rule_file.stem
        target_file = TARGETS_DIR / f"{rule_name}_targets.json"

        if not target_file.exists():
            print(f"⚠️ Skipping rule {rule_name}: No targets file found.")
            continue

        rule_name, rule_arn = deploy_eventbridge_rule(rule_file)
        attach_targets(rule_name, rule_arn, target_file)

    print("\n✅ All EventBridge rules deployed successfully!")


if __name__ == "__main__":
    deploy_all_eventbridge_rules()
