#!/bin/bash
# User data script for EC2 instance setup

# Update system
yum update -y

# Install and start SSM Agent (for Session Manager)
yum install -y amazon-ssm-agent
systemctl enable amazon-ssm-agent
systemctl start amazon-ssm-agent

# Install Docker
yum install -y docker

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Add ec2-user to docker group
usermod -aG docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create application directory
mkdir -p /home/ec2-user/app
cd /home/ec2-user/app

# Create FastAPI boilerplate
cat > /home/ec2-user/app/main.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="ARC Chatbot API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "ARC Chatbot API is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# Create requirements.txt
cat > /home/ec2-user/app/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
boto3==1.29.7
python-dotenv==1.0.0
EOF

# Create Dockerfile
cat > /home/ec2-user/app/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Create docker-compose.yml
cat > /home/ec2-user/app/docker-compose.yml << 'EOF'
version: '3.8'

services:
  fastapi:
    build: .
    ports:
      - "8000:8000"
    restart: always
    environment:
      - AWS_DEFAULT_REGION=ap-southeast-1
    volumes:
      - ./main.py:/app/main.py

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage
    restart: always

volumes:
  qdrant_storage:
EOF

# Set ownership
chown -R ec2-user:ec2-user /home/ec2-user/app

# Build and start containers
cd /home/ec2-user/app
docker-compose up -d

# Log completion
echo "EC2 setup completed at $(date)" >> /var/log/user-data.log
