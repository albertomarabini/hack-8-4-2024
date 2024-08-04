#!/bin/bash

# Update package list
sudo apt update

# Install Python (replace with the version you have if needed)
sudo apt install -y python3.12.3

# Install pip
sudo apt install -y python3-pip

# Install LangChain (replace with the version you have if needed)
pip3 install langchain==0.1.20

# Verify installations
python3 --version
pip3 show langchain
