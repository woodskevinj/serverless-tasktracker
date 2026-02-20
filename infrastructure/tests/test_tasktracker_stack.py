import aws_cdk as cdk
from aws_cdk import assertions
from infrastructure.tasktracker_stack import TasktrackerStack


def get_template():
    app = cdk.App()
    stack = TasktrackerStack(app, "TestStack", env=cdk.Environment(region="us-east-1"))
    return assertions.Template.from_stack(stack)


# ---------------------------------------------------------------
# VPC
# ---------------------------------------------------------------
def test_vpc_created():
    template = get_template()
    template.resource_count_is("AWS::EC2::VPC", 1)


# ---------------------------------------------------------------
# RDS
# ---------------------------------------------------------------
def test_rds_instance_type_and_engine():
    template = get_template()
    template.has_resource_properties(
        "AWS::RDS::DBInstance",
        {
            "DBInstanceClass": "db.t3.micro",
            "Engine": "postgres",
            "DBName": "tasktracker",
        },
    )


def test_rds_not_publicly_accessible():
    template = get_template()
    template.has_resource_properties(
        "AWS::RDS::DBInstance",
        {
            "PubliclyAccessible": False,
        },
    )


def test_rds_security_group_allows_postgres_from_ecs():
    template = get_template()
    template.has_resource_properties(
        "AWS::EC2::SecurityGroup",
        {
            "GroupDescription": "Allow PostgreSQL access from ECS",
            "SecurityGroupIngress": assertions.Match.absent(),
        },
    )
    template.has_resource_properties(
        "AWS::EC2::SecurityGroupIngress",
        {
            "IpProtocol": "tcp",
            "FromPort": 5432,
            "ToPort": 5432,
        },
    )


# ---------------------------------------------------------------
# ECR
# ---------------------------------------------------------------
def test_ecr_repositories_created():
    template = get_template()
    template.has_resource_properties(
        "AWS::ECR::Repository",
        {"RepositoryName": "tasktracker-frontend"},
    )
    template.has_resource_properties(
        "AWS::ECR::Repository",
        {"RepositoryName": "tasktracker-backend"},
    )


# ---------------------------------------------------------------
# ECS Cluster
# ---------------------------------------------------------------
def test_ecs_cluster_created():
    template = get_template()
    template.resource_count_is("AWS::ECS::Cluster", 1)


# ---------------------------------------------------------------
# ASG
# ---------------------------------------------------------------
def test_asg_launch_template_instance_type():
    template = get_template()
    template.has_resource_properties(
        "AWS::EC2::LaunchTemplate",
        {
            "LaunchTemplateData": assertions.Match.object_like(
                {"InstanceType": "t3.micro"}
            ),
        },
    )


# ---------------------------------------------------------------
# ECS Task Definition
# ---------------------------------------------------------------
def test_ecs_task_definition_has_two_containers():
    template = get_template()
    template.has_resource_properties(
        "AWS::ECS::TaskDefinition",
        {
            "NetworkMode": "bridge",
            "ContainerDefinitions": assertions.Match.array_with(
                [
                    assertions.Match.object_like(
                        {
                            "Name": "frontend",
                            "PortMappings": [
                                {"ContainerPort": 80, "HostPort": 80},
                            ],
                        }
                    ),
                    assertions.Match.object_like(
                        {
                            "Name": "backend",
                            "PortMappings": [
                                {"ContainerPort": 3001, "HostPort": 3001},
                            ],
                        }
                    ),
                ]
            ),
        },
    )


# ---------------------------------------------------------------
# ALB
# ---------------------------------------------------------------
def test_alb_created():
    template = get_template()
    template.has_resource_properties(
        "AWS::ElasticLoadBalancingV2::LoadBalancer",
        {
            "Scheme": "internet-facing",
        },
    )


# ---------------------------------------------------------------
# ECS Service
# ---------------------------------------------------------------
def test_ecs_service_created():
    template = get_template()
    template.resource_count_is("AWS::ECS::Service", 1)


# ---------------------------------------------------------------
# Stack Outputs
# ---------------------------------------------------------------
def test_outputs_exist():
    template = get_template()
    outputs = template.to_json()["Outputs"]
    output_keys = list(outputs.keys())

    assert any("AlbDnsName" in k for k in output_keys), "Missing AlbDnsName output"
    assert any("RdsEndpoint" in k for k in output_keys), "Missing RdsEndpoint output"
    assert any("RdsSecurityGroupId" in k for k in output_keys), "Missing RdsSecurityGroupId output"
    assert any("FrontendEcrUri" in k for k in output_keys), "Missing FrontendEcrUri output"
    assert any("BackendEcrUri" in k for k in output_keys), "Missing BackendEcrUri output"
