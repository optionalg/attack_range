import sys
import re
import boto3



def get_instance_by_name(ec2_name, config):
    instances = get_all_instances(config)
    for instance in instances:
        str = instance['Tags'][0]['Value']
        if str == ec2_name:
            return instance

def get_single_instance_public_ip(ec2_name, config):
    instance = get_instance_by_name(ec2_name, config)
    return instance['NetworkInterfaces'][0]['Association']['PublicIp']


def get_all_instances(config):
    key_name = config['key_name']
    client = boto3.client('ec2')
    response = client.describe_instances(
        Filters=[
            {
                'Name': "key-name",
                'Values': [key_name]
            }
        ]
    )
    instances = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            if instance['State']['Name']!='terminated':
                str = instance['Tags'][0]['Value']
                if str.startswith('attack-range'):
                    instances.append(instance)

    return instances


def check_ec2_instance_state(ec2_name, state, config):
    instance = get_instance_by_name(ec2_name, config)

    if not instance:
        log.error(ec2_name + ' not found as AWS EC2 instance.')
        sys.exit(1)

    return (instance['State']['Name'] == state)


def change_ec2_state(instances, new_state, log):

    client = boto3.client('ec2')

    if len(instances) == 0:
        log.error(ec2_name + ' not found as AWS EC2 instance.')
        sys.exit(1)

    if new_state == 'stopped':
        for instance in instances:
            if instance['State']['Name'] == 'running':
                response = client.stop_instances(
                    InstanceIds=[instance['InstanceId']]
                )
                log.info('Successfully stopped instance with ID ' +
                      instance['InstanceId'] + ' .')

    elif new_state == 'running':
        for instance in instances:
            if instance['State']['Name'] == 'stopped':
                response = client.start_instances(
                    InstanceIds=[instance['InstanceId']]
                )
                log.info('Successfully started instance with ID ' + instance['InstanceId'] + ' .')


def deregister_images(images, config, log):
    client = boto3.client('ec2')

    for image in images:
        response = client.describe_images(
            Filters=[
                {
                    'Name': 'name',
                    'Values': [
                        str("packer-" + image + "-" + config['key_name']),
                    ]
                }
            ]
        )
        if len(response['Images']):
            image_obj = response['Images'][0]
            client.deregister_image(ImageId=image_obj['ImageId'])
            log.info('Successfully deregistered AMI ' +  image_obj['Name'] +  ' with AMI ID ' + image_obj['ImageId'] + ' .')
        else:
            log.info('Didn\'t find AMI: ' +  str("packer-" + image + "-" + config['key_name']) + ' .')
