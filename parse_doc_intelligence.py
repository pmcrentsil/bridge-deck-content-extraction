import html
import os
import pickle

import markdownify
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import DocumentAnalysisFeature

from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
from promptflow.core import tool
import json
load_dotenv("credentials.env")



pdf_input_path = 'input/pdf/'

 

def table_conversion(table, table_format):
    table_html = "<table>"
    rows = [
        sorted(
            [cell for cell in table.cells if cell.row_index == i],
            key=lambda cell: cell.column_index,
        )
        for i in range(table.row_count)
    ]
    for row_cells in rows:
        table_html += "<tr>"
        for cell in row_cells:
            tag = (
                "th"
                if (cell.kind == "columnHeader" or cell.kind == "rowHeader")
                else "td"
            )
            cell_spans = ""
            if cell.column_span is not None and cell.column_span > 1:
                cell_spans += f" colSpan={cell.column_span}"
            if cell.row_span is not None and cell.row_span > 1:
                cell_spans += f" rowSpan={cell.row_span}"
            table_html += f"<{tag}{cell_spans}>{html.escape(cell.content)}</{tag}>"
        table_html += "</tr>"
    table_html += "</table>"

    if table_format == "md":
        table_html = markdownify.markdownify(table_html, heading_style="ATX")

    return table_html


# The inputs section will change based on the arguments of the tool function, after you save the code
# Adding type to arguments and return value will help the system show the types properly
# Please update the function name/signature per need
@tool
def pdf_parsing_Doc_intelligence(fiLeName: str, table_format: str) -> str:
    credential = AzureKeyCredential(os.environ["DOCUMENT_INTELLIGENCE_KEY"])
    offset = 0
    page_map = []
    # form_recognizer_client = DocumentAnalysisClient(endpoint=os.environ["DOCUMENT_INTELLIGENCE_ENDPOINT"], credential=credential)
    # poller = form_recognizer_client.begin_analyze_document_from_url("prebuilt-layout", document_url = url)

    di_client = DocumentIntelligenceClient(
        endpoint=os.environ["DOCUMENT_INTELLIGENCE_ENDPOINT"], credential=credential
    )
    #poller = di_client.begin_analyze_document(
    #    "prebuilt-layout", AnalyzeDocumentRequest(url_source=url)
    #)

    with open(f"{pdf_input_path}/{fiLeName}", "rb") as f:
        poller = di_client.begin_analyze_document(
            "prebuilt-layout", body=f, features=[DocumentAnalysisFeature.OCR_HIGH_RESOLUTION]
    )
        
    form_recognizer_results = poller.result()

    for page_num, page in enumerate(form_recognizer_results.pages):
        # tables_on_page = [table for table in form_recognizer_results.tables if table.bounding_regions[0].page_number == page_num + 1]
        tables_on_page = [
            table
            for table in (form_recognizer_results.tables or [])
            if table.bounding_regions
            and table.bounding_regions[0].page_number == page_num + 1
        ]
        # mark all positions of the table spans in the page
        page_offset = page.spans[0].offset
        page_length = page.spans[0].length
        table_chars = [-1] * page_length
        for table_id, table in enumerate(tables_on_page):
            for span in table.spans:
                # replace all table spans with "table_id" in table_chars array
                for i in range(span.length):
                    idx = span.offset - page_offset + i
                    if idx >= 0 and idx < page_length:
                        table_chars[idx] = table_id

        # build page text by replacing charcters in table spans with table html
        page_text = ""
        added_tables = set()
        for idx, table_id in enumerate(table_chars):
            if table_id == -1:
                page_text += form_recognizer_results.content[page_offset + idx]
            elif not table_id in added_tables:
                page_text += table_conversion(tables_on_page[table_id], table_format)
                added_tables.add(table_id)

        page_text += " "
        page_map.append((page_num, offset, page_text))
        offset += len(page_text)
        #print(f"page_num: {page_num} page_num: {offset} page_num: {page_text}")

    return page_map
