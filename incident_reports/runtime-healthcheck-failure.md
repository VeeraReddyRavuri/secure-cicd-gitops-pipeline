# Incident: Runtime Failure Detected During Canary Deployment

## Stage
Post-deploy (validation phase)

## Symptoms
- ALB returned intermittent 502/500 responses
- Validation step recorded elevated failure rate
- Example output:
```
Attempt 4 → Status: 502
Attempt 9 → Status: 502
Total failures: X
```

## Root Cause
New application version deployed to Green returned errors under runtime conditions not caught during testing.

## Debugging Steps
- Observed validation logs in pipeline
- Checked container logs via `docker logs green`
- Verified Green environment behavior

## Fix Applied
- Automatic rollback triggered:
  - ALB traffic shifted to 100% Blue
  - Manifest repo reverted to previous stable version

## Key Learnings
- Build/test success ≠ runtime success
- Canary deployments reduce blast radius
- Automated rollback is critical for resilienc