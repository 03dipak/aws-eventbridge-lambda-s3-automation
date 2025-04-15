import json

def lambda_handler(event, context):
    print("Event Received:", json.dumps(event))

    try:
        # Extract bucket name and object key from EventBridge event
        bucket_name = event['detail']['bucket']['name']
        object_key = event['detail']['object']['key']
        
        # Prefix to match
        prefix = "restricted-folder/data/output_data_"
        
        # Check if object key matches prefix
        if object_key.startswith(prefix):
            print(f"Matched file: {object_key} in bucket: {bucket_name}")
            # Add your processing logic here
        else:
            print(f"Ignored file: {object_key}")
    
    except Exception as e:
        print(f"Error processing event: {e}")
        raise
