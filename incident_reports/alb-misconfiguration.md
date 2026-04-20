# Incident: ALB Misconfiguration (502 Bad Gateway)

## Stage
Post-deploy (traffic routing)

## Symptoms
Users received: `502 Bad Gateway`

## Root Cause
Target group configured with incorrect port, causing ALB to route traffic to a non-listening port.

## Debugging Steps
- Checked ALB target group settings
- Verified port mappings (8080 / 8081)
- Ran `ss -tlnp` on EC2 to confirm listening ports
- Tested locally via curl

## Fix Applied
- Corrected target group port configuration
- Revalidated ALB routing

## Key Learnings
- Infrastructure misconfigurations can mimic application failures
- Always verify network layer before debugging app
- ALB health checks are critical for routing correctness