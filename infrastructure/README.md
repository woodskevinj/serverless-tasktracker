# Task Tracker — Infrastructure

AWS CDK app (Python) that defines the cloud infrastructure for the Task Tracker application. Uses ECS with EC2 launch type to run the frontend and backend as Docker containers behind an Application Load Balancer.

## Tech Stack

- **IaC:** AWS CDK v2 (Python)
- **Language:** Python 3.8+
- **Testing:** pytest + aws_cdk.assertions

## Architecture

```
                         ┌─────────────────────────────────────────────────────┐
                         │  VPC (2 AZs, us-east-1)                            │
                         │                                                     │
Internet ──▶ ALB (:80)   │  ┌───────────────────────┐  ┌───────────────────┐  │
              │          │  │  Public Subnets         │  │  Private Subnets   │  │
              │          │  │                         │  │                   │  │
              ├─ /api/* ─┼──┤  ┌───────────────────┐  │  │  ┌─────────────┐  │  │
              │          │  │  │ ECS EC2 (t3.micro)│  │  │  │ RDS         │  │  │
              │          │  │  │ ASG (1 instance)  │  │  │  │ PostgreSQL  │  │  │
              │          │  │  │                   │  │  │  │ db.t3.micro │  │  │
              │          │  │  │ ┌───────────────┐ │──┼──┼─▶│ tasktracker │  │  │
              │          │  │  │ │ backend :3001 │ │  │  │  └─────────────┘  │  │
              │          │  │  │ └───────────────┘ │  │  │  Not publicly     │  │
              └─ /* ─────┼──┤  │ ┌───────────────┐ │  │  │  accessible       │  │
                         │  │  │ │ frontend :80  │ │  │  │                   │  │
                         │  │  │ └───────────────┘ │  │  │                   │  │
                         │  │  └───────────────────┘  │  │                   │  │
                         │  └───────────────────────┘  └───────────────────┘  │
                         └─────────────────────────────────────────────────────┘

ECR: tasktracker-frontend ──▶ frontend container (:80, nginx + React SPA)
ECR: tasktracker-backend  ──▶ backend container (:3001, Express.js)
```

## Resources

| Resource | Type | Details |
| --- | --- | --- |
| VPC | `AWS::EC2::VPC` | 2 AZs, public + private isolated subnets, no NAT gateways |
| ECR Repositories | `AWS::ECR::Repository` | `tasktracker-frontend` and `tasktracker-backend` |
| ECS Cluster | `AWS::ECS::Cluster` | EC2 launch type |
| Launch Template | `AWS::EC2::LaunchTemplate` | t3.micro, ECS-optimized AMI, IAM role for ECS |
| Auto Scaling Group | `AWS::AutoScaling::AutoScalingGroup` | Uses launch template, public subnet, capacity 1 |
| Task Definition | `AWS::ECS::TaskDefinition` | Host networking, 2 containers (frontend:80, backend:3001), placeholder images |
| ECS Service | `AWS::ECS::Service` | Desired count 1, min healthy 0%, implicit EC2 placement |
| ALB | `AWS::ElasticLoadBalancingV2::LoadBalancer` | Internet-facing, path-based routing |
| RDS Instance | `AWS::RDS::DBInstance` | db.t3.micro, PostgreSQL 16, private subnet, DB name `tasktracker` |
| ALB Security Group | `AWS::EC2::SecurityGroup` | Inbound: 80 (HTTP), 443 (HTTPS) from 0.0.0.0/0 |
| ECS Security Group | `AWS::EC2::SecurityGroup` | Inbound: 80, 3001 from ALB SG |
| RDS Security Group | `AWS::EC2::SecurityGroup` | Inbound: 5432 from ECS SG only |

## ALB Routing

| Path | Target | Port |
| --- | --- | --- |
| `/api/*` | Backend container | 3001 |
| `/*` (default) | Frontend container | 80 |

The task definition uses host networking — containers bind directly to the EC2 host's network. The frontend nginx config proxies `/api/` to `localhost:3001` since both containers share the host's network stack.

## Backend Environment Variables

The backend container receives RDS connection details at runtime:

| Variable | Source |
| --- | --- |
| `DB_HOST` | RDS endpoint address |
| `DB_PORT` | RDS endpoint port |
| `DB_NAME` | `tasktracker` (static) |
| `DB_USER` | Secrets Manager (auto-generated) |
| `DB_PASSWORD` | Secrets Manager (auto-generated) |
| `PORT` | `3001` (static) |

## Deployment Notes

**Placeholder images:** The task definition uses `nginx:alpine` (frontend) and `node:20-alpine` (backend) as placeholder images so the ECS service stabilizes on first deploy without needing images pushed to ECR. Update the task definition to use ECR images after pushing real builds.

**Memory:** Each container has a 128 MiB soft reservation and 256 MiB hard limit (512 MiB total max). A t3.micro has ~900 MiB available after OS/ECS agent overhead, so this fits comfortably.

**Single-instance deployment:** The service sets `min_healthy_percent=0` and `max_healthy_percent=100` so ECS can stop the old task before starting a new one on a single instance. This avoids host port conflicts during deployments.

**Cleanup ordering:** The capacity provider disables managed termination protection. The ECS service does not explicitly reference the capacity provider via `capacity_provider_strategies` — instead it relies on implicit EC2 placement through the cluster's registered capacity provider. This avoids a circular dependency during CloudFormation rollback/deletion where the capacity provider cannot be removed while the service still references it. EC2 instances register with the cluster via user data (`ECS_CLUSTER` written to `/etc/ecs/ecs.config`).

## Stack Outputs

| Output | Description |
| --- | --- |
| `AlbDnsName` | Application Load Balancer DNS name |
| `RdsEndpoint` | RDS PostgreSQL endpoint address |
| `RdsSecurityGroupId` | RDS security group ID |
| `FrontendEcrUri` | Frontend ECR repository URI |
| `BackendEcrUri` | Backend ECR repository URI |

## Project Structure

```
infrastructure/
├── app.py                      # CDK app entry point (us-east-1)
├── cdk.json                    # CDK configuration
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Test dependencies (pytest)
├── infrastructure/
│   ├── __init__.py
│   └── tasktracker_stack.py    # Main stack definition
└── tests/
    ├── __init__.py
    └── test_tasktracker_stack.py
```

## Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt
```

## Testing

```bash
source .venv/bin/activate
pytest -v
```

Runs 12 tests using `aws_cdk.assertions.Template`. No AWS account or credentials needed.

### Test Coverage

- VPC is created
- RDS instance type (`db.t3.micro`), engine (`postgres`), and database name (`tasktracker`)
- RDS is not publicly accessible
- RDS security group allows port 5432 from ECS security group
- ECR repositories created (`tasktracker-frontend`, `tasktracker-backend`)
- ECS cluster created
- ASG launch template uses `t3.micro`
- Task definition has 2 containers (frontend on port 80, backend on port 3001) with host networking, placeholder images, and memory limits
- ALB is internet-facing
- ECS service created
- ECS service deployment config: min healthy 0%, max 100%
- Stack outputs exist (ALB DNS, RDS endpoint, RDS SG ID, ECR URIs)

## Synthesize CloudFormation Template

```bash
source .venv/bin/activate
cdk synth
```

Generates the CloudFormation template in `cdk.out/`. Requires the AWS CDK CLI (`npm install -g aws-cdk`).

## Deployment (future)

Deployment is not part of this phase. When ready:

```bash
cdk deploy
```

This requires AWS credentials configured and the CDK CLI bootstrapped in the target account/region.
