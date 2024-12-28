import boto3
from botocore.exceptions import NoCredentialsError
from django.conf import settings

def generate_presigned_url(bucket_name, object_name, expiration=3600, operation='get_object'):
    """
    Generate a pre-signed URL for an S3 object.
    Supports both 'get_object' (download) and 'put_object' (upload) operations.
    
    :param bucket_name: S3 bucket name
    :param object_name: Object key (file path) in the S3 bucket
    :param expiration: Time in seconds for the pre-signed URL to remain valid
    :param operation: S3 operation ('get_object' for download, 'put_object' for upload)
    :return: Pre-signed URL or None if an error occurs
    """
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )

    try:
        response = s3_client.generate_presigned_url(
            operation,
            Params={'Bucket': bucket_name, 'Key': object_name},
            ExpiresIn=expiration
        )
    except NoCredentialsError:
        return None

    return response
