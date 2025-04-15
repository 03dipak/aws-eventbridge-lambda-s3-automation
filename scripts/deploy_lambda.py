import boto3, zipfile, os, sys
from botocore.exceptions import ClientError

def zip_lambda(source_dir, zip_path):
    """Create a zip file from the source directory."""
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                path = os.path.join(root, file)
                zipf.write(path, os.path.relpath(path, source_dir))

def deploy_lambda(lambda_name, source_dir, role_arn, region):
    """Deploy or update a Lambda function."""
    zip_path = f"/tmp/{lambda_name}.zip"
    zip_lambda(source_dir, zip_path)
    
    # Initialize the Lambda client
    client = boto3.client("lambda", region_name=region)

    with open(zip_path, "rb") as f:
        zipped_code = f.read()

    # Try to get the function and update or create it
    try:
        # Check if the Lambda function already exists
        client.get_function(FunctionName=lambda_name)
        # Update the existing Lambda function
        client.update_function_code(FunctionName=lambda_name, ZipFile=zipped_code)
        print(f"✅ Updated {lambda_name}")
    except client.exceptions.ResourceNotFoundException:
        # If the function doesn't exist, create a new one
        try:
            client.create_function(
                FunctionName=lambda_name,
                Runtime="python3.10",  # Lambda runtime version
                Role=role_arn,  # Ensure this role ARN is correctly formatted
                Handler="lambda_function.lambda_handler",  # Entry point of the Lambda
                Code={'ZipFile': zipped_code},
                Timeout=30  # Timeout for the function
            )
            print(f"✅ Created {lambda_name}")
        except ClientError as e:
            print(f"❌ Error creating function {lambda_name}: {e}")
            raise

if __name__ == "__main__":
    # Ensure correct number of arguments
    if len(sys.argv) != 5:
        print("Usage: python deploy_lambda.py <lambda_name> <source_dir> <role_arn> <region>")
        sys.exit(1)

    deploy_lambda(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
