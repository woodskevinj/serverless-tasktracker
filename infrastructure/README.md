# Task Tracker — Infrastructure

AWS CDK app (Python) that defines the cloud infrastructure for the Task Tracker application.

## Tech Stack

- **IaC:** AWS CDK v2 (Python)
- **Language:** Python 3.8+
- **Testing:** pytest + aws_cdk.assertions

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  VPC (2 AZs, us-east-1)                                │
│                                                         │
│  ┌──────────────────┐       ┌────────────────────────┐  │
│  │  Public Subnets   │       │  Private Subnets        │  │
│  │                  │       │                        │  │
│  │  ┌────────────┐  │       │  ┌──────────────────┐  │  │
│  │  │ EC2        │  │ :5432 │  │ RDS PostgreSQL   │  │  │
│  │  │ t3.micro   │──┼───────┼─▶│ db.t3.micro      │  │  │
│  │  │            │  │       │  │ DB: tasktracker   │  │  │
│  │  └────────────┘  │       │  └──────────────────┘  │  │
│  │   :22 :80 :443   │       │   Not publicly          │  │
│  │   from 0.0.0.0/0 │       │   accessible             │  │
│  └──────────────────┘       └────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Resources

| Resource | Type | Details |
| --- | --- | --- |
| VPC | `AWS::EC2::VPC` | 2 AZs, public + private isolated subnets, no NAT gateways |
| EC2 Instance | `AWS::EC2::Instance` | t3.micro, Amazon Linux 2023, public subnet |
| RDS Instance | `AWS::RDS::DBInstance` | db.t3.micro, PostgreSQL 16, private subnet, DB name `tasktracker` |
| EC2 Security Group | `AWS::EC2::SecurityGroup` | Inbound: 22 (SSH), 80 (HTTP), 443 (HTTPS) from 0.0.0.0/0 |
| RDS Security Group | `AWS::EC2::SecurityGroup` | Inbound: 5432 from EC2 security group only |

## Stack Outputs

| Output | Description |
| --- | --- |
| `RdsEndpoint` | RDS PostgreSQL endpoint address |
| `Ec2PublicIp` | EC2 instance public IP |
| `RdsSecurityGroupId` | RDS security group ID |

## Project Structure

```
infrastructure/
├── app.py                      # CDK app entry point
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

Runs 7 tests using `aws_cdk.assertions.Template`. No AWS account or credentials needed.

### Test Coverage

- VPC is created
- RDS instance type (`db.t3.micro`), engine (`postgres`), and database name (`tasktracker`)
- RDS is not publicly accessible
- EC2 instance type (`t3.micro`)
- RDS security group allows port 5432 from EC2 security group
- EC2 security group allows ports 22, 80, 443 from 0.0.0.0/0
- Stack outputs exist for RDS endpoint, EC2 public IP, and RDS security group ID

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
