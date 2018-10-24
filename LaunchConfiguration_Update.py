#!/usr/bin/python3.4

import time
import sys
import csv
import boto3
from boto3.session import Session

#Read arguments
stackfile = sys.argv[3]
webami = sys.argv[1]
cmsami = sys.argv[2]
accesskey = sys.argv[4]
secretkey = sys.argv[5]

#Read file for stacknames
stack_list = []
with open('stackfile') as file:
                reader = csv.reader(file, delimiter='\n')
                for row in reader:
                                stack_list.append(row[0])

#stack_list=['Stack-1', 'Stack-2']

session = Session(aws_access_key_id=accesskey,aws_secret_access_key=secretkey,region_name='us-west-2')
cf = session.client('cloudformation')
asg = session.client('autoscaling')

for stackname in stack_list:
                # stackdetails = {}
                # stackdetails = { stackname : {} }
                cms_asg = None
                web_asg = None
                cms_lc = None
                web_lc = None
                cf_details = cf.list_stack_resources(StackName = stackname)['StackResourceSummaries']
                for resources in cf_details:
                                if 'AWS::AutoScaling::AutoScalingGroup' in resources['ResourceType']:
                                                if "cms" in resources['PhysicalResourceId'].lower():
                                                                cms_asg = resources['PhysicalResourceId']
                                                                # stackdetails[stackname]['cms_asg'] = resources['PhysicalResourceId']
                                                elif "web" in resources['PhysicalResourceId'].lower():
                                                                web_asg = resources['PhysicalResourceId']
                                                                # stackdetails[stackname]['web_asg'] = resources['PhysicalResourceId']
                                elif 'AWS::AutoScaling::LaunchConfiguration' in resources['ResourceType']:
                                                if 'web' in resources['PhysicalResourceId'].lower():
                                                                web_lc = resources['PhysicalResourceId']
                                                                # stackdetails[stackname]['weblc'] = resources['PhysicalResourceId']
                                                elif 'cms' in resources['PhysicalResourceId'].lower():
                                                                cms_lc = resources['PhysicalResourceId']
                                                                # stackdetails[stackname]['cmslc'] = resources['PhysicalResourceId']
                if not web_lc:
                                web_asg_details = asg.describe_auto_scaling_groups(AutoScalingGroupNames=[web_asg])['AutoScalingGroups']
                                for asgs in web_asg_details:
                                                web_lc = asgs['LaunchConfigurationName']
                                                for inst in asgs['Instances']:
                                                                web_instid = inst['InstanceId']
                                                                break
                if not cms_lc:
                                cms_asg_details = asg.describe_auto_scaling_groups(AutoScalingGroupNames=[cms_asg])['AutoScalingGroups']
                                for asgs in cms_asg_details:
                                                cms_lc = asgs['LaunchConfigurationName']
                                                for inst in asgs['Instances']:
                                                                cms_instid = inst['InstanceId']
                                                                break
                timestr = time.strftime("%b%Y")
                new_web_lc = asg.create_launch_configuration( InstanceId = web_instid, ImageId=webami, LaunchConfigurationName = web_lc + '_updated_%s' % timestr)
                new_cms_lc = asg.create_launch_configuration( InstanceId = cms_instid, ImageId=cmsami, LaunchConfigurationName = cms_lc + '_updated_%s' % timestr)
                response = asg.update_auto_scaling_group(AutoScalingGroupName=web_asg,LaunchConfigurationName=new_web_lc)
                if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                                print("LC %s Update failed on %s ASG" % (new_web_lc, web_asg))
                response = asg.update_auto_scaling_group(AutoScalingGroupName=cms_asg,LaunchConfigurationName=new_cms_lc)
                if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                                print("LC %s Update failed on %s ASG" % (new_cms_lc, cms_asg))
