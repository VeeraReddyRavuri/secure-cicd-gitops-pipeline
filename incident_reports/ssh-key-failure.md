# Incident: SSH Key Misconfiguration (Manifest Repo Access Failure)

## Stage
Deploy (manifest repo clone step)

## Symptoms
Pipeline failed during manifest repo clone step with error:
```
git@github.com: Permission denied (publickey).
fatal: Could not read from remote repository.
```

## Root Cause
Incorrect private SSH key stored in GitHub Secrets did not match the deploy key configured in the manifest repository.

## Debugging Steps
- Checked failing pipeline step logs
- Identified failure at `git clone` command
- Verified SSH key used in workflow
- Compared with deploy key in manifest repo settings

## Fix Applied
- Updated `MANIFEST_REPO_SSH_KEY` secret with correct private key
- Re-ran pipeline

## Key Learnings
- SSH-based GitOps requires strict key alignment
- Deployment failures can occur before runtime even begins
- Always validate secrets independently before pipeline execution