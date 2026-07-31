#!/usr/bin/env bash
# AWS Infrastructure Provisioning Script for Agent WAF on AWS ECS Fargate
# Run this script with AWS CLI configured: aws configure

set -e

REGION="us-east-1"
CLUSTER_NAME="agent-waf-cluster"
VPC_NAME="agent-waf-vpc"
ALB_NAME="agent-waf-alb"
ECR_BACKEND="agent-waf-backend"
ECR_FRONTEND="agent-waf-frontend"

echo "=========================================================="
echo "  Provisioning Agent WAF AWS Infrastructure (${REGION})"
echo "=========================================================="

# 1. Create Amazon ECR Repositories
echo "[1/11] Creating ECR Repositories..."
aws ecr create-repository --repository-name ${ECR_BACKEND} --region ${REGION} || true
aws ecr create-repository --repository-name ${ECR_FRONTEND} --region ${REGION} || true

# 2. Create CloudWatch Log Groups
echo "[2/11] Creating CloudWatch Log Groups..."
aws logs create-log-group --log-group-name /ecs/agent-waf-backend --region ${REGION} || true
aws logs create-log-group --log-group-name /ecs/agent-waf-frontend --region ${REGION} || true

# 3. Create VPC, Internet Gateway, and Subnets
echo "[3/11] Creating Networking VPC & Subnets..."
VPC_ID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 --query 'Vpc.VpcId' --output text --region ${REGION})
aws ec2 create-tags --resources ${VPC_ID} --tags Key=Name,Value=${VPC_NAME} --region ${REGION}
aws ec2 modify-vpc-attribute --vpc-id ${VPC_ID} --enable-dns-hostnames '{"Value":true}' --region ${REGION}

IGW_ID=$(aws ec2 create-internet-gateway --query 'InternetGateway.InternetGatewayId' --output text --region ${REGION})
aws ec2 attach-internet-gateway --vpc-id ${VPC_ID} --internet-gateway-id ${IGW_ID} --region ${REGION}

SUBNET_1=$(aws ec2 create-subnet --vpc-id ${VPC_ID} --cidr-block 10.0.1.0/24 --availability-zone ${REGION}a --query 'Subnet.SubnetId' --output text --region ${REGION})
SUBNET_2=$(aws ec2 create-subnet --vpc-id ${VPC_ID} --cidr-block 10.0.2.0/24 --availability-zone ${REGION}b --query 'Subnet.SubnetId' --output text --region ${REGION})

aws ec2 modify-subnet-attribute --subnet-id ${SUBNET_1} --map-public-ip-on-launch --region ${REGION}
aws ec2 modify-subnet-attribute --subnet-id ${SUBNET_2} --map-public-ip-on-launch --region ${REGION}

ROUTE_TABLE_ID=$(aws ec2 create-route-table --vpc-id ${VPC_ID} --query 'RouteTable.RouteTableId' --output text --region ${REGION})
aws ec2 create-route --route-table-id ${ROUTE_TABLE_ID} --destination-cidr-block 0.0.0.0/0 --gateway-id ${IGW_ID} --region ${REGION}
aws ec2 associate-route-table --subnet-id ${SUBNET_1} --route-table-id ${ROUTE_TABLE_ID} --region ${REGION}
aws ec2 associate-route-table --subnet-id ${SUBNET_2} --route-table-id ${ROUTE_TABLE_ID} --region ${REGION}

# 4. Create Security Groups
echo "[4/11] Creating Security Groups..."
ALB_SG=$(aws ec2 create-security-group --group-name agent-waf-alb-sg --description "Security group for Agent WAF ALB" --vpc-id ${VPC_ID} --query 'GroupId' --output text --region ${REGION})
aws ec2 authorize-security-group-ingress --group-id ${ALB_SG} --protocol tcp --port 80 --cidr 0.0.0.0/0 --region ${REGION}
aws ec2 authorize-security-group-ingress --group-id ${ALB_SG} --protocol tcp --port 443 --cidr 0.0.0.0/0 --region ${REGION}

ECS_SG=$(aws ec2 create-security-group --group-name agent-waf-ecs-sg --description "Security group for Agent WAF ECS tasks" --vpc-id ${VPC_ID} --query 'GroupId' --output text --region ${REGION})
aws ec2 authorize-security-group-ingress --group-id ${ECS_SG} --protocol tcp --port 8000 --source-group ${ALB_SG} --region ${REGION}
aws ec2 authorize-security-group-ingress --group-id ${ECS_SG} --protocol tcp --port 80 --source-group ${ALB_SG} --region ${REGION}

# 5. Create AWS Cloud Map Private DNS Namespace (Service Discovery)
echo "[5/11] Creating Cloud Map Service Discovery Namespace..."
NAMESPACE_ID=$(aws servicediscovery create-private-dns-namespace --name agent-waf.local --vpc ${VPC_ID} --query 'OperationId' --output text --region ${REGION} || true)

