# Scalable EC2 Face Recognition

A cloud-based, auto-scaling face recognition system built on AWS EC2, utilizing SQS queues for distributed processing.

## Overview

This project implements a scalable face recognition service that automatically adjusts capacity based on demand. The system uses a Flask web application as the front-end, Amazon SQS for task distribution, S3 buckets for storage, and EC2 instances that scale up or down depending on the processing queue length.

## Architecture

The system consists of three main components:

1. **Web Application (`sqs.py`)**: A Flask web server that:
   - Receives image uploads from users
   - Queues processing requests in SQS
   - Manages EC2 instance scaling
   - Returns face recognition results

2. **Worker Application (`flask_aws_app.py`)**: Runs on EC2 instances and:
   - Pulls image processing requests from the SQS queue
   - Processes images using face recognition
   - Sends results back via a response queue

3. **Face Recognition Engine (`face_recognition.py`)**: Performs the actual face detection and matching using:
   - MTCNN for face detection
   - FaceNet (InceptionResnetV1) for face embedding generation
   - Distance-based matching against stored face embeddings

## Auto-Scaling Logic

The system automatically scales EC2 instances based on the SQS queue length:
- Spins up new instances when the request queue grows
- Shuts down instances when demand decreases
- Implements a maximum of 20 EC2 instances to control costs

## Key Technologies

- **AWS Services**: EC2, SQS, S3
- **Machine Learning**: FaceNet, MTCNN
- **Web Framework**: Flask
- **Programming Language**: Python

## Setup and Deployment

1. Configure AWS credentials
2. Set up SQS queues: `req-queue` and `resp-queue`
3. Create S3 buckets: `in-bucket` and `out-bucket`
4. Deploy the Flask application
5. Prepare the EC2 AMI with face recognition dependencies
6. Test with sample images
