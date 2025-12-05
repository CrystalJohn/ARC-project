#!/usr/bin/env python3
"""
Setup Cognito Test Users
Creates admin and researcher users in Cognito User Pool for testing
"""

import boto3
import sys
from botocore.exceptions import ClientError

# Cognito configuration from Task #12
USER_POOL_ID = 'ap-southeast-1_8KB4JYvsX'
REGION = 'ap-southeast-1'

# Test users to create
TEST_USERS = [
    {
        'email': 'admin@arc.com',
        'password': 'Admin123!',
        'group': 'admin',
        'name': 'Admin User'
    },
    {
        'email': 'researcher@arc.com',
        'password': 'Researcher123!',
        'group': 'researcher',
        'name': 'Researcher User'
    }
]

def create_cognito_user(client, user_pool_id, email, password, name):
    """Create a user in Cognito User Pool"""
    try:
        response = client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'email_verified', 'Value': 'true'},
                {'Name': 'name', 'Value': name}
            ],
            TemporaryPassword=password,
            MessageAction='SUPPRESS'  # Don't send welcome email
        )
        print(f"✅ Created user: {email}")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'UsernameExistsException':
            print(f"⚠️  User already exists: {email}")
            return True
        else:
            print(f"❌ Error creating user {email}: {e}")
            return False

def set_permanent_password(client, user_pool_id, email, password):
    """Set permanent password for user"""
    try:
        client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=email,
            Password=password,
            Permanent=True
        )
        print(f"✅ Set permanent password for: {email}")
        return True
    except ClientError as e:
        print(f"❌ Error setting password for {email}: {e}")
        return False

def add_user_to_group(client, user_pool_id, email, group_name):
    """Add user to Cognito group"""
    try:
        client.admin_add_user_to_group(
            UserPoolId=user_pool_id,
            Username=email,
            GroupName=group_name
        )
        print(f"✅ Added {email} to group: {group_name}")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"❌ Group '{group_name}' does not exist. Creating it...")
            try:
                client.create_group(
                    GroupName=group_name,
                    UserPoolId=user_pool_id,
                    Description=f'{group_name.capitalize()} users'
                )
                print(f"✅ Created group: {group_name}")
                # Retry adding user to group
                return add_user_to_group(client, user_pool_id, email, group_name)
            except ClientError as create_error:
                print(f"❌ Error creating group {group_name}: {create_error}")
                return False
        else:
            print(f"❌ Error adding {email} to group {group_name}: {e}")
            return False

def main():
    print("=" * 60)
    print("Setting up Cognito Test Users")
    print("=" * 60)
    print(f"User Pool ID: {USER_POOL_ID}")
    print(f"Region: {REGION}")
    print()

    # Initialize Cognito client
    try:
        client = boto3.client('cognito-idp', region_name=REGION)
        print("✅ Connected to AWS Cognito")
    except Exception as e:
        print(f"❌ Failed to connect to AWS: {e}")
        print("\nMake sure you have:")
        print("1. AWS CLI configured (aws configure)")
        print("2. Proper IAM permissions for Cognito")
        sys.exit(1)

    print()
    print("Creating test users...")
    print("-" * 60)

    success_count = 0
    for user in TEST_USERS:
        print(f"\n📧 Processing: {user['email']}")
        
        # Create user
        if not create_cognito_user(client, USER_POOL_ID, user['email'], user['password'], user['name']):
            continue
        
        # Set permanent password
        if not set_permanent_password(client, USER_POOL_ID, user['email'], user['password']):
            continue
        
        # Add to group
        if not add_user_to_group(client, USER_POOL_ID, user['email'], user['group']):
            continue
        
        success_count += 1
        print(f"✅ Successfully setup: {user['email']}")

    print()
    print("=" * 60)
    print(f"Setup Complete: {success_count}/{len(TEST_USERS)} users configured")
    print("=" * 60)
    print()
    print("Test Credentials:")
    print("-" * 60)
    for user in TEST_USERS:
        print(f"Email: {user['email']}")
        print(f"Password: {user['password']}")
        print(f"Group: {user['group']}")
        print()
    
    print("You can now login at: http://localhost:5173/login")
    print()

if __name__ == '__main__':
    main()
