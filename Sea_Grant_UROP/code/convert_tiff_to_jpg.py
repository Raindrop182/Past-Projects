from PIL import Image
import os

def convert_tiffs_to_jpgs(input_folder, output_folder):
    """
    Converts all TIFF files in the input_folder to JPEG format
    and saves them in the output_folder.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(('.tif', '.tiff')):
            try:
                filepath = os.path.join(input_folder, filename)
                img = Image.open(filepath)
                
                output_filename = os.path.splitext(filename)[0] + '.jpg'
                output_filepath = os.path.join(output_folder, output_filename)
                
                img = img.convert('RGB')
                img.save(output_filepath, 'jpeg', quality=15) 
                print(f"Converted '{filename}' to '{output_filename}'")
            except Exception as e:
                print(f"Error converting '{filename}': {e}")

if __name__ == "__main__":
    input_directory = r"C:\Users\raine\Downloads\in"
    output_directory = r"C:\Users\raine\Downloads\in"

    convert_tiffs_to_jpgs(input_directory, output_directory)
    
