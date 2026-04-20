# Incident: Dockerfile Syntax Error

## Stage
Build (docker build step)

## Symptoms
Pipeline failed during image build with error:
```
unknown instruction: FORM
```

## Root Cause
Typo in Dockerfile instruction (`FORM` instead of `FROM`)

## Debugging Steps
- Identified failure in build step logs
- Inspected Dockerfile
- Located incorrect instruction
- Compared against valid Dockerfile syntax

## Fix Applied
- Corrected instruction to `FROM`
- Rebuilt image via pipeline

## Key Learnings
- Build stage acts as first line of defense
- Small syntax errors completely block deployment
- CI prevents invalid artifacts from progressing further