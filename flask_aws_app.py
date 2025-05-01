
import boto3
import os
import subprocess

image_folder = '/home/ec2-user/face_images_1000/'
queue_url = 'https://sqs.us-east-1.amazonaws.com/590183783524/req-queue'
queue_resp_url = 'https://sqs.us-east-1.amazonaws.com/590183783524/resp-queue'
session = boto3.Session(region_name='us-east-1')
sqs_client = session.client('sqs')

def from_queue():
    while True:
        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,  
            WaitTimeSeconds=10,
            VisibilityTimeout=3,
            )

        if 'Messages' in response:
            message = response['Messages'][0]
            receipt_handle = message['ReceiptHandle']
            jpg = message['Body']
            path =os.path.join(image_folder, message['Body'])
            result = subprocess.run(["python3", "face_recognition.py", path], capture_output=True, text=True)
            sendBack = f"{jpg}:{result.stdout.strip()}"
            print(result.stdout)
            if result.stdout:
                response = sqs_client.send_message(
                    QueueUrl=queue_resp_url,
                    MessageBody=sendBack
                )
            print(message)
            sqs_client.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
                )
        else: 
            print('none')
        

if __name__ == '__main__':
    from_queue()
