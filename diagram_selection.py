
from promptflow import tool
from pydantic import BaseModel
import os
from openai import AzureOpenAI  
import base64
import json
import cv2
from dotenv import load_dotenv
load_dotenv("credentials.env")


## Sample output from file_processing.py
# {
#   "fileName": "0000305_35-0006_FINAL_100317.pdf",
#   "number_of_page": 1,
#   "images_metadata": [
#     {
#       "page_number": 0,
#       "image_path": "input/images/0000305/original/0000305_35-0006_FINAL_100317_page1.png",
#       "status": true
#     }
#   ]
# }


class ExtractedInformationDiagram(BaseModel):        
        Image_Width: int
        Image_Height: int
        x1: int
        y1: int
        x2: int
        y2: int


def cropped_img(image_path_input, image_path_output, cropped_info):
    # Read the image
    try:
        img = cv2.imread(image_path_input)
        

        ratio_y = img.shape[0]/cropped_info['Image_Height']
        ratio_x = img.shape[1] /cropped_info['Image_Width']

        # Crop the image using the coordinates
        cropped_img = img[round(ratio_y*cropped_info['y1']):round(ratio_y*cropped_info['y2']), round(ratio_x*cropped_info['x1']):round(ratio_x*cropped_info['x2'])]

        # Save the cropped image
        cv2.imwrite(image_path_output, cropped_img)

        return {"status": True, "cropped_image_path": image_path_output}
    except Exception as e:
        print(f"Error cropping image {image_path_input}: {e}")
        return {"status": False, "error_message": str(e)}

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


@tool
def diagram_selection(images_meta, system_prompt) :

    
    

# Initialize the Azure OpenAI client  
    client = AzureOpenAI(
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )
    aoai_deployment_name = os.environ["AZURE_OPENAI_MODEL"]  

    fileName = images_meta['fileName']
    images_metadata = images_meta['images_metadata']
    bridge_number = images_meta['bridge_number']
    
    rst = {
         
                "fileName": fileName,
                "bridge_number": bridge_number,
                "images_metadata_cropped": [], 
                "images_metadata_original": images_metadata
            } 
    
    if not images_metadata:
        return "No images found in the metadata."
    else:
            images = []         
            for image in images_metadata:
                page_number = image['page_number']
                image_path = image['image_path']


                task_prompt = "This is the new image that you need to analyze, please extract the coodinate for the diagram. "

                try:    
                    with open(image_path, 'rb') as image_file:
                            image_bytes = image_file.read()
                            # Convert image to data URL  
                            image_data_url = image_to_data_url(image_bytes)

                            messages=[{"role": "system",   "content": system_prompt}, 
                                    {"role": "user",    "content": [{"type": "text",  "text": task_prompt}, {"type": "image_url",  "image_url": {"url": image_data_url}}]}, 
                                    ]
                            
                            completion = client.beta.chat.completions.parse(  
                                    model=aoai_deployment_name,  
                                    messages=messages,
                                    response_format=ExtractedInformationDiagram)
                                
                            response = json.loads(completion.model_dump_json(indent=2))  
                            cropped_info = response['choices'][0]['message']['parsed']  

                            image_path_output = f'input/images/{bridge_number}/cropped/{fileName.split(".")[0]}_page{page_number + 1}_cropped.png'
                            
                            images.append({"page_number": page_number, "image_path": image_path_output, "status": True})

                            cropped_img(image_path, image_path_output, cropped_info)

                except Exception as e:
                    print(f"Error processing images: {e}")
                    images.append({"page_number": page_number,  "status": False, "error_message": str(e)})

            rst["images_metadata_cropped"] = images

    return rst
