#!/bin/bash
# EC2 Setup Script for Calls Summary
# Run on a fresh Ubuntu 24.04 EC2 instance
# Usage: curl -sSL https://raw.githubusercontent.com/Ziv1972/calls_summery/main/deploy/setup-ec2.sh | bash

set -e

echo "=== Calls Summary - EC2 Setup ==="
echo ""

# 1. Install Docker
echo "Installing Docker..."
sudo apt-get update -qq
sudo apt-get install -y -qq ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -qq
sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER
echo "Docker installed."

# 2. Clone repo
echo "Cloning repository..."
cd ~
if [ -d "calls_summery" ]; then
    echo "Repository already exists, pulling latest..."
    cd calls_summery
    git pull
else
    git clone https://github.com/Ziv1972/calls_summery.git
    cd calls_summery
fi

# 3. Setup .env
if [ ! -f .env ]; then
    echo ""
    echo "=== IMPORTANT: Configure your .env file ==="
    echo "Copy the example and fill in your API keys:"
    echo ""
    echo "  cp .env.example .env"
    echo "  nano .env"
    echo ""
    echo "Required keys: AWS, Deepgram, Anthropic, SendGrid, SECRET_KEY"
    echo "Set FRONTEND_URL=http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo 'YOUR-EC2-IP'):8501"
    echo ""
    cp .env.example .env
    echo "Created .env from .env.example. Edit it before starting!"
    echo ""
    echo "After editing .env, start the app with:"
    echo "  cd ~/calls_summery"
    echo "  docker compose up -d --build"
    echo ""
else
    echo ".env file already exists."
fi

# 4. Print access info
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "YOUR-EC2-IP")
echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit .env with your API keys: nano ~/calls_summery/.env"
echo "  2. Start the app: cd ~/calls_summery && docker compose up -d --build"
echo "  3. Check status: docker compose ps"
echo "  4. View logs: docker compose logs -f"
echo ""
echo "Access URLs (after starting):"
echo "  UI:   http://${PUBLIC_IP}:8501"
echo "  API:  http://${PUBLIC_IP}:8001/docs"
echo ""
echo "Security Group: Make sure ports 22, 8501, 8001 are open."
echo ""
echo "NOTE: Log out and back in for Docker permissions to take effect."
