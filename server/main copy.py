from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename
from google.cloud import vision
from flask_cors import CORS

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"C:\Users\kiran\OneDrive\Documents\Kiran\Smartstudy1\server\totemic-effect-427302-k0-9eeda753d6d8.json"
# Assuming you've set the GOOGLE_APPLICATION_CREDENTIALS environment variable
# (see instructions below)
client = vision.ImageAnnotatorClient()  # Initialize the Vision client

app = Flask(__name__)
CORS(app)

# Configure file upload
app.config['UPLOAD_FOLDER'] = 'uploads/'
allowed_extensions = set(['png', 'jpg', 'jpeg', 'gif'])


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
        response = {'error': 'No image file uploaded'}
        return jsonify(response), 400

    file = request.files['image']
    if file.filename == '':
        response = {'error': 'No selected file'}
        return jsonify(response), 400

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
    app.run(host='0.0.0.0', port=3002)  # Run on all interfaces (0.0.0.0) and port 3002