# 6. Create Application Load Balancer, Target Groups, & Path Rules
echo "[6/11] Creating ALB & Target Groups..."
ALB_ARN=$(aws elbv2 create-load-balancer --name ${ALB_NAME} --subnets ${SUBNET_1} ${SUBNET_2} --security-groups ${ALB_SG} --query 'LoadBalancers[0].LoadBalancerArn' --output text --region ${REGION})

TG_BACKEND=$(aws elbv2 create-target-group --name agent-waf-backend-tg --protocol HTTP --port 8000 --vpc-id ${VPC_ID} --target-type ip --health-check-path /api/v1/health --health-check-interval-seconds 15 --query 'TargetGroups[0].TargetGroupArn' --output text --region ${REGION})
TG_FRONTEND=$(aws elbv2 create-target-group --name agent-waf-frontend-tg --protocol HTTP --port 80 --vpc-id ${VPC_ID} --target-type ip --health-check-path / --health-check-interval-seconds 15 --query 'TargetGroups[0].TargetGroupArn' --output text --region ${REGION})

# Default Listener: Forward /* to Frontend Target Group
LISTENER_ARN=$(aws elbv2 create-listener --load-balancer-arn ${ALB_ARN} --protocol HTTP --port 80 --default-actions Type=forward,TargetGroupArn=${TG_FRONTEND} --query 'Listeners[0].ListenerArn' --output text --region ${REGION})

# Rule 1 (Priority 10): Route /api/* to Backend Target Group
aws elbv2 create-rule \
  --listener-arn ${LISTENER_ARN} \
  --priority 10 \
  --conditions Field=path-pattern,Values='/api/*' \
  --actions Type=forward,TargetGroupArn=${TG_BACKEND} \
  --region ${REGION}

# Rule 2 (Priority 20): Route /ws/* to Backend Target Group (WebSocket support)
aws elbv2 create-rule \
  --listener-arn ${LISTENER_ARN} \
  --priority 20 \
  --conditions Field=path-pattern,Values='/ws/*' \
  --actions Type=forward,TargetGroupArn=${TG_BACKEND} \
  --region ${REGION}

# 7. IAM Task Execution Roles
echo "[7/11] Setting up IAM Task Execution Roles..."
aws iam create-role --role-name agent-waf-ecs-execution-role --assume-role-policy-document '{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}' || true

aws iam attach-role-policy --role-name agent-waf-ecs-execution-role --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy || true

aws iam create-role --role-name agent-waf-ecs-task-role --assume-role-policy-document '{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}' || true

# 8. Create ECS Cluster
echo "[8/11] Creating ECS Cluster..."
aws ecs create-cluster --cluster-name ${CLUSTER_NAME} --region ${REGION}

# 9. Register Task Definitions
echo "[9/11] Registering Task Definitions..."
aws ecs register-task-definition --cli-input-json file://aws/ecs-task-def-backend.json --region ${REGION}
aws ecs register-task-definition --cli-input-json file://aws/ecs-task-def-frontend.json --region ${REGION}

# 10. Create ECS Services
echo "[10/11] Creating ECS Services..."
aws ecs create-service \
  --cluster ${CLUSTER_NAME} \
  --service-name agent-waf-backend-service \
  --task-definition agent-waf-backend \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[${SUBNET_1},${SUBNET_2}],securityGroups=[${ECS_SG}],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=${TG_BACKEND},containerName=agent-waf-backend,containerPort=8000" \
  --region ${REGION}

aws ecs create-service \
  --cluster ${CLUSTER_NAME} \
  --service-name agent-waf-frontend-service \
  --task-definition agent-waf-frontend \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[${SUBNET_1},${SUBNET_2}],securityGroups=[${ECS_SG}],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=${TG_FRONTEND},containerName=agent-waf-frontend,containerPort=80" \
  --region ${REGION}

# 11. Configure ECS Service Auto Scaling
echo "[11/11] Configuring Auto Scaling Target (70% CPU Target Tracking)..."
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/${CLUSTER_NAME}/agent-waf-backend-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 1 \
  --max-capacity 3 \
  --region ${REGION}

aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/${CLUSTER_NAME}/agent-waf-backend-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name backend-cpu-target-70 \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleOutCooldown": 60,
    "ScaleInCooldown": 300
  }' \
  --region ${REGION}

echo "=========================================================="
echo "  Agent WAF Infrastructure Provisioned Successfully!"
echo "  ALB DNS Name: $(aws elbv2 describe-load-balancers --load-balancer-arns ${ALB_ARN} --query 'LoadBalancers[0].DNSName' --output text --region ${REGION})"
echo "=========================================================="
