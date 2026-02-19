import aws_cdk as cdk
from aws_cdk import assertions
from infrastructure.tasktracker_stack import TasktrackerStack


def get_template():
    app = cdk.App()
    stack = TasktrackerStack(app, "TestStack", env=cdk.Environment(region="us-east-1"))
    return assertions.Template.from_stack(stack)


def test_vpc_created():
    template = get_template()
    template.resource_count_is("AWS::EC2::VPC", 1)


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


def test_ec2_instance_type():
    template = get_template()
    template.has_resource_properties(
        "AWS::EC2::Instance",
        {
            "InstanceType": "t3.micro",
        },
    )


def test_rds_security_group_allows_postgres_from_ec2_sg():
    template = get_template()
    template.has_resource_properties(
        "AWS::EC2::SecurityGroup",
        {
            "GroupDescription": "Allow PostgreSQL access from EC2",
            "SecurityGroupIngress": assertions.Match.absent(),
        },
    )
    # The ingress rule is created as a separate resource by CDK
    template.has_resource_properties(
        "AWS::EC2::SecurityGroupIngress",
        {
            "IpProtocol": "tcp",
            "FromPort": 5432,
            "ToPort": 5432,
        },
    )


def test_ec2_security_group_allows_ssh_http_https():
    template = get_template()
    template.has_resource_properties(
        "AWS::EC2::SecurityGroup",
        {
            "GroupDescription": "Allow SSH, HTTP, and HTTPS access to EC2",
            "SecurityGroupIngress": [
                {
                    "CidrIp": "0.0.0.0/0",
                    "FromPort": 22,
                    "IpProtocol": "tcp",
                    "ToPort": 22,
                },
                {
                    "CidrIp": "0.0.0.0/0",
                    "FromPort": 80,
                    "IpProtocol": "tcp",
                    "ToPort": 80,
                },
                {
                    "CidrIp": "0.0.0.0/0",
                    "FromPort": 443,
                    "IpProtocol": "tcp",
                    "ToPort": 443,
                },
            ],
        },
    )


def test_outputs_exist():
    template = get_template()
    outputs = template.to_json()["Outputs"]
    output_keys = list(outputs.keys())

    assert any("RdsEndpoint" in k for k in output_keys), "Missing RdsEndpoint output"
    assert any("Ec2PublicIp" in k for k in output_keys), "Missing Ec2PublicIp output"
    assert any("RdsSecurityGroupId" in k for k in output_keys), "Missing RdsSecurityGroupId output"
