#!/bin/bash
# Setup Cognito Test Users - Bash version
# Creates admin and researcher users in Cognito User Pool

USER_POOL_ID="ap-southeast-1_8KB4JYvsX"
REGION="ap-southeast-1"

echo "=========================================="
echo "Setting up Cognito Test Users"
echo "=========================================="
echo "User Pool ID: $USER_POOL_ID"
echo "Region: $REGION"
echo ""

# Function to create user
create_user() {
    local email=$1
    local password=$2
    local name=$3
    local group=$4

    echo "📧 Creating user: $email"
    
    # Create user
    aws cognito-idp admin-create-user \
        --user-pool-id "$USER_POOL_ID" \
        --username "$email" \
        --user-attributes Name=email,Value="$email" Name=email_verified,Value=true Name=name,Value="$name" \
        --temporary-password "$password" \
        --message-action SUPPRESS \
        --region "$REGION" 2>/dev/null
    
    if [ $? -eq 0 ] || [ $? -eq 254 ]; then
        echo "✅ User created or already exists: $email"
    else
        echo "❌ Failed to create user: $email"
        return 1
    fi

    # Set permanent password
    aws cognito-idp admin-set-user-password \
        --user-pool-id "$USER_POOL_ID" \
        --username "$email" \
        --password "$password" \
        --permanent \
        --region "$REGION" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ Password set for: $email"
    else
        echo "❌ Failed to set password for: $email"
        return 1
    fi

    # Create group if not exists
    aws cognito-idp create-group \
        --group-name "$group" \
        --user-pool-id "$USER_POOL_ID" \
        --description "$group users" \
        --region "$REGION" 2>/dev/null

    # Add user to group
    aws cognito-idp admin-add-user-to-group \
        --user-pool-id "$USER_POOL_ID" \
        --username "$email" \
        --group-name "$group" \
        --region "$REGION" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ Added to group: $group"
    else
        echo "❌ Failed to add to group: $group"
        return 1
    fi

    echo "✅ Successfully setup: $email"
    echo ""
}

# Create admin user
create_user "admin@arc.com" "Admin123!" "Admin User" "admin"

# Create researcher user
create_user "researcher@arc.com" "Researcher123!" "Researcher User" "researcher"

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Test Credentials:"
echo "------------------------------------------"
echo "Admin:"
echo "  Email: admin@arc.com"
echo "  Password: Admin123!"
echo ""
echo "Researcher:"
echo "  Email: researcher@arc.com"
echo "  Password: Researcher123!"
echo ""
echo "Login at: http://localhost:5173/login"
echo ""
