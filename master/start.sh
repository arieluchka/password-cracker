#!/bin/bash

setsid python master/MasterCracker.py </dev/null > /dev/null 2>&1 &

sleep 3
python master/cli.py
