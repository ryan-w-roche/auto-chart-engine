import unittest
from unittest.mock import patch, MagicMock
import os
from botocore.exceptions import ClientError

from ace.data.file_data import S3FileManager

class TestS3FileManager(unittest.TestCase):
    """Tests for S3FileManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bucket_name = "test-bucket"
        self.aws_access_key_id = "test-access-key"
        self.aws_secret_access_key = "test-secret-key"
        self.region_name = "us-east-1"
        
        # Create patcher for boto3 client
        self.boto3_client_patcher = patch('boto3.client')
        self.mock_boto3_client = self.boto3_client_patcher.start()
        self.mock_s3 = MagicMock()
        self.mock_boto3_client.return_value = self.mock_s3
        
        # Initialize S3FileManager with test values
        self.s3_manager = S3FileManager(
            bucket_name=self.bucket_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        )
        
    def tearDown(self):
        """Tear down test fixtures"""
        self.boto3_client_patcher.stop()
    
    def test_init_with_credentials(self):
        """Test initialization with AWS credentials"""
        # boto3.client should be called with the provided credentials
        self.mock_boto3_client.assert_called_with(
            's3',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        )
        self.assertEqual(self.s3_manager.bucket_name, self.bucket_name)
    
    def test_init_without_credentials(self):
        """Test initialization without AWS credentials"""
        self.boto3_client_patcher.stop()
        with patch('boto3.client') as mock_client:
            S3FileManager(bucket_name=self.bucket_name)
            # boto3.client should be called without credentials
            mock_client.assert_called_with('s3')
        
        # Restart the patcher for other tests
        self.mock_boto3_client = self.boto3_client_patcher.start()
        self.mock_boto3_client.return_value = self.mock_s3
    
    def test_init_empty_bucket_name(self):
        """Test initialization with empty bucket name"""
        with self.assertRaises(ValueError):
            S3FileManager(bucket_name="")
    
    def test_context_manager(self):
        """Test context manager functionality"""
        with S3FileManager(bucket_name=self.bucket_name) as s3_manager:
            self.assertIsInstance(s3_manager, S3FileManager)
    
    def test_write_file_string(self):
        """Test write_file method with string data"""
        key = "test/file.txt"
        data = "Hello, world!"
        content_type = "text/plain"
        
        # Mock successful response
        self.mock_s3.put_object.return_value = {"ETag": "test-etag"}
        
        response = self.s3_manager.write_file(key, data, content_type)
        
        # Verify put_object was called with correct parameters
        self.mock_s3.put_object.assert_called_with(
            Bucket=self.bucket_name,
            Key=key,
            Body=data.encode('utf-8'),
            ContentType=content_type
        )
        self.assertEqual(response, {"ETag": "test-etag"})
    
    def test_write_file_bytes(self):
        """Test write_file method with bytes data"""
        key = "test/file.bin"
        data = b"Hello, world!"
        
        # Mock successful response
        self.mock_s3.put_object.return_value = {"ETag": "test-etag"}
        
        response = self.s3_manager.write_file(key, data)
        
        # Verify put_object was called with correct parameters
        self.mock_s3.put_object.assert_called_with(
            Bucket=self.bucket_name,
            Key=key,
            Body=data
        )
        self.assertEqual(response, {"ETag": "test-etag"})
    
    def test_write_file_empty_key(self):
        """Test write_file method with empty key"""
        with self.assertRaises(ValueError):
            self.s3_manager.write_file("", "data")
    
    def test_write_file_error(self):
        """Test write_file method with boto3 client error"""
        key = "test/file.txt"
        data = "Hello, world!"
        
        # Mock ClientError
        self.mock_s3.put_object.side_effect = ClientError(
            {"Error": {"Code": "InternalError", "Message": "Test error"}},
            "PutObject"
        )
        
        response = self.s3_manager.write_file(key, data)
        self.assertIsNone(response)
    
    def test_read_file_success(self):
        """Test read_file method with successful read"""
        key = "test/file.txt"
        mock_body = MagicMock()
        mock_body.read.return_value = b"Hello, world!"
        
        # Mock successful response
        self.mock_s3.get_object.return_value = {"Body": mock_body}
        
        content = self.s3_manager.read_file(key)
        
        # Verify get_object was called with correct parameters
        self.mock_s3.get_object.assert_called_with(
            Bucket=self.bucket_name,
            Key=key
        )
        self.assertEqual(content, b"Hello, world!")
    
    def test_read_file_empty_key(self):
        """Test read_file method with empty key"""
        with self.assertRaises(ValueError):
            self.s3_manager.read_file("")
    
    def test_read_file_error(self):
        """Test read_file method with boto3 client error"""
        key = "test/file.txt"
        
        # Mock ClientError
        self.mock_s3.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}},
            "GetObject"
        )
        
        content = self.s3_manager.read_file(key)
        self.assertIsNone(content)
    
    def test_file_exists_true(self):
        """Test file_exists method when file exists"""
        key = "test/file.txt"
        
        # Mock successful head_object call
        self.mock_s3.head_object.return_value = {}
        
        exists = self.s3_manager.file_exists(key)
        
        # Verify head_object was called with correct parameters
        self.mock_s3.head_object.assert_called_with(
            Bucket=self.bucket_name,
            Key=key
        )
        self.assertTrue(exists)
    
    def test_file_exists_false(self):
        """Test file_exists method when file does not exist"""
        key = "test/file.txt"
        
        # Mock ClientError for non-existent file
        self.mock_s3.head_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}},
            "HeadObject"
        )
        
        exists = self.s3_manager.file_exists(key)
        self.assertFalse(exists)
    
    def test_delete_file_success(self):
        """Test delete_file method with successful delete"""
        key = "test/file.txt"
        
        # Mock successful response
        self.mock_s3.delete_object.return_value = {}
        
        success = self.s3_manager.delete_file(key)
        
        # Verify delete_object was called with correct parameters
        self.mock_s3.delete_object.assert_called_with(
            Bucket=self.bucket_name,
            Key=key
        )
        self.assertTrue(success)
    
    def test_delete_file_empty_key(self):
        """Test delete_file method with empty key"""
        with self.assertRaises(ValueError):
            self.s3_manager.delete_file("")
    
    def test_delete_file_error(self):
        """Test delete_file method with boto3 client error"""
        key = "test/file.txt"
        
        # Mock ClientError
        self.mock_s3.delete_object.side_effect = ClientError(
            {"Error": {"Code": "InternalError", "Message": "Test error"}},
            "DeleteObject"
        )
        
        success = self.s3_manager.delete_file(key)
        self.assertFalse(success)
    
    def test_list_files_success(self):
        """Test list_files method with successful listing"""
        prefix = "test/"
        max_items = 100
        
        # Create mock paginator
        mock_paginator = MagicMock()
        self.mock_s3.get_paginator.return_value = mock_paginator
        
        # Create mock page iterator
        mock_page_iterator = MagicMock()
        mock_paginator.paginate.return_value = mock_page_iterator
        
        # Create mock pages
        mock_page_iterator.__iter__.return_value = [
            {
                "Contents": [
                    {"Key": "test/file1.txt", "Size": 100},
                    {"Key": "test/file2.txt", "Size": 200}
                ]
            },
            {
                "Contents": [
                    {"Key": "test/file3.txt", "Size": 300}
                ]
            }
        ]
        
        files = self.s3_manager.list_files(prefix, max_items)
        
        # Verify get_paginator was called
        self.mock_s3.get_paginator.assert_called_with('list_objects_v2')
        
        # Verify paginate was called with correct parameters
        mock_paginator.paginate.assert_called_with(
            Bucket=self.bucket_name,
            Prefix=prefix,
            PaginationConfig={'MaxItems': max_items}
        )
        
        # Verify the returned files list
        self.assertEqual(len(files), 3)
        self.assertEqual(files[0]["Key"], "test/file1.txt")
        self.assertEqual(files[1]["Key"], "test/file2.txt")
        self.assertEqual(files[2]["Key"], "test/file3.txt")
    
    def test_list_files_empty(self):
        """Test list_files method with no files"""
        # Create mock paginator
        mock_paginator = MagicMock()
        self.mock_s3.get_paginator.return_value = mock_paginator
        
        # Create mock page iterator
        mock_page_iterator = MagicMock()
        mock_paginator.paginate.return_value = mock_page_iterator
        
        # Create mock empty pages
        mock_page_iterator.__iter__.return_value = [{}]
        
        files = self.s3_manager.list_files()
        
        self.assertEqual(files, [])
    
    def test_list_files_error(self):
        """Test list_files method with boto3 client error"""
        # Mock ClientError
        self.mock_s3.get_paginator.side_effect = ClientError(
            {"Error": {"Code": "InternalError", "Message": "Test error"}},
            "ListObjectsV2"
        )
        
        files = self.s3_manager.list_files()
        self.assertEqual(files, [])
    
    def test_copy_file_success(self):
        """Test copy_file method with successful copy"""
        source_key = "test/source.txt"
        dest_key = "test/dest.txt"
        
        # Mock successful response
        self.mock_s3.copy_object.return_value = {}
        
        success = self.s3_manager.copy_file(source_key, dest_key)
        
        # Verify copy_object was called with correct parameters
        self.mock_s3.copy_object.assert_called_with(
            CopySource={'Bucket': self.bucket_name, 'Key': source_key},
            Bucket=self.bucket_name,
            Key=dest_key
        )
        self.assertTrue(success)
    
    def test_copy_file_empty_keys(self):
        """Test copy_file method with empty keys"""
        with self.assertRaises(ValueError):
            self.s3_manager.copy_file("", "dest.txt")
        
        with self.assertRaises(ValueError):
            self.s3_manager.copy_file("source.txt", "")
    
    def test_copy_file_error(self):
        """Test copy_file method with boto3 client error"""
        source_key = "test/source.txt"
        dest_key = "test/dest.txt"
        
        # Mock ClientError
        self.mock_s3.copy_object.side_effect = ClientError(
            {"Error": {"Code": "InternalError", "Message": "Test error"}},
            "CopyObject"
        )
        
        success = self.s3_manager.copy_file(source_key, dest_key)
        self.assertFalse(success)
    
    @patch('os.path.exists')
    def test_upload_file_success(self, mock_exists):
        """Test upload_file method with successful upload"""
        local_path = "local/file.txt"
        s3_key = "remote/file.txt"
        content_type = "text/plain"
        
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock successful response
        self.mock_s3.upload_file.return_value = None
        
        success = self.s3_manager.upload_file(local_path, s3_key, content_type)
        
        # Verify upload_file was called with correct parameters
        self.mock_s3.upload_file.assert_called_with(
            local_path,
            self.bucket_name,
            s3_key,
            ExtraArgs={'ContentType': content_type}
        )
        self.assertTrue(success)
    
    @patch('os.path.exists')
    def test_upload_file_no_content_type(self, mock_exists):
        """Test upload_file method without content type"""
        local_path = "local/file.txt"
        s3_key = "remote/file.txt"
        
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock successful response
        self.mock_s3.upload_file.return_value = None
        
        success = self.s3_manager.upload_file(local_path, s3_key)
        
        # Verify upload_file was called with correct parameters
        self.mock_s3.upload_file.assert_called_with(
            local_path,
            self.bucket_name,
            s3_key,
            ExtraArgs={}
        )
        self.assertTrue(success)
    
    @patch('os.path.exists')
    def test_upload_file_nonexistent(self, mock_exists):
        """Test upload_file method with nonexistent local file"""
        local_path = "local/file.txt"
        s3_key = "remote/file.txt"
        
        # Mock file non-existence
        mock_exists.return_value = False
        
        success = self.s3_manager.upload_file(local_path, s3_key)
        
        # Verify upload_file was not called
        self.mock_s3.upload_file.assert_not_called()
        self.assertFalse(success)
    
    @patch('os.path.exists')
    def test_upload_file_error(self, mock_exists):
        """Test upload_file method with boto3 client error"""
        local_path = "local/file.txt"
        s3_key = "remote/file.txt"
        
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock ClientError
        self.mock_s3.upload_file.side_effect = ClientError(
            {"Error": {"Code": "InternalError", "Message": "Test error"}},
            "UploadFile"
        )
        
        success = self.s3_manager.upload_file(local_path, s3_key)
        self.assertFalse(success)
    
    @patch('os.makedirs')
    def test_download_file_success(self, mock_makedirs):
        """Test download_file method with successful download"""
        s3_key = "remote/file.txt"
        local_path = "local/file.txt"
        
        # Mock successful response
        self.mock_s3.download_file.return_value = None
        
        success = self.s3_manager.download_file(s3_key, local_path)
        
        # Verify makedirs was called to ensure directory exists
        mock_makedirs.assert_called_with(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
        
        # Verify download_file was called with correct parameters
        self.mock_s3.download_file.assert_called_with(
            self.bucket_name,
            s3_key,
            local_path
        )
        self.assertTrue(success)
    
    @patch('os.makedirs')
    def test_download_file_error(self, mock_makedirs):
        """Test download_file method with boto3 client error"""
        s3_key = "remote/file.txt"
        local_path = "local/file.txt"
        
        # Mock ClientError
        self.mock_s3.download_file.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}},
            "DownloadFile"
        )
        
        success = self.s3_manager.download_file(s3_key, local_path)
        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main() 