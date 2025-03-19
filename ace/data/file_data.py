import boto3
import botocore
import logging
from typing import Optional, Union, List, Dict, Any, Iterator
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class S3FileManager:
    def __init__(self, bucket_name: str, aws_access_key_id: Optional[str] = None, 
                 aws_secret_access_key: Optional[str] = None, region_name: Optional[str] = None):
        """
        Initialize the S3FileManager with the target S3 bucket and (optionally) AWS credentials.
        If credentials are not provided, boto3 will use the default configuration.
        
        Parameters:
            bucket_name (str): Name of the S3 bucket
            aws_access_key_id (str, optional): AWS access key ID
            aws_secret_access_key (str, optional): AWS secret access key
            region_name (str, optional): AWS region name
        """
        if not bucket_name:
            raise ValueError("Bucket name must be provided")
            
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
        
    def __enter__(self):
        """Enable context manager support with 'with' statement"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources when exiting context manager"""
        pass
        
    def write_file(self, key: str, data: Union[str, bytes], content_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Write data to an S3 object.
        
        Parameters:
          key (str): The S3 object key (can include folder/prefix paths).
          data (str or bytes): The data content that will form the S3 object.
          content_type (str, optional): The content type of the file (e.g., 'text/plain', 'application/json')
        
        Returns:
          dict: Response from the put_object API call or None if error occurs.
        
        Raises:
          ValueError: If key is empty or None
        """
        if not key:
            raise ValueError("Object key must be provided")
            
        # Convert string data to bytes if needed
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        try:
            params = {
                'Bucket': self.bucket_name,
                'Key': key,
                'Body': data
            }
            
            # Add content type if provided
            if content_type:
                params['ContentType'] = content_type
                
            response = self.s3.put_object(**params)
            logger.info(f"Successfully uploaded file to {self.bucket_name}/{key}")
            return response
        except botocore.exceptions.ClientError as error:
            logger.error(f"Error uploading file to {self.bucket_name}/{key}: {error}")
            return None

    def read_file(self, key: str) -> Optional[bytes]:
        """
        Retrieve an S3 object from the bucket.
        
        Parameters:
          key (str): The S3 object key.
        
        Returns:
          bytes: The content of the retrieved file or None if error occurs.
          
        Raises:
          ValueError: If key is empty or None
        """
        if not key:
            raise ValueError("Object key must be provided")
            
        try:
            response = self.s3.get_object(Bucket=self.bucket_name, Key=key)
            content = response['Body'].read()
            logger.info(f"Successfully retrieved file from {self.bucket_name}/{key}")
            return content
        except botocore.exceptions.ClientError as error:
            logger.error(f"Error reading file from {self.bucket_name}/{key}: {error}")
            return None
            
    def file_exists(self, key: str) -> bool:
        """
        Check if a file exists in the S3 bucket.
        
        Parameters:
          key (str): The S3 object key.
          
        Returns:
          bool: True if the file exists, False otherwise.
        """
        try:
            self.s3.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except botocore.exceptions.ClientError:
            return False
            
    def delete_file(self, key: str) -> bool:
        """
        Delete a file from the S3 bucket.
        
        Parameters:
          key (str): The S3 object key.
          
        Returns:
          bool: True if deletion was successful, False otherwise.
        """
        if not key:
            raise ValueError("Object key must be provided")
            
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Successfully deleted file from {self.bucket_name}/{key}")
            return True
        except botocore.exceptions.ClientError as error:
            logger.error(f"Error deleting file from {self.bucket_name}/{key}: {error}")
            return False
            
    def list_files(self, prefix: str = "", max_items: int = 1000) -> List[Dict[str, Any]]:
        """
        List files in the S3 bucket with an optional prefix.
        
        Parameters:
          prefix (str): Prefix to filter objects (like a folder path)
          max_items (int): Maximum number of items to return
          
        Returns:
          list: List of file information dictionaries
        """
        try:
            paginator = self.s3.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=prefix,
                PaginationConfig={'MaxItems': max_items}
            )
            
            files = []
            for page in page_iterator:
                if 'Contents' in page:
                    files.extend(page['Contents'])
                    
            logger.info(f"Listed {len(files)} files from {self.bucket_name} with prefix '{prefix}'")
            return files
        except botocore.exceptions.ClientError as error:
            logger.error(f"Error listing files from {self.bucket_name} with prefix '{prefix}': {error}")
            return []
            
    def copy_file(self, source_key: str, dest_key: str) -> bool:
        """
        Copy a file within the same bucket.
        
        Parameters:
          source_key (str): The source S3 object key
          dest_key (str): The destination S3 object key
          
        Returns:
          bool: True if copy was successful, False otherwise
        """
        if not source_key or not dest_key:
            raise ValueError("Source and destination keys must be provided")
            
        try:
            copy_source = {'Bucket': self.bucket_name, 'Key': source_key}
            self.s3.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=dest_key
            )
            logger.info(f"Successfully copied {source_key} to {dest_key} in {self.bucket_name}")
            return True
        except botocore.exceptions.ClientError as error:
            logger.error(f"Error copying {source_key} to {dest_key} in {self.bucket_name}: {error}")
            return False
            
    def upload_file(self, local_path: str, s3_key: str, content_type: Optional[str] = None) -> bool:
        """
        Upload a local file to S3.
        
        Parameters:
          local_path (str): Path to the local file
          s3_key (str): The destination S3 object key
          content_type (str, optional): The content type of the file
          
        Returns:
          bool: True if upload was successful, False otherwise
        """
        if not os.path.exists(local_path):
            logger.error(f"Local file does not exist: {local_path}")
            return False
            
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
                
            self.s3.upload_file(
                local_path, 
                self.bucket_name, 
                s3_key,
                ExtraArgs=extra_args
            )
            logger.info(f"Successfully uploaded {local_path} to {self.bucket_name}/{s3_key}")
            return True
        except botocore.exceptions.ClientError as error:
            logger.error(f"Error uploading {local_path} to {self.bucket_name}/{s3_key}: {error}")
            return False
            
    def download_file(self, s3_key: str, local_path: str) -> bool:
        """
        Download a file from S3 to a local path.
        
        Parameters:
          s3_key (str): The S3 object key
          local_path (str): Path where the file should be saved locally
          
        Returns:
          bool: True if download was successful, False otherwise
        """
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
            
            self.s3.download_file(self.bucket_name, s3_key, local_path)
            logger.info(f"Successfully downloaded {self.bucket_name}/{s3_key} to {local_path}")
            return True
        except botocore.exceptions.ClientError as error:
            logger.error(f"Error downloading {self.bucket_name}/{s3_key} to {local_path}: {error}")
            return False

# # Example usage:
# if __name__ == "__main__":
#     # Replace these values with your bucket name and (if needed) AWS credentials.
#     bucket_name = "your_bucket_name"
#     file_key = "folder/subfolder/example_file.txt"
#     sample_text = "This is a sample file uploaded using boto3."

#     # Optionally, include credentials; if they are set in your environment, omit these parameters.
#     s3_manager = S3FileManager(
#         bucket_name,
#         aws_access_key_id="YOUR_ACCESS_KEY",
#         aws_secret_access_key="YOUR_SECRET_KEY",
#         region_name="YOUR_AWS_REGION"
#     )

#     # Write the file to S3
#     upload_response = s3_manager.write_file(file_key, sample_text)
#     if upload_response:
#         # Retrieve the file from S3
#         downloaded_data = s3_manager.read_file(file_key)
#         if downloaded_data:
#             # Decode bytes to string if text data was uploaded (or handle bytes as needed)
#             print("File content:")
#             print(downloaded_data.decode('utf-8'))
