
from promptflow import tool
from dotenv import load_dotenv
load_dotenv("credentials.env")
from promptflow import tool
from pydantic import BaseModel
import os
from openai import AzureOpenAI  
import base64
import json


class FieldSchema(BaseModel):
        ConfidenceLevel: str
        Value: str

class SpanSchema(BaseModel):
        ConfidenceLevel: str
        Value: list[str]

class ExtractedInformation(BaseModel):   
        SPAN: list[SpanSchema] 
        GN: list[FieldSchema]            
        DOH_D: list[FieldSchema]
        DOH_L: list[FieldSchema]
        GIRD_SPACE: list[FieldSchema]
        D_WIDTH: list[FieldSchema]
        DOH_R: list[FieldSchema]
        SD_TOTAL: list[FieldSchema]
        D_EXT: list[FieldSchema]
        D_INT: list[FieldSchema]
        TD_CLR: list[FieldSchema]
        TD_SIZE_SPA: list[FieldSchema]
        TDOH_SIZE_SPA: list[FieldSchema]
        BD_SIZE_SPA: list[FieldSchema]
        BD_CLR: list[FieldSchema]

def image_to_data_url(image_bytes, mime_type='image/png'):  
    """  
    Convert image bytes to a data URL.  
  
    Parameters:  
    -----------  
    image_bytes : bytes  
        The image data in bytes.  
    mime_type : str  
        The MIME type of the image.  
  
    Returns:  
    --------  
    str  
        A data URL representing the image.  
    """  
    base64_encoded_data = base64.b64encode(image_bytes).decode('utf-8')  
    return f"data:{mime_type};base64,{base64_encoded_data}"


output_file_path = 'output/'

