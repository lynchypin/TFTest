#!/bin/bash
# Bootstrap script to create S3 bucket and DynamoDB table for Terraform state
# Run this ONCE before using S3 backend

set -e

BUCKET_NAME="${1:-pagerduty-tf-state-$(whoami)}"
REGION="${2:-us-east-1}"
DYNAMODB_TABLE="terraform-state-lock"

echo "Creating S3 bucket: $BUCKET_NAME"
aws s3api create-bucket \
  --bucket "$BUCKET_NAME" \
  --region "$REGION" \
  ${REGION != "us-east-1" && echo "--create-bucket-configuration LocationConstraint=$REGION"}

echo "Enabling versioning..."
aws s3api put-bucket-versioning \
  --bucket "$BUCKET_NAME" \
  --versioning-configuration Status=Enabled

echo "Enabling encryption..."
aws s3api put-bucket-encryption \
  --bucket "$BUCKET_NAME" \
  --server-side-encryption-configuration '{
    "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
  }'

echo "Blocking public access..."
aws s3api put-public-access-block \
  --bucket "$BUCKET_NAME" \
  --public-access-block-configuration '{
    "BlockPublicAcls": true,
    "IgnorePublicAcls": true,
    "BlockPublicPolicy": true,
    "RestrictPublicBuckets": true
  }'

echo "Creating DynamoDB table: $DYNAMODB_TABLE"
aws dynamodb create-table \
  --table-name "$DYNAMODB_TABLE" \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region "$REGION" || echo "Table may already exist"

echo ""
echo "✅ Done! Update backend.tf with:"
echo ""
echo "terraform {"
echo "  backend \"s3\" {"
echo "    bucket         = \"$BUCKET_NAME\""
echo "    key            = \"pagerduty-demo/terraform.tfstate\""
echo "    region         = \"$REGION\""
echo "    encrypt        = true"
echo "    dynamodb_table = \"$DYNAMODB_TABLE\""
echo "  }"
echo "}"
