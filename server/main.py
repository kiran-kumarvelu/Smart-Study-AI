from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from google.cloud import vision  # Assuming you have Google Cloud Vision set up
from pdf2image import convert_from_path # Assuming you have PyPDF2 installed
import fitz
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads/'
allowed_extensions = set(['png', 'jpg', 'jpeg', 'gif', 'pdf'])
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"C:/Users/kiran/OneDrive/Desktop/Smartstudy1/server/totemic-effect-427302-k0-9eeda753d6d8.json"
# Assuming you've set the GOOGLE_APPLICATION_CREDENTIALS environment variable
# (see instructions below)
client = vision.ImageAnnotatorClient()  # Initialize the Vision client

def convert_page_to_image(page):
  """
  Converts a PyMuPDF page object to an image file.

  Args:
      page (fitz.Page): The PyMuPDF page object to convert.

  Returns:
      str: Path to the saved image file.
  """
  # Set desired image resolution (adjust as needed)
  dpi = 300
  matrix = fitz.Matrix(dpi / 72, dpi / 72)

  # Extract the page pixmap with the specified matrix
  pixmap = page.get_pixmap(matrix=matrix)

  # Generate a unique filename for the temporary image
  filename = f"temp_page_{page.number}.jpg"
  image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

  # Save the pixmap as a JPEG image
  pixmap.save(image_path)

  return image_path

def extract_text_from_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    images = convert_from_path(pdf_path)  # Convert PDF to PIL Image objects
    results = []  # List to store results from do_action

    for i, image in enumerate(images):
        result = extract_text_from_image(image)  # Apply do_action to each page image
        results.append(result)

    # Combine results into a cumulative string (modify as needed)
    cumulative_result = "\n".join(results)

    return cumulative_result

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions
           
@app.route('/', methods=['GET'])
def upload_form():
  return """
  <form method="POST" enctype="multipart/form-data">
    <input type="file" name="image">
    <input type="submit">
  </form>
  """


@app.route('/api/extract-text', methods=['POST'])
def extract_text():
  if 'image' not in request.files:
    response = {'error': 'No file uploaded'}
    return jsonify(response), 400

  file = request.files['image']
  if file.filename == '':
    response = {'error': 'No selected file'}
    return jsonify(response), 400

  if file and allowed_file(file.filename):
    filename = secure_filename(file.filename)
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(image_path)

    if filename.endswith('.pdf'):
      # Use the new function for PDF processing
      extracted_text = extract_text_from_pdf(image_path)
    else:
      # Existing logic for handling images
      try:
        with open(image_path, 'rb') as image_file:
          content = image_file.read()
          image = vision.Image(content=content)
          response = client.text_detection(image=image)
          extracted_text = response.full_text_annotation.text
      except Exception as e:
        print(f"Error extracting text: {e}")
        response = {'error': 'Failed to extract text'}
        return jsonify(response), 500

    os.remove(image_path)  # Delete temporary file

    return jsonify({'extractedText': extracted_text})
  else:
    response = {'error': 'Unsupported file format'}
    return jsonify(response), 400

def extract_text_from_image() :
    file = request.files['image']
    

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(image_path)

        # Text extraction logic using Google Cloud Vision
        try:
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            image = vision.Image(content=content)

            response = client.text_detection(image=image)
            extracted_text = response.full_text_annotation.text

            os.remove(image_path)  # Delete temporary file

            return jsonify({'extractedText': extracted_text})
        except Exception as e:
            print(f"Error extracting text: {e}")
            response = {'error': 'Failed to extract text'}
            return jsonify(response), 500

    else:
        response = {'error': 'Unsupported file format'}
        return jsonify(response), 400
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3002)