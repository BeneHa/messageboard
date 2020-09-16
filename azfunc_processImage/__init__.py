import logging
import os
from azure.storage.blob import BlobClient, ContentSettings, BlobServiceClient, ContainerClient
from babel.dates import format_date
import datetime


import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    image = req.files['file1'].read()
    image_name = req.files["file1"].filename
    board_id = req.form["board_id"]
    logging.info("Image was read.")

    time_local_timezone = datetime.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")

    blob_client = BlobClient(account_url="https://adlsmessageboard.blob.core.windows.net", container_name="$web",
                    blob_name=f"images/{board_id}/{time_local_timezone}|{image_name}", credential=os.environ["blob_key"])

    blob_client.upload_blob(image, blob_type="BlockBlob", overwrite=True)
    logging.info("Image was uploaded to BLOB.")




    return func.HttpResponse("Foto wurde hochgeladen.", status_code=200)