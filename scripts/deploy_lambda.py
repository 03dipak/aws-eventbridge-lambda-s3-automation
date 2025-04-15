import boto3, zipfile, os, sys

def zip_lambda(source_dir, zip_path):
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                path = os.path.join(root, file)
                zipf.write(path, os.path.relpath(path, source_dir))

def deploy_lambda(lambda_name, source_dir, role_arn, region):
    zip_path = f"/tmp/{lambda_name}.zip"
    zip_lambda(source_dir, zip_path)
    client = boto3.client("lambda", region_name=region)

    with open(zip_path, "rb") as f:
        zipped_code = f.read()

    try:
        client.get_function(FunctionName=lambda_name)
        client.update_function_code(FunctionName=lambda_name, ZipFile=zipped_code)
        print(f"Updated {lambda_name}")
    except client.exceptions.ResourceNotFoundException:
        client.create_function(
            FunctionName=lambda_name,
            Runtime="python3.10",
            Role=role_arn,
            Handler="lambda_function.lambda_handler",
            Code={'ZipFile': zipped_code},
            Timeout=30
        )
        print(f"Created {lambda_name}")

if __name__ == "__main__":
    deploy_lambda(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
