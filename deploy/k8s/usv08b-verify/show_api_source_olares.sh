#!/usr/bin/env bash
sudo k3s kubectl exec deploy/aimpos-api -n aimpos-mwayolares -- sed -n '140,150p' /usr/local/lib/python3.12/site-packages/app/domain/character/service.py
