import logging
import azure.functions as func
from azure.storage.blob import BlobClient, ContentSettings, BlobServiceClient, ContainerClient
from azure.cosmosdb.table.tableservice import TableService
import os
import datetime
from babel.dates import format_date
import uuid
import json
from operator import itemgetter
import time
import requests
from azure.cosmosdb.table.models import Entity



from jinja2 import Template



def main(req: func.HttpRequest, showMessageTemplateBlob: func.InputStream, messageTable: func.Out[str]) -> func.HttpResponse:

    logging.info('Python HTTP trigger function processed a request.')

    try:
        board_id = dict(req.form)["board_id"]
        sender = dict(req.form)["sender"]
        message_text = dict(req.form)["message_text"]
    except KeyError:
        return func.HttpResponse(f"Hello, please pass a board_id, sender and message_text in the request params.")

    # Take input text, write to storage table
    time_local_timezone = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    print_time = format_date(datetime.date.today(), format="EEEE", locale="de") + " " + time_local_timezone.strftime("%H:%M")
    new_message_dict = {"RowKey": str(uuid.uuid4()),
                    "PartitionKey": board_id,
                    "sender_name": sender,
                    "timestamp": print_time,
                    "message_text": message_text}

    table_service = TableService(account_name='adlsmessageboard', account_key=os.environ["blob_key"])
    table_service.insert_entity('messages', new_message_dict)


    logging.info("Message was set to output table.")

    requests.post(f"https://funcapp-messageboard.azurewebsites.net/api/azfunc_refreshBoard?board_id={board_id}")


    return func.HttpResponse("Board wurde geupdatet.")