import boto3
import botocore
import logging
from typing import Optional, Union, Dict, Any
from rich import print

import os

# Configure logging
root_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(root_dir)
log_file = os.path.join(parent_dir, "ace.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
            print(f"[bold green]✔ Successfully uploaded file to[/bold green] [cyan]{self.bucket_name}/{key}[/cyan]")
            return response
        except botocore.exceptions.ClientError as error:
            logger.error(f"Error uploading file to {self.bucket_name}/{key}: {error}")
            print(f"[bold red]Error uploading file to[/bold red] [cyan]{self.bucket_name}/{key}[/cyan]: {error}")
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
            print(f"[bold green]✔ Successfully retrieved file from[/bold green] [cyan]{self.bucket_name}/{key}[/cyan]")
            return content
        except botocore.exceptions.ClientError as error:
            logger.error(f"Error reading file from {self.bucket_name}/{key}: {error}")
            print(f"[bold red]Error reading file from[/bold red] [cyan]{self.bucket_name}/{key}[/cyan]: {error}")
            return None