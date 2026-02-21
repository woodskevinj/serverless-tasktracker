from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_ecr as ecr,
    aws_ecs as ecs,
    aws_autoscaling as autoscaling,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam,
)
from constructs import Construct


class TasktrackerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ---------------------------------------------------------------
        # VPC
        # ---------------------------------------------------------------
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

        # ---------------------------------------------------------------
        # ECR Repositories
        # ---------------------------------------------------------------
        frontend_repo = ecr.Repository(
            self,
            "FrontendRepo",
            repository_name="tasktracker-frontend",
            removal_policy=RemovalPolicy.DESTROY,
            empty_on_delete=True,
        )

        backend_repo = ecr.Repository(
            self,
            "BackendRepo",
            repository_name="tasktracker-backend",
            removal_policy=RemovalPolicy.DESTROY,
            empty_on_delete=True,
        )

        # ---------------------------------------------------------------
        # Security Groups
        # ---------------------------------------------------------------
        alb_sg = ec2.SecurityGroup(
            self,
            "AlbSecurityGroup",
            vpc=vpc,
            description="Allow HTTP and HTTPS to ALB",
            allow_all_outbound=True,
        )
        alb_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP"
        )
        alb_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(443), "Allow HTTPS"
        )

        ecs_sg = ec2.SecurityGroup(
            self,
            "EcsSecurityGroup",
            vpc=vpc,
            description="Allow traffic from ALB to ECS containers",
            allow_all_outbound=True,
        )
        ecs_sg.add_ingress_rule(
            alb_sg, ec2.Port.tcp(80), "Allow frontend from ALB"
        )
        ecs_sg.add_ingress_rule(
            alb_sg, ec2.Port.tcp(3001), "Allow backend from ALB"
        )

        rds_sg = ec2.SecurityGroup(
            self,
            "RdsSecurityGroup",
            vpc=vpc,
            description="Allow PostgreSQL access from ECS",
            allow_all_outbound=False,
        )
        rds_sg.add_ingress_rule(
            ecs_sg, ec2.Port.tcp(5432), "Allow PostgreSQL from ECS"
        )

        # ---------------------------------------------------------------
        # RDS PostgreSQL
        # ---------------------------------------------------------------
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

        # ---------------------------------------------------------------
        # ECS Cluster
        # ---------------------------------------------------------------
        cluster = ecs.Cluster(
            self,
            "TasktrackerCluster",
            vpc=vpc,
        )

        # ---------------------------------------------------------------
        # Auto Scaling Group for ECS EC2 instances
        # ---------------------------------------------------------------
        ecs_instance_role = iam.Role(
            self,
            "EcsInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonEC2ContainerServiceforEC2Role"
                ),
            ],
        )

        launch_template = ec2.LaunchTemplate(
            self,
            "EcsLaunchTemplate",
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3, ec2.InstanceSize.MICRO
            ),
            machine_image=ecs.EcsOptimizedImage.amazon_linux2023(),
            security_group=ecs_sg,
            role=ecs_instance_role,
            associate_public_ip_address=True,
            user_data=ec2.UserData.for_linux(),
        )

        asg = autoscaling.AutoScalingGroup(
            self,
            "EcsAsg",
            vpc=vpc,
            launch_template=launch_template,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            min_capacity=1,
            max_capacity=1,
            desired_capacity=1,
        )

        capacity_provider = ecs.AsgCapacityProvider(
            self,
            "AsgCapacityProvider",
            auto_scaling_group=asg,
        )
        cluster.add_asg_capacity_provider(capacity_provider)

        # ---------------------------------------------------------------
        # ECS Task Definition (2 containers, bridge networking)
        # ---------------------------------------------------------------
        task_definition = ecs.Ec2TaskDefinition(
            self,
            "TasktrackerTaskDef",
            network_mode=ecs.NetworkMode.BRIDGE,
        )

        # Frontend container — uses nginx placeholder until real image is pushed to ECR
        task_definition.add_container(
            "frontend",
            image=ecs.ContainerImage.from_registry("nginx:alpine"),
            memory_reservation_mib=128,
            memory_limit_mib=256,
            port_mappings=[
                ecs.PortMapping(container_port=80, host_port=80),
            ],
            logging=ecs.LogDrivers.aws_logs(stream_prefix="frontend"),
        )

        # Backend container — uses node placeholder until real image is pushed to ECR
        task_definition.add_container(
            "backend",
            image=ecs.ContainerImage.from_registry("node:20-alpine"),
            memory_reservation_mib=128,
            memory_limit_mib=256,
            port_mappings=[
                ecs.PortMapping(container_port=3001, host_port=3001),
            ],
            environment={
                "DB_HOST": db_instance.db_instance_endpoint_address,
                "DB_PORT": db_instance.db_instance_endpoint_port,
                "DB_NAME": "tasktracker",
                "PORT": "3001",
            },
            secrets={
                "DB_USER": ecs.Secret.from_secrets_manager(
                    db_instance.secret, field="username"
                ),
                "DB_PASSWORD": ecs.Secret.from_secrets_manager(
                    db_instance.secret, field="password"
                ),
            },
            logging=ecs.LogDrivers.aws_logs(stream_prefix="backend"),
        )

        # ---------------------------------------------------------------
        # Application Load Balancer
        # ---------------------------------------------------------------
        alb = elbv2.ApplicationLoadBalancer(
            self,
            "TasktrackerAlb",
            vpc=vpc,
            internet_facing=True,
            security_group=alb_sg,
        )

        listener = alb.add_listener(
            "HttpListener",
            port=80,
            open=False,
        )

        # ---------------------------------------------------------------
        # ECS Service
        # ---------------------------------------------------------------
        service = ecs.Ec2Service(
            self,
            "TasktrackerService",
            cluster=cluster,
            task_definition=task_definition,
            desired_count=1,
            capacity_provider_strategies=[
                ecs.CapacityProviderStrategy(
                    capacity_provider=capacity_provider.capacity_provider_name,
                    weight=1,
                ),
            ],
        )

        # Backend target group — /api/* routes
        backend_tg = listener.add_targets(
            "BackendTarget",
            port=3001,
            protocol=elbv2.ApplicationProtocol.HTTP,
            targets=[
                service.load_balancer_target(
                    container_name="backend",
                    container_port=3001,
                ),
            ],
            health_check=elbv2.HealthCheck(path="/api/projects"),
            conditions=[
                elbv2.ListenerCondition.path_patterns(["/api/*"]),
            ],
            priority=1,
        )

        # Frontend target group — default (everything else)
        frontend_tg = listener.add_targets(
            "FrontendTarget",
            port=80,
            targets=[
                service.load_balancer_target(
                    container_name="frontend",
                    container_port=80,
                ),
            ],
            health_check=elbv2.HealthCheck(path="/"),
        )

        # ---------------------------------------------------------------
        # Stack Outputs
        # ---------------------------------------------------------------
        CfnOutput(
            self,
            "AlbDnsName",
            value=alb.load_balancer_dns_name,
            description="Application Load Balancer DNS name",
        )
        CfnOutput(
            self,
            "RdsEndpoint",
            value=db_instance.db_instance_endpoint_address,
            description="RDS PostgreSQL endpoint",
        )
        CfnOutput(
            self,
            "RdsSecurityGroupId",
            value=rds_sg.security_group_id,
            description="RDS security group ID",
        )
        CfnOutput(
            self,
            "FrontendEcrUri",
            value=frontend_repo.repository_uri,
            description="Frontend ECR repository URI",
        )
        CfnOutput(
            self,
            "BackendEcrUri",
            value=backend_repo.repository_uri,
            description="Backend ECR repository URI",
        )
