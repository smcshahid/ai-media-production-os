#!/usr/bin/env bash
sudo k3s kubectl get pod -n aimpos-mwayolares -l app=aimpos-api -o jsonpath='{.items[0].spec.containers[0].image}{"\n"}'
sudo k3s kubectl get pod -n aimpos-mwayolares -l app=aimpos-api -o jsonpath='{.items[0].status.containerStatuses[0].imageID}{"\n"}'
sudo ctr -a /run/containerd/containerd.sock -n k8s.io images ls | grep aimpos-api
