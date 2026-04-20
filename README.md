# Secure CI/CD with GitOps and Automated Rollback

> A fault-tolerant deployment pipeline that minimizes production risk using canary releases, health-based validation, and instant rollback with GitOps consistency.

![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat&logo=githubactions&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python_3.12-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-232F3E?style=flat&logo=amazonaws&logoColor=white)
![Amazon S3](https://img.shields.io/badge/Amazon_S3-569A31?style=flat&logo=amazons3&logoColor=white)
![Amazon EC2](https://img.shields.io/badge/Amazon_EC2-FF9900?style=flat&logo=amazonec2&logoColor=white)
![DockerHub](https://img.shields.io/badge/DockerHub-2496ED?style=flat&logo=docker&logoColor=white)
![Trivy](https://img.shields.io/badge/Trivy-1904DA?style=flat&logo=aquasecurity&logoColor=white)
![Git](https://img.shields.io/badge/Git-F05032?style=flat&logo=git&logoColor=white)
![YAML](https://img.shields.io/badge/YAML-CB171E?style=flat&logo=yaml&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=flat&logo=linux&logoColor=black)

---

## TL;DR

- Built a production-style CI/CD pipeline that performs secure image builds, GitOps-based deployments, canary traffic shifting via AWS ALB, and automated rollback (traffic + state) based on runtime health validation. 
- Demonstrates real-world deployment safety patterns beyond simple push-to-deploy pipelines including supply chain security, manifest repo separation, and failure-driven engineering.

---

## Tech Stack

| Category       | Tools                              |
|----------------|------------------------------------|
| CI/CD          | GitHub Actions                     |
| Security       | Trivy (CVE scanning)               |
| Registry       | DockerHub                          |
| Infra          | AWS EC2, ALB, S3                   |
| Observability  | ALB Health Checks, CloudWatch      |
| GitOps         | Manifest Repository Pattern        |
| Language       | Python 3.12 / Fast API             |

---

## Architecture

```mermaid
flowchart TD
    DEV([Developer]) -->|git push to main| GH[GitHub App Repo]

    GH -->|triggers| GA[GitHub Actions Pipeline]

    subgraph CI ["CI — Verify & Build"]
        GA --> LINT[Lint - flake8]
        GA --> TEST[Test - pytest]
        LINT --> BUILD[Build Docker Image\ngit SHA tag]
        TEST --> BUILD
        BUILD --> TRIVY{Trivy Scan\nCRITICAL CVE?}
        TRIVY -->|CVE found| FAIL[ Pipeline Fails\nDeploy Blocked]
        TRIVY -->|Clean| PUSH[Push Image to DockerHub]
    end

    subgraph ARTIFACT ["Artifact & Metadata"]
        PUSH --> S3[Upload deployment record to S3 (stores commit SHA, timestamp, scan status for audit and incident debugging)\nSHA · timestamp · trivy status]
    end

    subgraph GITOPS ["GitOps — Manifest Update"]
        S3 --> MANIFEST[Update Manifest Repo\ndeployment.yml → new image SHA]
    end

    subgraph DEPLOY ["Deploy — Blue/Green Canary"]
        MANIFEST --> GREEN[Start Green Container\nEC2 port 8081]
        GREEN --> ALB[ALB Listener Rule\n90% Blue · 10% Green]
        ALB --> BLUE[Blue Container\nEC2 port 8080]
        ALB --> GREENC[Green Container\nEC2 port 8081]
    end

    subgraph VALIDATE ["Validate — Health Check Loop"]
        ALB --> VAL{Failure Rate\n≥ Threshold?}
        VAL -->|No — healthy| PROMOTE[Promote Green to 100%\nDecommission Blue]
        VAL -->|Yes — unhealthy| ROLLBACK[Automatic Rollback]
        ROLLBACK --> RB1[ALB → 100% Blue]
        ROLLBACK --> RB2[git revert Manifest Repo]
        RB1 --> SAFE[✅ System Restored\nLast Known Good State]
        RB2 --> SAFE
    end

    PROMOTE --> USERS([🌐 Users])
    BLUE --> USERS
    GREENC --> USERS

    style FAIL fill:#ff4d4d,color:#fff
    style SAFE fill:#2d8a4e,color:#fff
    style PROMOTE fill:#2d8a4e,color:#fff
    style TRIVY fill:#f0a500,color:#fff
    style VAL fill:#f0a500,color:#fff
    style CI fill:#1a1a2e,color:#fff
    style ARTIFACT fill:#16213e,color:#fff
    style GITOPS fill:#0f3460,color:#fff
    style DEPLOY fill:#1a1a2e,color:#fff
    style VALIDATE fill:#16213e,color:#fff
```

**Key design principle:** The pipeline never applies infrastructure changes directly. It updates the manifest repo and stops. The system is designed to be compatible with GitOps agents like ArgoCD (not deployed in this project), which would pull and apply the desired state.

---

## Pipeline Flow

```mermaid
flowchart LR
    COMMIT([commit]) --> LINT[lint\nflake8]
    COMMIT --> TEST[test\npytest]

    LINT --> BUILD[build docker image\ngit SHA tag]
    TEST --> BUILD

    BUILD --> SCAN[trivy scan\nCRITICAL gate]
    SCAN -->|CVE found| BLOCKED([blocked])
    SCAN -->|clean| PUSH[push image\nDockerHub]

    PUSH --> S3[upload S3\ndeployment record]
    S3 --> MANIFEST[update manifest repo\nnew SHA]
    MANIFEST --> GREEN[deploy green\nEC2 port 8081]
    GREEN --> ALB[shift ALB traffic\n90% blue · 10% green]
    ALB --> VAL[validate\nretry + failure rate check]

    VAL -->|pass ✓| PROMOTE[promote green\ndecommission blue]
    VAL -->|fail ✗| RB1[ALB → 100% blue]
    VAL -->|fail ✗| RB2[git revert\nmanifest repo]

    style BLOCKED fill:#ff4d4d,color:#fff
    style PROMOTE fill:#2d8a4e,color:#fff
    style RB1 fill:#c0392b,color:#fff
    style RB2 fill:#c0392b,color:#fff
    style SCAN fill:#f0a500,color:#fff
    style VAL fill:#f0a500,color:#fff
```

---

## Design Decisions & Tradeoffs

### GitOps over direct `kubectl apply`
The pipeline commits image tag changes to a separate manifest repo rather than applying them directly to the cluster. This provides a complete Git audit trail of every deployment, enables rollback via `git revert`, and removes the need to expose cluster credentials to the pipeline. Tradeoff: adds operational complexity — a manifest repo and sync agent must be maintained.

### ALB over NGINX for traffic control
AWS ALB provides native target group weight management, built-in health checks, and CloudWatch metric integration without additional tooling. NGINX would require running and managing a reverse proxy layer. Tradeoff: ALB has per-hour cost; NGINX is free but adds operational burden.

### Canary (90/10) instead of full blue/green switch
Shifting 10% of traffic to Green first limits blast radius — if Green is broken, only 10% of users are affected during the validation window. Full blue/green switches 100% atomically, which is faster but riskier. Tradeoff: canary is slower to fully promote and requires a validation loop.

### Trivy CRITICAL-only failure threshold
Failing the pipeline on HIGH and above generates alert fatigue — teams start ignoring failures or adding `continue-on-error: true`, which defeats security scanning entirely. CRITICAL CVEs represent actively exploitable, high-impact vulnerabilities that must block deployment. HIGH and below are reported and tracked but don't block. Tradeoff: a HIGH vulnerability could reach production; mitigated by regular scheduled scans and SBOM tracking.

### Failure rate validation over single health check
A single `/health` endpoint returning 200 doesn't reflect real application health — it only proves the process is alive. Monitoring the failure rate of actual traffic requests during the canary window catches errors that a shallow health check misses. Tradeoff: requires a validation window (time cost) rather than instant promotion.

---

## Deployment Strategy

Blue/Green deployment runs on a single EC2 instance with two containers:

| Environment | Version      | Port | Traffic (initial) |
|-------------|--------------|------|-------------------|
| Blue        | Current      | 8080 | 90%               |
| Green       | New (canary) | 8081 | 10%               |

**Promotion flow:**
1. Green deployed and registered with Green target group
2. ALB listener rule updated: Blue 90 / Green 10
3. Validation loop runs — monitors failure rate over a time window
4. If healthy: ALB updated to Blue 0 / Green 100, Blue decommissioned
5. If unhealthy: automatic rollback triggered (see below)

**Why keep Blue running during canary?**
Instant rollback requires Blue to be live. Terminating Blue before Green is validated removes the safety net.

---

## Rollback Mechanism

### Trigger
- Failure rate ≥ configured threshold during canary validation window
- ALB health check: target marked unhealthy (3 consecutive failures × 30s interval = 90s detection window)

### Steps
1. ALB listener rule updated → 100% Blue, 0% Green
2. In-flight Green requests complete (connection draining: 30–60s)
3. `git revert` executed on manifest repo — explicit rollback commit with message referencing the failed SHA
4. Green container stopped and deregistered from target group
5. On-call notification triggered

### Why two rollback actions are required
The ALB switch is the **fast action** — stops user impact immediately. The manifest repo revert is the **state action** — ensures Git reflects reality and the next pipeline run doesn't re-deploy the broken image. Skipping the manifest revert leaves an incomplete audit trail and risks redeploying the broken version.

### Rollback type
Traffic rollback + State rollback (GitOps-consistent)

---

## Failure Injection Strategy

To validate rollback behavior, controlled failures were introduced:

- Application returning HTTP 500 on root endpoint
- ALB returning 502 when target becomes unhealthy

This ensures the system is tested under real runtime failure conditions rather than only build-time failures, validating both detection and recovery mechanisms.

---

## Failure Scenarios

| Scenario | Pipeline Stage | Error Message | Root Cause | Resolution |
|---|---|---|---|---|
| Wrong SSH key in secrets | deploy — git clone manifest repo | `Permission denied (publickey)` | Private key in secret doesn't match public deploy key registered in manifest repo | Replace `MANIFEST_REPO_SSH_KEY` secret with correct private key |
| Dockerfile syntax error | build — docker build | `unknown instruction: FORM` (or similar) | Typo in Dockerfile instruction | Fix Dockerfile syntax, repush |
| CRITICAL CVE introduced | scan — trivy | `exit code 1`, CVE list printed | Vulnerable package version in `requirements.txt` | Update or replace the vulnerable package |
| Runtime 500 errors post-deploy | post-deploy validation | Failure rate ≥ threshold | Application bug in new version not caught by unit tests | Automatic rollback triggers — fix bug, create new commit |
| ALB misconfiguration | post-deploy | `502 Bad Gateway` | Target group pointing to wrong port or unhealthy targets | Verify target group port config (8080/8081), check security group rules |

---

## Project Structure

```
secure-cicd-gitops-pipeline/
├── .github/
│   └── workflows/
│       └── pipeline.yml        # Full CI/CD pipeline definition
├── app/
│   ├── app.py                  # Flask application
│   └── requirements.txt        # Python dependencies
├── tests/
│   └── test_app.py             # Unit tests (pytest)
├── Dockerfile                  # Multi-stage build, non-root user
├── .dockerignore
└── README.md

# Separate manifest repo: secure-cicd-gitops-pipeline-manifests/
├── manifests/
│   ├── deployment.yml          # Image tag updated by pipeline on every deploy
│   └── service.yml
└── README.md
```

---

## Setup & Prerequisites

### GitHub Secrets Required

| Secret | Description |
|---|---|
| `DOCKER_USERNAME` | DockerHub username |
| `DOCKER_PASSWORD` | DockerHub password or access token |
| `AWS_ACCESS_KEY_ID` | AWS credentials for EC2/ALB/S3 access |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `AWS_REGION` | Target AWS region (e.g. `ap-south-1`) |
| `MANIFEST_REPO_SSH_KEY` | Private SSH key — public key registered as deploy key in manifest repo |
| `EC2_HOST` | Public IP or DNS of EC2 instance |
| `EC2_SSH_KEY` | Private key for SSH access to EC2 |

> **Known limitation on auth**: This project uses static AWS credentials for simplicity during initial build. Production improvement: replace `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` with OIDC identity federation — IAM role trust policy scoped to this specific repo and branch, no stored credentials. See Module 3 notes in `docs/`.

### AWS Infrastructure (Manual Provisioning)

1. **EC2 instance** — Ubuntu 22.04, Docker installed, ports 8080 and 8081 open in security group
2. **Application Load Balancer** — internet-facing, HTTP listener on port 80
3. **Two target groups:**
   - `blue-tg` → EC2 port 8080, health check path `/health`
   - `green-tg` → EC2 port 8081, health check path `/health`
4. **S3 bucket** — `veera-deployment-records` with folders: `deployments/`, `sboms/`
5. **CloudWatch alarm** — on `HTTPCode_Target_5XX_Count` metric from ALB, threshold ≥ 5 errors in 60s

---

## How to Run

1. Fork this repo and the manifest repo
2. Configure all GitHub Secrets listed above
3. Provision AWS infrastructure per prerequisites
4. Push any commit to `main`
5. Watch the pipeline in GitHub Actions:
   - Lint and test run in parallel
   - Build produces image tagged with git SHA
   - Trivy scans for CRITICAL CVEs — pipeline stops if found
   - Image pushed to DockerHub
   - Deployment record uploaded to S3
   - Manifest repo updated with new SHA
   - Green container deployed on EC2 port 8081
   - ALB shifts to 90/10 canary
   - Validation loop runs for configured window
   - Promotion or rollback executes automatically

---

## Demo

> 📹 Screen recording covers:
> - Successful deploy: commit → canary → promotion → Blue decommissioned
> - Failure injection: 500 errors introduced → validation detects → auto rollback to Blue → manifest repo reverted
> - Wrong SSH key: pipeline fails at deploy stage with `Permission denied (publickey)`

*(Link to be added after recording)*

---

## Known Limitations

- **Static AWS credentials** — uses access key/secret for simplicity. Should be replaced with OIDC federation in production (see Setup notes above)
- **No ArgoCD/Flux** — manifest repo pattern is implemented and ArgoCD-ready, but the cluster sync agent is not provisioned due to cost constraints. The pipeline correctly stops at manifest repo update; a GitOps agent would complete the loop
- **Single EC2 instance** — Blue and Green run on the same host. A real production setup would use separate instances or ECS tasks per target group
- **Single region** — no multi-region failover
- **Shallow health check** — `/health` endpoint returns 200 if the process is alive. A production health check would verify database connectivity and critical dependencies
- **Manual infra provisioning** — ALB, EC2, and target groups are set up manually. Next iteration will use Terraform

---

## Future Improvements

- Replace static AWS credentials with OIDC (IAM role + GitHub identity federation)
- Add Terraform module for full infra provisioning (EC2, ALB, target groups, S3, CloudWatch)
- Integrate ArgoCD for true pull-based GitOps cluster sync
- Add Prometheus + Grafana or CloudWatch dashboards for real-time observability
- Multi-stage canary rollout: 10% → 25% → 50% → 100% with validation at each step
- Retry and backoff logic in validation loop
- Slack / webhook alerting on rollback events
- Migrate to Kubernetes (EKS) — covered in next project
- Add cosign image signing for full supply chain verification
- SBOM generation and storage per build for CVE audit queries