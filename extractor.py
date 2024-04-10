# extractor.py
from fastapi import APIRouter

from fastapi import UploadFile, File, Body
from pydantic import BaseModel, Field
from typing import Optional
import json

from openai import OpenAI

from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)
model = "gpt-4-turbo-2024-04-09"
router = APIRouter()

class ExtractData(BaseModel):
    data: Optional[str] = Field(None, alias="fields")
    pdf: Optional[UploadFile] = File(None)


async def extract_information(main_schema_reasoning, query, context):
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": """
                    You are extracting data from a form of text based on a user query. 
                    Return None otherwise. 
                    Please provide a confidence score based on how likely you think the answer is correct based on the context. 
                    If there are multiple answers, please seperate by commas",
                    You may be passed tables as HTML. Numbers tend to be to the right of the text.
                    """
            },
            {
                "role": "user",
                "content": (
                    "Please extract " + str(query)
                ) + "\n"
                + "###"
                + str(context),
            },
        ],
        functions=[
            {"name": "answer_multiple_choice", "parameters": main_schema_reasoning}
        ],
        function_call={"name": "answer_multiple_choice"},
        temperature=0,
    )
    

    main_json = completion.choices[0].message.function_call.arguments
    main_json = json.loads(main_json)

    print(main_json)

    return main_json


@router.post("/extract")
async def extract_data(extract_data: ExtractData = Body(...)):
    schema = json.loads(extract_data.data)

    schema = schema['fields']

    data_extracted = {"usage":{"num_pages":1},"result":{"type":"full","chunks":[{"content":"# PHONE: (270) 465-2624\n\nCustomer No. 68108\n\nJob No. 37\n\nPurchase Order No.\n\nReference\n\nTerms 2% 10TH. NET 30\n\nClerk SAM\n\nDate Time 3/25/24 8:\n\nSold To HAMMOND & BRANDT BUILDERS, LLC P O BOX 150828 NASHVILLE TN 37215\n\nShip To 2104 NATCHEZ TRACE NASHVILLE TN 37215\n\nDOC# M73982 TERM#557 *CREDIT MEMO* SLSPR: 39 ROBIN CALLAHAN TAX : 052 NASHVILLE/DAVIDSON CO","embed":"# PHONE: (270) 465-2624\n\nCustomer No. 68108\n\nJob No. 37\n\nPurchase Order No.\n\nReference\n\nTerms 2% 10TH. NET 30\n\nClerk SAM\n\nDate Time 3/25/24 8:\n\nSold To HAMMOND & BRANDT BUILDERS, LLC P O BOX 150828 NASHVILLE TN 37215\n\nShip To 2104 NATCHEZ TRACE NASHVILLE TN 37215\n\nDOC# M73982 TERM#557 *CREDIT MEMO* SLSPR: 39 ROBIN CALLAHAN TAX : 052 NASHVILLE/DAVIDSON CO","enriched":None,"enrichment_success":False,"blocks":[{"type":"Header","bbox":{"left":0.3913367986679077,"top":0.03369634225964546,"width":0.22752125561237335,"height":0.05451235920190811,"page":1},"content":"COX INTERIOR, INC.\n1751 OLD COLUMBIA RD\nCAMPBELLSVILLE, KY 42718"},{"type":"Page Number","bbox":{"left":0.8346150517463684,"top":0.032403361052274704,"width":0.0737486258149147,"height":0.011384516023099422,"page":1},"content":"PAGE NO\n1"},{"type":"Title","bbox":{"left":0.42201361060142517,"top":0.10471180826425552,"width":0.16714777052402496,"height":0.019676880910992622,"page":1},"content":"PHONE: (270) 465-2624"},{"type":"Text","bbox":{"left":0.05813441798090935,"top":0.1957378387451172,"width":0.06039692461490631,"height":0.026615513488650322,"page":1},"content":"Customer No. 68108"},{"type":"Text","bbox":{"left":0.14078661799430847,"top":0.19540810585021973,"width":0.034996114671230316,"height":0.02698349952697754,"page":1},"content":"Job No. 37"},{"type":"Text","bbox":{"left":0.19232064485549927,"top":0.19546157121658325,"width":0.0905146598815918,"height":0.009436121210455894,"page":1},"content":"Purchase Order No."},{"type":"Text","bbox":{"left":0.38931944966316223,"top":0.19506220519542694,"width":0.04677501320838928,"height":0.009862111881375313,"page":1},"content":"Reference"},{"type":"Text","bbox":{"left":0.5748492479324341,"top":0.19534212350845337,"width":0.10260720551013947,"height":0.026663141325116158,"page":1},"content":"Terms 2% 10TH. NET 30"},{"type":"Text","bbox":{"left":0.7429856061935425,"top":0.19451315701007843,"width":0.03131262585520744,"height":0.027458278462290764,"page":1},"content":"Clerk SAM"},{"type":"Text","bbox":{"left":0.8333765268325806,"top":0.19482579827308655,"width":0.1144159808754921,"height":0.027663694694638252,"page":1},"content":"Date Time 3/25/24 8:"},{"type":"Text","bbox":{"left":0.08797098696231842,"top":0.2471405565738678,"width":0.21270005404949188,"height":0.08325590938329697,"page":1},"content":"Sold To HAMMOND & BRANDT BUILDERS, LLC P O BOX 150828 NASHVILLE TN 37215"},{"type":"Text","bbox":{"left":0.3447457253932953,"top":0.2469070851802826,"width":0.16772331297397614,"height":0.08383198827505112,"page":1},"content":"Ship To 2104 NATCHEZ TRACE NASHVILLE TN 37215"},{"type":"Text","bbox":{"left":0.5886984467506409,"top":0.26388970017433167,"width":0.34718793630599976,"height":0.08501258492469788,"page":1},"content":"DOC# M73982 TERM#557 *CREDIT MEMO* SLSPR: 39 ROBIN CALLAHAN TAX : 052 NASHVILLE/DAVIDSON CO"}]},{"content":"# PHONE: (270) 465-2624 (cont.)\n\n<table><tr><th>SHIPPED</th><th>ORDERED</th><th>UM</th><th>SKU</th><th>DESCRIPTION</th><td></td><th>UNITS</th><th>PRICE/PER</th><th colspan=\"2\">EXTENSION</th></tr><tr><td>-162</td><td></td><td>LF</td><td>MISSM</td><td>POP PLINTH BLOCKS 1\" THICK CREDIT RETURN OrigInv#1/M73980</td><td></td><td>162</td><td>5.48 /LF</td><td colspan=\"2\">-887.76R</td></tr><tr><td>-1</td><td></td><td>LF</td><td>MIS</td><td>X 3 3/4 WIDE X 9 1/4\" TALL CREDIT RETURN OrigInv#1/M73980</td><td></td><td>1</td><td>/LF</td><td colspan=\"2\">R</td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td colspan=\"2\"></td></tr><tr><td></td><td></td><td></td><td>6771</td><td colspan=\"2\">** AMOUNT CREDITED TO ACCOUNT **</td><td>969.88</td><td>TAXABLE</td><td></td><td>-887.76</td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td colspan=\"2\">NON-TAXABLE</td><td>0.00</td></tr><tr><td colspan=\"9\">SUBTOTAL</td><td>-887.76</td></tr><tr><td colspan=\"7\"></td><td>TAX AMOUNT</td><td></td><td>-82.12</td></tr><tr><td colspan=\"9\">TOTAL AMOUNT</td><td>-969.88</td></tr></table>","embed":"# PHONE: (270) 465-2624 (cont.)\n\n<table><tr><th>SHIPPED</th><th>ORDERED</th><th>UM</th><th>SKU</th><th>DESCRIPTION</th><td></td><th>UNITS</th><th>PRICE/PER</th><th colspan=\"2\">EXTENSION</th></tr><tr><td>-162</td><td></td><td>LF</td><td>MISSM</td><td>POP PLINTH BLOCKS 1\" THICK CREDIT RETURN OrigInv#1/M73980</td><td></td><td>162</td><td>5.48 /LF</td><td colspan=\"2\">-887.76R</td></tr><tr><td>-1</td><td></td><td>LF</td><td>MIS</td><td>X 3 3/4 WIDE X 9 1/4\" TALL CREDIT RETURN OrigInv#1/M73980</td><td></td><td>1</td><td>/LF</td><td colspan=\"2\">R</td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td colspan=\"2\"></td></tr><tr><td></td><td></td><td></td><td>6771</td><td colspan=\"2\">** AMOUNT CREDITED TO ACCOUNT **</td><td>969.88</td><td>TAXABLE</td><td></td><td>-887.76</td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td colspan=\"2\">NON-TAXABLE</td><td>0.00</td></tr><tr><td colspan=\"9\">SUBTOTAL</td><td>-887.76</td></tr><tr><td colspan=\"7\"></td><td>TAX AMOUNT</td><td></td><td>-82.12</td></tr><tr><td colspan=\"9\">TOTAL AMOUNT</td><td>-969.88</td></tr></table>","enriched":None,"enrichment_success":False,"blocks":[{"type":"Table","bbox":{"left":0.04420928657054901,"top":0.38455554842948914,"width":0.9186877012252808,"height":0.5035775303840637,"page":1},"content":"<table><tr><th>SHIPPED</th><th>ORDERED</th><th>UM</th><th>SKU</th><th>DESCRIPTION</th><td></td><th>UNITS</th><th>PRICE/PER</th><th colspan=\"2\">EXTENSION</th></tr><tr><td>-162</td><td></td><td>LF</td><td>MISSM</td><td>POP PLINTH BLOCKS 1\" THICK CREDIT RETURN OrigInv#1/M73980</td><td></td><td>162</td><td>5.48 /LF</td><td colspan=\"2\">-887.76R</td></tr><tr><td>-1</td><td></td><td>LF</td><td>MIS</td><td>X 3 3/4 WIDE X 9 1/4\" TALL CREDIT RETURN OrigInv#1/M73980</td><td></td><td>1</td><td>/LF</td><td colspan=\"2\">R</td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td colspan=\"2\"></td></tr><tr><td></td><td></td><td></td><td>6771</td><td colspan=\"2\">** AMOUNT CREDITED TO ACCOUNT **</td><td>969.88</td><td>TAXABLE</td><td></td><td>-887.76</td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td colspan=\"2\">NON-TAXABLE</td><td>0.00</td></tr><tr><td colspan=\"9\">SUBTOTAL</td><td>-887.76</td></tr><tr><td colspan=\"7\"></td><td>TAX AMOUNT</td><td></td><td>-82.12</td></tr><tr><td colspan=\"9\">TOTAL AMOUNT</td><td>-969.88</td></tr></table>"}]},{"content":"# PHONE: (270) 465-2624 (cont.)","embed":"# PHONE: (270) 465-2624 (cont.)","enriched":None,"enrichment_success":False,"blocks":[{"type":"Footer","bbox":{"left":0.14026705920696259,"top":0.9497212767601013,"width":0.057440221309661865,"height":0.011075405403971672,"page":1},"content":"Received By"}]}]}}

    chunks = data_extracted['result']['chunks']

    chunk_contents = [{"content": chunk['content']} for chunk in chunks]

    data = {}
    for field in schema:
        print(field)
        #print("FIELD : " + str(field))
        main_schema_reasoning = {
            "type": "object",
                "properties": {
                    field['name']: {
                        "type": "string",
                        "description": field['name'],
                    },
                    "confidence_score": {
                        "type": "string",
                        "description": "A score from 0-100 about how confident you are in your answer.",
                    },
                    # "reasoning": {
                    #     "type": "string",
                    #     "description": "reasoning behind the text"
                    # }
                },
                "required": [field['name'], "confidence_score"],
        }

        extract_data = await extract_information(main_schema_reasoning, field['name'], chunk_contents)

        print(extract_data)

        
        data[field['name']] = extract_data[field['name']]

    print(data)


    return data
