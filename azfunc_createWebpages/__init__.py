import logging
import azure.functions as func
from azure.storage.blob import BlobClient, ContentSettings, BlobServiceClient, ContainerClient
import os

from jinja2 import Template



def main(req: func.HttpRequest, enterMessageTemplateBlob: func.InputStream,
        showMessageTemplateBlob: func.InputStream) -> func.HttpResponse:

    logging.info('Python HTTP trigger function processed a request.')

    board_id = dict(req.form)["board_id"]
    if not board_id:
        return func.HttpResponse(f"Hello, please pass a board_id in the request body.")

    # Verfiy name for forbidden characters
    forbidden_character_list = ["/", "\\"]
    if any(f in board_id for f in forbidden_character_list):
        return func.HttpResponse("Der Name enthält ungültige Zeichen. Bitte nur Buchstaben, Zahlen und Leerzeichen verwenden.")

    # Check if board_id already exists
    connection_str = os.environ["blobConnectionString"]
    blob_service_client = BlobServiceClient.from_connection_string(connection_str)

    container_name = "$web"
    container_client = blob_service_client.get_container_client(container_name)

    blob_list = container_client.list_blobs(name_starts_with="live_webpages/")
    existing_boards_list = list(set([b["name"].split("/")[1] for b in blob_list]))

    if board_id in existing_boards_list:
        return func.HttpResponse("Dieser Name wird bereits verwendet, bitte einen anderen auswählen.")

    logging.info("Board name is valid.")

    # Render both templates
    enter_string_raw = str(enterMessageTemplateBlob.read())
    show_string_raw = str(showMessageTemplateBlob.read())

    for x in ["\\n", "\\r", "b'"]:
        enter_string_raw = enter_string_raw.replace(x, "")
        show_string_raw = show_string_raw.replace(x, "")

    enter_template = Template(enter_string_raw)
    show_template = Template(show_string_raw)

    rendered_enter_template = enter_template.render(board_id = board_id, iframe_page = f"https://adlsmessageboard.z1.web.core.windows.net/live_webpages/{board_id}/show_messages.html")
    rendered_show_template = show_template.render(board_id = board_id, content_items = [])


    logging.info('Templates were processed.')


    #Write finished webpages to BLOB
    blob_client_enter = BlobClient(account_url="https://adlsmessageboard.blob.core.windows.net", container_name="$web", blob_name=f"live_webpages/{board_id}/enter_message.html",
                        credential=os.environ["blob_key"])
    blob_client_show = BlobClient(account_url="https://adlsmessageboard.blob.core.windows.net", container_name="$web", blob_name=f"live_webpages/{board_id}/show_messages.html",
                        credential=os.environ["blob_key"])

    logging.info('BLOB client was created.')


    blob_client_enter.upload_blob(rendered_enter_template, blob_type="BlockBlob", overwrite=True, content_settings=ContentSettings(content_type="text/html; charset=utf-8"))
    blob_client_show.upload_blob(rendered_show_template, blob_type="BlockBlob", overwrite=True, content_settings=ContentSettings(content_type="text/html; charset=utf-8"))


    enter_page_url = f"https://adlsmessageboard.z1.web.core.windows.net/live_webpages/{board_id}/enter_message.html"
    show_page_url = f"https://adlsmessageboard.z1.web.core.windows.net/live_webpages/{board_id}/show_messages.html"

    response_string = f"Die Websiten wurden erstellt!\n Eingabe-Website: {enter_page_url}\n Anzeige-Website: {show_page_url}"

    return func.HttpResponse(response_string)