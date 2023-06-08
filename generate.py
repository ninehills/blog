#!/usr/bin/env python3

import os
import sys
import json

issues = json.loads(sys.stdin.read())

print("""# 九原山

## Posts
""")

for issue in issues:
    print(f"- #{issue['number']} [{issue['title']}]({issue['url']}) {issue['updatedAt'].split('T')[0]}")

