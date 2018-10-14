"""Generating CloudFormation template."""
from ipaddress import ip_network

from ipify import get_ip

from troposphere.iam import (
    InstanceProfile,
    PolicyType as IAMPolicy,
    Role,
    Base64,
    ec2,
    GetAtt,
    Join,
    Output,
    Parameter,
    Ref,
    Template,
)

from awacs.aws import (
    Action,
    Allow,
    Policy,
    Principal,
    Statement,
)
from awacs.sts import AssumeRole


ApplicationName = "jenkins"
ApplicationPort = "8080"
GithubAccount = "EffectiveDevOpsWithAWS"
GithubAnsibleURL = "https://github.com/jaehlee3663/ansible".format(jaehlee3663)
AnsiblePullCmd = "/usr/local/ansible-pull -U https://github.com/jaehlee3663/ansible helloworld.yml -i localhost".format(GithubAnsibleURL, ApplicationName)

t = Template()

t.add_description("Effective DevOps in AWS: HelloWorld web application")

t.add_parameter(Parameter(
    "KeyPair",
    Description="Name of an existing EC2 KeyPair to SSH",
    Type="AWS::EC2::KeyPair::KeyName",
    ConstraintDescription="must be the name of an existing EC2 KeyPair.",
))

t.add_resource(ec2.SecurityGroup(
    "SecurityGroup",
    GroupDescription="Allow SSH and TCP/{} access".format(ApplicationPort),
    SecurityGroupIngress=[
        ec2.SecurityGroupRule(
            IpProtocol="tcp",
            FromPort="22",
            ToPort="22",
            CidrIp="0.0.0.0/0",
        ),
        ec2.SecurityGroupRule(
            IpProtocol="tcp",
            FromPort=ApplicationPort,
            ToPort=ApplicationPort,
            CidrIp="0.0.0.0/0",
        ),
    ],
))

ud = Base64(Join('\n', [
    "#!/bin/bash",
    "yum remove java-1.7.0-openjdk -y",
    "yum install java-1.8.0-openjdk -y",
    "yum install --enablerepo=epel -y git",
    "pip install ansible",
      AnsiblePullCmd,
      "echo '*/10 * * * * root {}' > /etc/cron.d/ansible-pull".format(AnsiblePullCmd)
]))

t.add_resource(Role(
    "Role",
    AssumeRolePolicyDocument=Policy(
      Statement=[
        Statement(
          Effect=Allow,
          Action=[AssumeRole],
          Principal=Principal("Service", ["ec2.amazonaws.com"])
        )
      ]
    )
))


t.add_resource(ec2.Instance(
    "instance",
    ImageId="ami-0a10b2721688ce9d2",
    InstanceType="t2.micro",
    SecurityGroups=[Ref("SecurityGroup")],
    KeyName=Ref("KeyPair"),
    UserData=ud,
))

t.add_output(Output(
    "InstancePublicIp",
    Description="Public IP of our instance.",
    Value=GetAtt("instance", "PublicIp"),
))

t.add_output(Output(
    "WebUrl",
    Description="Application endpoint",
    Value=Join("", [
        "http://", GetAtt("instance", "PublicDnsName"),
        ":", ApplicationPort
    ]),
))

print (t.to_json())
