## [2.0.0] - 05-07-2026
### Major Changes
- Removed AWS S3 dependency. Files are now saved locally to the user-specified output directory.
- Removed `.env` configuration requirement. No AWS credentials needed.

### Removed
- `boto3`, `botocore`, `s3transfer`, `python-dotenv` dependencies