import os
from cleaner import clean_html
from reformatter import reformat_html

def save_html(output_filename, content):
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"file saved to '{output_filename}'")

# def main():
#     input_file = "ReplacingtheForm4LresincartridgeRFIDboard.html"
    
#     try:
#         with open(input_file, 'r', encoding='utf-8') as f:
#             html_content = f.read()

#         #clean the html
#         cleaned_content = clean_html(html_content)

#         #reformat after cleaning
#         reformatted_content = reformat_html(cleaned_content)
        
#         #save final file
#         filename, extension = os.path.splitext(input_file)
      
#         # output_file = f"formatted_{filename}{extension}"
#         output_file = f"test_{filename}{extension}"
#         save_html(output_file, reformatted_content)
#         #save_html(output_file, cleaned_content)
        
#     except FileNotFoundError:
#         print(f"Error: file was not found")

def main():
    """
    Processes all HTML files in a specified folder.
    """
    input_folder = "/Users/aya.kakizaki/Desktop/SLA repair script"  #save path
    
    for filename in os.listdir(input_folder):
        if filename.endswith(".html") or filename.endswith(".htm"):
            input_file = os.path.join(input_folder, filename)
            
            try:
                with open(input_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()

                print(f"\nProcessing '{filename}'...")

                #clean html
                cleaned_content = clean_html(html_content)

                #reformat html next
                reformatted_content = reformat_html(cleaned_content)
                
                output_file = f"reformatted_{filename}"
                save_html(output_file, reformatted_content)
                
            except FileNotFoundError:
                print(f"Error: The file '{input_file}' was not found.")
            except Exception as e:
                print(f"An error occurred while processing '{input_file}': {e}")


if __name__ == "__main__":
    main()