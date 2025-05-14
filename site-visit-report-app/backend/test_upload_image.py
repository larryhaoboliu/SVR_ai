import requests

# Set the Flask API URL and the image path
url = "http://localhost:5001/analyze-image"
image_path = "C:/Larry/apple.jpg"  # Update with your image path

# Open the image file in binary mode
with open(image_path, "rb") as image_file:
    # Send a POST request to the Flask API with the image file
    files = {"image": image_file}
    response = requests.post(url, files=files)

    # Print the JSON response from the Flask API
    print(response.json())
