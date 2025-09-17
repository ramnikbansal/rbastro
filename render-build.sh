#!/usr/bin/env bash

# Upgrade pip just in case
pip install --upgrade pip

# Force install swisseph and dependencies
pip install --no-cache-dir --force-reinstall swisseph
pip install --no-cache-dir -r requirements.txt
