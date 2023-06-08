#!/bin/bash
# need install gh/python


gh issue list --state open --json title,url,author,number,labels,updatedAt > issues.json
cat issues.json | python3 generate.py > README.md
