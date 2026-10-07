# Agent Runtime Bridge

This is a free local bridge for the Agent Studio chat.

Browser -> http://127.0.0.1:8787 -> GitHub Actions -> Agent Runtime.

## Windows PowerShell

Set a GitHub token only in your local terminal environment:

    $env:GITHUB_TOKEN="YOUR_TOKEN"
    python bridge/server.py

Keep the terminal running while using Execute in Agent Runtime.

## macOS / Linux

    export GITHUB_TOKEN="YOUR_TOKEN"
    python3 bridge/server.py

## Token permissions

Use the minimum permissions required by your repository. Never put the token in frontend code, status.json, or any committed file.

## Health check

With the bridge running, the Studio chat should show Bridge Connected.

If it shows Bridge Offline, start the local bridge and refresh the page.

The bridge only accepts the five validated runtime actions: claim, assign, verify, complete, fail.
