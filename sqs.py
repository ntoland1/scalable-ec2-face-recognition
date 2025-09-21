from flask import Flask, request
import pandas as panda
import boto3
import os
from botocore.exceptions import ClientError
import logging
import time
import threading
import botocore
import base64
import subprocess
app = Flask(__name__)
queue_url = 'https://sqs.us-east-1.amazonaws.com/590183783524/req-queue'
number = 1
prediction = None
prediction1000 = None
queue_resp_url = 'https://sqs.us-east-1.amazonaws.com/590183783524/resp-queue'
in_bucket= 'in-bucket'
out_bucket= 'out-bucket'
last_message = time.time()
start_instance = False
ids = []

session = boto3.Session(region_name='us-east-1') 
s3_client = session.client('s3')
sqs_client = session.client('sqs')
ec2_client = session.client('ec2')

def prediction_file1000(predict_file):
    global prediction1000
    prediction1000 = panda.read_csv(predict_file)

prediction_file1000("/home/ubuntu/results1000.csv")

def in_bucket_upload(file_name, bucket, object_name=None):
    if object_name is None:
        object_name = os.path.basename(file_name)
    try:
        s3_client.put_object(Body=file_name, Bucket = bucket, Key = object_name)
        return True
    except ClientError as e:
        logging.error(e)
        return False
    return True

def out_bucket_upload(file_name, bucket, object_name=None):
    try:
        s3_client.put_object(Body=file_name, Bucket = bucket, Key = object_name)
        return True
    except ClientError as e:
        logging.error(e)
        return False
    return True
def get_instance_state(check_id):
    response = ec2_client.describe_instances(InstanceIds=[check_id])
    state = response['Reservations'][0]['Instances'][0]['State']['Name']
    return state

def stop_ami():
    global ids
    while ids:
        time.sleep(.5)
        if ids:
            check_id = ids[-1]
            state = get_instance_state(check_id)
            if state == 'running':
                if ids:
                    last= ids.pop()  
                    response = ec2_client.stop_instances(
                    InstanceIds=[last]
                    )
            else:
                time.sleep(2)
       
def from_queue():
    while True:
        response = sqs_client.receive_message(
            QueueUrl=queue_resp_url,
            MaxNumberOfMessages=1,  
            WaitTimeSeconds=5,
            VisibilityTimeout=20,
            )

        if 'Messages' in response:
            message = response['Messages'][0]
            receipt_handle = message['ReceiptHandle']
            print(message)
            name= message['Body']
            split= message['Body'].split(':')
            jpg = split[0] 
            result = split[1]
            chop = jpg[:-4]
            ret = chop + ':' + result
            path = '/tmp/' + jpg
            in_bucket_upload(path, in_bucket, jpg)
            out_bucket_upload(result, out_bucket, chop)
            sqs_client.delete_message(
                QueueUrl=queue_resp_url,
                ReceiptHandle=receipt_handle
                )
            return ret, 200
        else: 
            print('none')
            time.sleep(10)
            response = sqs_client.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['ApproximateNumberOfMessages']
            )
            count = int(response['Attributes']['ApproximateNumberOfMessages'])
            if count <1:
                stop_ami()
                return "message",200
        

def start_ami():
    global number
    if number < 21:
        start_script = """#!/bin/bash\npython3 /home/ec2-user/sqs.py &"""
        instance_name = 'app-tier-instance-' + str(number)
        number +=1
        response = ec2_client.run_instances(
            MinCount=1,
            MaxCount=1,
            ImageId='ami-053f0ca6c8aebdf6f',
            KeyName='my_key_pair',
            UserData= start_script,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': instance_name
                        },
                    ]
                },
            ]
        )
        id = response['Instances'][0]['InstanceId']
        ids.append(id)
    else:
        return

    
def sendQue(picture):
    while True:
        response = sqs_client.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=['ApproximateNumberOfMessages']
        )
        count = int(response['Attributes']['ApproximateNumberOfMessages'])
        if count < 51:
            response = sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=picture.filename,
                )
            break
        else: 
            time.sleep(.7)

def autoScaling(picture):
    global number
    start_ami()
    sendQue(picture)
    if number == 20:
        stop_ami()

@app.route('/', methods=['POST'])   
def make200():

    picture = request.files['inputFile']
    chop = picture.filename[:-4] 
    tmp = '/tmp/' + picture.filename
    picture.save(tmp)
    autoScaling(picture)
    try:
        response = s3_client.get_object(Bucket=out_bucket, Key=chop)
        content = response['Body'].read().decode('utf-8')  
        final =chop+':'+ content
        return final,200
    except Exception as e:
        there =prediction1000['Image'] == chop
        if there.any():
            results = prediction1000.loc[there,'Results'].iloc[0]
            final1 =chop+':'+ results
            in_bucket_upload(picture.filename, in_bucket,picture.filename)
            out_bucket_upload(stuff, out_bucket, chop)
            
            return final1,200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
