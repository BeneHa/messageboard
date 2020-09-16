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



def main(req: func.HttpRequest, showMessageTemplateBlob: func.InputStream, messageTable: func.Out[str]) -> func.HttpResponse:

    logging.info('Python HTTP trigger function processed a request.')

    board_id = dict(req.form)["board_id"]
    sender = dict(req.form)["sender"]
    message_text = dict(req.form)["message_text"]

    if not (board_id and sender and message_text):
        return func.HttpResponse(f"Hello, please pass a board_id, sender and message_text in the request params.")


    # Take input text, write to storage table
    time_local_timezone = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    print_time = format_date(datetime.date.today(), format="EEEE", locale="de") + " " + time_local_timezone.strftime("%H:%M")
    new_message_dict = {"rowKey": str(uuid.uuid4()),
                    "partitionKey": board_id,
                    "sender_name": sender,
                    "timestamp": print_time,
                    "message_text": message_text}
    messageTable.set(json.dumps(new_message_dict))

    # Read all contents for this board from storage
    table_service = TableService(account_name="adlsmessageboard", account_key=os.environ["blob_key"])
    min_datetime_for_messages = (datetime.datetime.utcnow() - datetime.timedelta(hours = 24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    messages_today = table_service.query_entities("messages",
                                                filter=f"PartitionKey eq '{board_id}' and Timestamp gt datetime'{min_datetime_for_messages}'",
                                                select="sender_name, timestamp, message_text")
    message_list = [m for m in messages_today]
    for m in message_list:
        m.pop("etag")
    message_list = sorted(message_list, key=itemgetter("timestamp"))

    #Add the current item to the message list because it will only be written to the table when this function completed running
    message_list.append({"sender_name": sender, "timestamp": print_time, "message_text": message_text})

    #Read images from storage
    connection_str = os.environ["blobConnectionString"]
    blob_service_client = BlobServiceClient.from_connection_string(connection_str)

    container_name = "$web"
    container_client = blob_service_client.get_container_client(container_name)

    blob_list = container_client.list_blobs(name_starts_with=f"images/{board_id}/")
    existing_images = sorted([b["name"] for b in blob_list], reverse=True)

    num_images = max(len(existing_images), 3)
    images_to_show = existing_images[0:num_images]








    # Render template
    show_string_raw = str(showMessageTemplateBlob.read())

    for x in ["\\n", "\\r", "b'"]:
        show_string_raw = show_string_raw.replace(x, "")

    show_template = Template(show_string_raw)
    rendered_show_template = show_template.render(board_id = board_id, content_items = message_list)

    logging.info('Template was processed.')


    #Write finished webpage to BLOB
    blob_client_show = BlobClient(account_url="https://adlsmessageboard.blob.core.windows.net", container_name="$web", blob_name=f"live_webpages/{board_id}/show_messages.html",
                        credential=os.environ["blob_key"])

    logging.info('BLOB client was created.')


    blob_client_show.upload_blob(rendered_show_template, blob_type="BlockBlob", overwrite=True, content_settings=ContentSettings(content_type="text/html; charset=utf-8"))


    return func.HttpResponse("Eintrag wurde angelegt.")