from collections import defaultdict
import zlib
import base64
import json
import boto3
import logging
import pyjq

logger = logging.getLogger()
logger.setLevel(logging.INFO)

lambda_client = boto3.client('lambda')

ROUTES = {
    'glow-sync-event-metrics-adaptor': 'select(.ident | test("dabapps-firefly-glow-.*worker"))',
}

def decode_event(event):
    return base64.b64decode(event['awslogs']['data'])

def decompress_event_data(compressed_event_data):
    return zlib.decompress(compressed_event_data, 31)

def deserialize_event_data(event_data):
    return json.loads(event_data)

def unpack_event(event):
    zipped_data = decode_event(event)
    serialized_data = decompress_event_data(zipped_data)
    return deserialize_event_data(serialized_data)

def lambda_handler(event, context):
    event_data = unpack_event(event)
    if event_data['messageType'] != 'DATA_MESSAGE':
        return

    log_group = event_data['logGroup']
    log_events = event_data['logEvents']
    for event in log_events:
        event['logGroup'] = log_group
    for log_filter, sub_handler in ROUTES.items():
        for event in pyjq.all(log_filter, log_events):
            route(sub_handler, event)
        
def route(handler, event):
    lambda_client.invoke(
        FunctionName=route,
        InvocationType='Event',
        Payload=json.dumps(event),
    )

def matches(log_filter, event):
   return True

