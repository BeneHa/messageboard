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



from jinja2 import Template


def main(req: func.HttpRequest, showMessageTemplateBlob: func.InputStream) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    board_id = req.params["board_id"]

    # Check if board_id already exists
    connection_str = os.environ["blobConnectionString"]
    blob_service_client = BlobServiceClient.from_connection_string(connection_str)

    container_name = "$web"
    container_client = blob_service_client.get_container_client(container_name)

    blob_list = container_client.list_blobs(name_starts_with="live_webpages/")
    existing_boards_list = list(set([b["name"].split("/")[1] for b in blob_list]))

    if board_id not in existing_boards_list:
        return func.HttpResponse("Dieses Board existiert nicht.")

    logging.info("Board name is valid.")


    # Read all contents for this board from storage
    table_service = TableService(account_name="adlsmessageboard", account_key=os.environ["blob_key"])
    min_datetime_for_messages = (datetime.datetime.utcnow() - datetime.timedelta(hours = 24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    messages_today = table_service.query_entities("messages",
                                                filter=f"PartitionKey eq '{board_id}' and Timestamp gt datetime'{min_datetime_for_messages}'",
                                                select="sender_name, timestamp, message_text")
    message_list = [m for m in messages_today]
    for m in message_list:
        m.pop("etag")

    message_texts = [d["message_text"] for d in message_list]
    message_senders = [d["sender_name"] for d in message_list]
    message_timestamps = [d["timestamp"] for d in message_list]


    message_list_unique = []
    distinct_message_texts = list(set(message_texts))
    for t in distinct_message_texts:
        messages_this_sender = [d for d  in message_list if d["message_text"] == t]
        text_sender = max([d["sender_name"] for d in messages_this_sender])
        text_timestamp = max([d["timestamp"] for d in messages_this_sender])
        message_list_unique.append({"message_text": t, "sender_name": text_sender, "timestamp": text_timestamp})


    
    message_list = sorted(message_list_unique, key=itemgetter("timestamp"))

    #Read images from storage
    connection_str = os.environ["blobConnectionString"]
    blob_service_client = BlobServiceClient.from_connection_string(connection_str)

    container_name = "$web"
    container_client = blob_service_client.get_container_client(container_name)

    blob_list = container_client.list_blobs(name_starts_with=f"images/{board_id}/")
    existing_images = sorted([b["name"] for b in blob_list], reverse=True)

    num_images = min(len(existing_images), 3)
    images_to_show = existing_images[0 : num_images + 1]
    images_full_paths = [f"https://adlsmessageboard.z1.web.core.windows.net/" + f  for f in images_to_show]
    image_items = [{"image_path": p} for p in images_full_paths]

    # Render template
    show_string_raw = str(showMessageTemplateBlob.read())

    for x in ["\\n", "\\r", "b'"]:
        show_string_raw = show_string_raw.replace(x, "")

    show_template = Template(show_string_raw)
    rendered_show_template = show_template.render(board_id = board_id, content_items = message_list, image_items = image_items)

    logging.info('Template was processed.')


    #Write finished webpage to BLOB
    blob_client_show = BlobClient(account_url="https://adlsmessageboard.blob.core.windows.net", container_name="$web", blob_name=f"live_webpages/{board_id}/show_messages.html",
                        credential=os.environ["blob_key"])

    logging.info('BLOB client was created.')


    blob_client_show.upload_blob(rendered_show_template, blob_type="BlockBlob", overwrite=True, content_settings=ContentSettings(content_type="text/html; charset=utf-8"))


    return func.HttpResponse("Board wurde geupdatet.")