@tool
def content_extraction(images_meta, system_prompt, few_shot_prompt, page_text):

     
    client = AzureOpenAI(
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )
    aoai_deployment_name = os.environ["AZURE_OPENAI_MODEL"]  

    #fileName = images_meta['fileName']
    images_metadata = images_meta['images_metadata_cropped']
    bridge_number = images_meta['bridge_number']
    images_metadata_original = images_meta['images_metadata_original']
 
    if not images_metadata:
        return "No images found in the metadata."
    else:
         results = []

         for index, image in enumerate(images_metadata):
                page_number = image['page_number']
                image_path_cropped = image['image_path']
                image_path_original = images_metadata_original[index]['image_path']
            
                try:    
                            with open(image_path_cropped, 'rb') as image_file:
                                    image_bytes = image_file.read()
                                    # Convert image to data URL  
                                    image_data_url = image_to_data_url(image_bytes)
                            
                            with open(image_path_original, 'rb') as image_file:
                                    image_bytes = image_file.read()
                                    # Convert image to data URL  
                                    image_data_original_url = image_to_data_url(image_bytes)


                            # Few-shot examples
                            with open(f"input/few_shots/deck_section/0006862_train.pdf.jpg", 'rb') as image_file:
                                    image_bytes = image_file.read()
                                    image_data_url1 = image_to_data_url(image_bytes)

                            with open(f"input/few_shots/deck_section/0007179_train.jpg", 'rb') as image_file:
                                    image_bytes = image_file.read()                                 
                                    image_data_url2 = image_to_data_url(image_bytes)

                            with open(f"input/few_shots/deck_section/0013711_train.jpg", 'rb') as image_file:
                                    image_bytes = image_file.read()                                   
                                    image_data_url3 = image_to_data_url(image_bytes)
                            
                            #task_prompt1 = "This is the new image which is the cropped version with the selected diagram give you higher resolution for the first iteration of analysis,  Please also provide your confidence level for each field, the confidence level should be slected from the following list: ['low', 'medium', 'high'].  "
                            #task_prompt2 = """This is the new image which is the full version with all diagrams give for your second iteration of analysis, for the fields in the first iteration which is NOT FOUND, or with low confidence, 
                            #use this image to determine if you can find additioanl information.  if you find any additional information, please update the value and confidence level based on the results frome the first iteration. If you can not find any additional information, please keep the value and confidence level the same as the first iteration.
                            #D_EXT and D_INT usualyly can be found in the full version image NOTES section, so please make sure to check them carefully. check the values related to "D" for interial beam and external beams, if any find one 'D' value,  then both D_EXT and D_INT should have the same value.
                            #"""

                            task_prompt = """ Please follow the instructions below to extract the information from the input image and text:
                            1. You will be provided with two images and a text, the first image is the cropped version of the original image, and the second image is the full version of the original image. The text is the page text from the original PDF document.
                            2. The cropped image is the one that you need to analyze first which has the higher resolution of the selected diagram, extract the key fields. Please also provide your confidence level for each field, the confidence level should be slected from the following list: ['low', 'medium', 'high']
                            3. The full version image is the one that you need to analyze second, which has all diagrams, use this image to determine if you can find additioanl information for the fields in the first iteration which is NOT FOUND, or with low confidence, if you find any additional information, please update the value and confidence level based on the results frome the first iteration. If you can not find any additional information, please keep the value and confidence level the same as the first iteration.  
                            4. The text is the page text from the original PDF document, which can be used to help you to extract the information from notes section, especially for the fields related to D_EXT and D_INT, so please make sure to check them carefully. check the values related to "D" for interial beam and external beams, if any find one 'D' value,  then both D_EXT and D_INT should have the same value. 
                            5. Please first determine how many spans are in the image, and then extract the information for SPAN,  the span information is usually located in the bottom right corner of the image, and the span information.  If you find SPAN 1,  that means this image is for Span 1.  If you find SPAN 1 and 3 , that means this image is for Span 1 and 3,  for several fields inlcuding SL, BL, CTOC_BRGL and  PS_FORCE_FINAL, we need to extract the information for each span. Please refer to the training image provided earlier for the format of the output. 
                            6. Please extract the GN which is the number of beam,  generally we can use the far right beam number.  Please also count the number of beams in the image,  and confirm
                            7. When determining the value D_WIDTH,  There are two scenarios: if you see out ot out,  usually the value can be directly extracted from the image.  Otherwise, you need to calculate the value based on the image, usually take the three numbers on the top of the diagram and sum them up. Please be careful about the calculation,  this value is in format of feet-inch,  and when you calculate the results.  output it in the same format. e.g, 43'-3" Please refer to the training image provided earlier for the format of the output. please use the feet and inches as your final output,  1 feet = 12 inches, for example in the training image the D_WIDTH is D_WIDTH = 36' - 0''  + 1'-6 1/2 '' + 1' 6 1/2 '' = 39'-1"
     
                            """

                            print(f"page_text: {page_text[page_number]}")

                            messages=[{"role": "system",   "content": system_prompt}, 
                                      {"role": "user",    "content": [{"type": "text",  "text": few_shot_prompt}, {"type": "image_url",  "image_url": {"url": image_data_url1}}, {"type": "image_url",  "image_url": {"url": image_data_url2}}, {"type": "image_url",  "image_url": {"url": image_data_url3}}]}, 
                                      {"role": "user",    "content": [{"type": "text",  "text": task_prompt}, {"type": "image_url",  "image_url": {"url": image_data_url}}, {"type": "image_url",  "image_url": {"url": image_data_original_url}},  {"type": "text",  "text": page_text[page_number][2]}]},
                                      #{"role": "user",    "content": [{"type": "text",  "text": task_prompt1}, {"type": "image_url",  "image_url": {"url": image_data_url}}]},
                                      #{"role": "user",    "content": [{"type": "text",  "text": task_prompt2}, {"type": "image_url",  "image_url": {"url": image_data_original_url}}] }
                                    ]
                            
                            completion = client.beta.chat.completions.parse(  
                                    model=aoai_deployment_name,  
                                    messages=messages,
                                    response_format=ExtractedInformation)
                                
                            response = json.loads(completion.model_dump_json(indent=2))  
                            extracted_information = response['choices'][0]['message']['parsed']  
                            results.append(extracted_information)
                            
                except Exception as e:
                    print(f"Error processing images: {e}")
                    results.append({})
         
         images_meta["extracted_Reusts"] = results
         with open(f"{output_file_path}{bridge_number}_deck_section_extracted.json", 'w') as f:
              json.dump(images_meta, f, indent=2)   


    return images_meta
