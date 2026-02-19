from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    aws_ec2 as ec2,
    aws_rds as rds,
)
from constructs import Construct


class TasktrackerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC with public and private subnets across 2 AZs
        vpc = ec2.Vpc(
            self,
            "TasktrackerVpc",
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
        )

        # Security group for EC2 — allow inbound SSH, HTTP, HTTPS
        ec2_sg = ec2.SecurityGroup(
            self,
            "Ec2SecurityGroup",
            vpc=vpc,
            description="Allow SSH, HTTP, and HTTPS access to EC2",
            allow_all_outbound=True,
        )
        ec2_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "Allow SSH"
        )
        ec2_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP"
        )
        ec2_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(443), "Allow HTTPS"
        )

        # Security group for RDS — allow inbound on 5432 from EC2 only
        rds_sg = ec2.SecurityGroup(
            self,
            "RdsSecurityGroup",
            vpc=vpc,
            description="Allow PostgreSQL access from EC2",
            allow_all_outbound=False,
        )
        rds_sg.add_ingress_rule(
            ec2_sg, ec2.Port.tcp(5432), "Allow PostgreSQL from EC2"
        )

        # RDS PostgreSQL instance in private subnet
        db_instance = rds.DatabaseInstance(
            self,
            "TasktrackerDb",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_16,
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3, ec2.InstanceSize.MICRO
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            security_groups=[rds_sg],
            database_name="tasktracker",
            publicly_accessible=False,
            removal_policy=RemovalPolicy.DESTROY,
            deletion_protection=False,
        )

        # EC2 instance in public subnet
        ec2_instance = ec2.Instance(
            self,
            "TasktrackerEc2",
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3, ec2.InstanceSize.MICRO
            ),
            machine_image=ec2.MachineImage.latest_amazon_linux2023(),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            security_group=ec2_sg,
        )

        # Stack outputs
        CfnOutput(
            self,
            "RdsEndpoint",
            value=db_instance.db_instance_endpoint_address,
            description="RDS PostgreSQL endpoint",
        )
        CfnOutput(
            self,
            "Ec2PublicIp",
            value=ec2_instance.instance_public_ip,
            description="EC2 instance public IP",
        )
        CfnOutput(
            self,
            "RdsSecurityGroupId",
            value=rds_sg.security_group_id,
            description="RDS security group ID",
        )
