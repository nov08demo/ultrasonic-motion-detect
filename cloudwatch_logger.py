import boto3
from botocore.exceptions import ClientError
import time
import os

class CloudwatchLogger:
    
    def __init__(self, log_group, stream_name, file_name, token=None):
        self.file_name = file_name
        self.client = boto3.client('logs')
        self.log_group = log_group
        self.stream_name = stream_name
        self.token = token
        if(not self.token):
            self.get_token()
    
    def get_token(self):
        # get current token in log stream
        self.token = self.client.describe_log_streams(
            logGroupName= self.log_group,
            logStreamNamePrefix= self.stream_name,
            orderBy='LogStreamName',
            descending=True,
        )['logStreams'][0]['uploadSequenceToken']
        
    
    def log(self, level, message):
        new_message = "[SUMMER-ULTRA][{}] {} ({}/{})".format(level.upper(), message, os.path.split(os.getcwd())[1], self.file_name)
        milli_time = int(round(time.time() * 1000))
        print(new_message)
        self.get_token()
        # put message inside the log stream using previous token
        try:
            response = self.client.put_log_events(
                logGroupName = self.log_group,
                logStreamName = self.stream_name,
                logEvents = [
                    {
                        'timestamp': int(milli_time),
                        'message': new_message
                    },
                ],
                sequenceToken = self.token
            )
        except ClientError as ex:
            self.log('error', 'Token Error getting another token')
            self.log(level, message)
        
    def key(self, message):
        self.log('key', message)
        
    def info(self, message):
        self.log('info', message)
        
    def error(self, message):
        self.log('error', message)
        
    def debug(self, message):
        self.log('debug', message)