
from promptflow import tool
import fitz  # PyMuPDF 
import os 


image_output_path =  'input/images/'
pdf_input_path = 'input/pdf/'
 
@tool
def file_processing(fileName: str, bridge_number: str) -> str:

    pdf_file = f'{pdf_input_path}{fileName}'
    doc = fitz.open(pdf_file)

    counter = 0
    images = []


    # Prepare output directory and image path
    output_dir = f"{image_output_path}{bridge_number}/"
    os.makedirs(output_dir, exist_ok=True)  # Ensure directory exists

    output_dir = f"{image_output_path}{bridge_number}/original/"
    os.makedirs(output_dir, exist_ok=True)  # Ensure directory exists

    
    output_dir = f"{image_output_path}{bridge_number}/cropped/"
    os.makedirs(output_dir, exist_ok=True)  # Ensure directory exists


    for page_number in range(len(doc)):
            
        try:  
            # Load the page  
            page = doc.load_page(page_number)  
            zoom = 2  # Zoom factor for image quality  
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))  
            image_bytes = pix.tobytes()  

            # Save the image to output_images directory  
            
            image_name = f"{image_output_path}{bridge_number}/original/{fileName.split('.')[0]}_page{page_number + 1}.png"

            pix.save(str(image_name))  
            print(f"Saved image to {image_name}")  

            # Print the image size and dimensions  
            image_size = os.path.getsize(str(image_name))  
            print(f"Image size: {image_size} bytes")  
            print(f"Image dimensions: {pix.width}x{pix.height}")   
            counter+=1
            images.append({"page_number": page_number, "image_path": image_name, "status": True})

        except Exception as e:  
            print(f"Error processing page {page_number} of {fileName}: {e}")
            images.append({"page_number": page_number,   "status": False, "error_message": str(e)})

    
    rst = {
         
        "fileName": fileName,
        "bridge_number": bridge_number,
        "number_of_page": len(doc),
        "images_metadata": images
    }

    return rst
