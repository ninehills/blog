#!/usr/bin/env python3

import os
import re
import json
import logging
import subprocess

logging.basicConfig(level=logging.INFO)

GH = "gh"
POSTS_DIR = "_posts"
LABELS = set(["blog"])
TIMEOUT = 20


def slugify(title: str, number: int) -> str:
    return str(number)


def date_from_iso(dt: str) -> str:
    return dt.split("T")[0]


def clean_body(body: str) -> str:
    return body.strip().replace("\r\n", "\n")


def extract_description(body: str, fallback: str, max_chars: int = 120) -> str:
    """Extract a short description from the issue body (first meaningful paragraph)."""
    lines = body.strip().split('\n')
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or stripped.startswith('![') or stripped.startswith('>'):
            continue
        stripped = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', stripped)
        stripped = re.sub(r'[*_`~]', '', stripped)
        if len(stripped) > max_chars:
            stripped = stripped[:max_chars-3] + '...'
        return stripped
    return fallback


## 1. find all issues with specific labels
issues_json = subprocess.check_output(
    "gh issue list --state open --json title,url,author,number,labels,updatedAt,createdAt",
    shell=True, timeout=TIMEOUT)
logging.info("issues_json: %s", issues_json)

issues = json.loads(issues_json)
issues = [issue for issue in issues if LABELS.intersection(
    set([label["name"] for label in issue["labels"]]))]
logging.info("issues with filter: %s", issues)

## 2. Generate README.md (for GitHub repo display)
with open("README.md", "w") as f:
    f.write("# 九原山\n\n")
    f.write("技术笔记与思考。关注大语言模型、AI Agent、推理优化、SRE 等领域。\n\n")
    f.write("> 访问 [ninehills.tech](https://ninehills.tech) 查看博客。\n\n")
    f.write("## Posts\n\n")
    for issue in issues:
        date = date_from_iso(issue['createdAt'])
        labels = " ".join([f"`{label['name']}`" for label in issue['labels']])
        f.write(
            f"- #{issue['number']} [{issue['title']}]({issue['url']}) {date} {labels}\n")

## 3. Generate Jekyll posts in _posts/
os.makedirs(POSTS_DIR, exist_ok=True)

for issue in issues:
    r = subprocess.check_output(
        f"gh issue view {issue['number']} --json title,url,author,number,labels,createdAt,updatedAt,body",
        shell=True, timeout=TIMEOUT)
    issue_data = json.loads(r)
    logging.info("process issue: %s", issue_data)

    date = date_from_iso(issue_data['createdAt'])
    slug = slugify(issue_data['title'], issue_data['number'])
    filename = f"{date}-{slug}.md"
    filepath = os.path.join(POSTS_DIR, filename)

    tags = [label['name'] for label in issue_data['labels']
            if label['name'] != 'blog']

    # Preserve existing description if the post already has one (not auto-generated)
    existing_desc = None
    if os.path.exists(filepath):
        with open(filepath) as f:
            old = f.read()
        m = re.search(r'^description:\s*"(.*?)"', old, re.MULTILINE)
        if m:
            existing_desc = m.group(1)
    
    description = existing_desc or extract_description(issue_data.get('body', ''), issue_data['title'])

    front_matter = f"""---
layout: post
title: "{issue_data['title']}"
description: "{description}"
author: {issue_data['author']['login']}
date: {date}
comments_url: {issue_data['url']}
"""
    if tags:
        front_matter += f"tags: [{', '.join(tags)}]\n"

    # Metadata blockquote placed at the BOTTOM so excerpts show clean content
    meta = (
        f"\n\n---\n\n"
        f"> 原文发布于 [GitHub Issue #{issue_data['number']}]({issue_data['url']})  \n"
        f"> 创建于 {issue_data['createdAt']}，更新于 {issue_data['updatedAt']}\n"
    )

    front_matter += "---\n\n"
    body = clean_body(issue_data['body'])

    with open(filepath, "w") as f:
        f.write(front_matter)
        f.write(body)
        f.write(meta)
        f.write("\n")

    logging.info("wrote: %s", filepath)

logging.info("Done. Generated %d posts.", len(issues))
