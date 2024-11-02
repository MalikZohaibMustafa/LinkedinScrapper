#!/usr/bin/env bash

# Install Chromium and necessary dependencies
apt-get update && apt-get install -y chromium-browser chromium-chromedriver

pip install -r requirements.txt
