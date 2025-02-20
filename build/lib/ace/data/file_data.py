import boto3
import botocore

class S3FileManager:
    def __init__(self, bucket_name, aws_access_key_id=None, aws_secret_access_key=None, region_name=None):
        """
        Initialize the S3FileManager with the target S3 bucket and (optionally) AWS credentials.
        If credentials are not provided, boto3 will use the default configuration.
        """
        if aws_access_key_id and aws_secret_access_key:
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name
            )
        else:
            self.s3 = boto3.client('s3')
        self.bucket_name = bucket_name

    def write_file(self, key, data):
        """
        Write data to an S3 object.
        
        Parameters:
          key (str): The S3 object key (can include folder/prefix paths).
          data (str or bytes): The data content that will form the S3 object.
        
        Returns:
          dict: Response from the put_object API call.
        """
        try:
            response = self.s3.put_object(Bucket=self.bucket_name, Key=key, Body=data)
            print(f"Successfully uploaded file to {self.bucket_name}/{key}")
            return response
        except botocore.exceptions.ClientError as error:
            print(f"Error uploading file: {error}")
            return None

    def read_file(self, key):
        """
        Retrieve an S3 object from the bucket.
        
        Parameters:
          key (str): The S3 object key.
        
        Returns:
          bytes: The content of the retrieved file.
        """
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            content = response['Body'].read()
            print(f"Successfully downloaded file from {self.bucket_name}/{key}")
            return content
        except botocore.exceptions.ClientError as error:
            print(f"Error reading file: {error}")
            return None

# Example usage:
if __name__ == "__main__":
    # Replace these values with your bucket name and (if needed) AWS credentials.
    bucket_name = "your_bucket_name"
    file_key = "folder/subfolder/example_file.txt"
    sample_text = "This is a sample file uploaded using boto3."

    # Optionally, include credentials; if they are set in your environment, omit these parameters.
    s3_manager = S3FileManager(
        bucket_name,
        aws_access_key_id="YOUR_ACCESS_KEY",
        aws_secret_access_key="YOUR_SECRET_KEY",
        region_name="YOUR_AWS_REGION"
    )

    # Write the file to S3
    upload_response = s3_manager.write_file(file_key, sample_text)
    if upload_response:
        # Retrieve the file from S3
        downloaded_data = s3_manager.read_file(file_key)
        if downloaded_data:
            # Decode bytes to string if text data was uploaded (or handle bytes as needed)
            print("File content:")
            print(downloaded_data.decode('utf-8'))
