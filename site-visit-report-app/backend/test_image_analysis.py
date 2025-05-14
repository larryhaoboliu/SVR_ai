import requests
import os
import sys

def test_image_analysis():
    # URL of the Flask endpoint
    url = 'http://localhost:5001/analyze-image'
    
    # Check if image path was provided as argument
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        # Default to a sample image if available
        sample_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(os.path.dirname(sample_dir), 'apple.jpg')
        
        if not os.path.exists(image_path):
            print(f"Error: Could not find default image at {image_path}")
            print("Please provide an image path as argument: python test_image_analysis.py path/to/image.jpg")
            return
    
    print(f"Testing image analysis with image: {image_path}")
    
    # Check if the file exists
    if not os.path.exists(image_path):
        print(f"Error: The file {image_path} does not exist.")
        return
    
    # Open image file
    with open(image_path, 'rb') as image_file:
        # Create a multipart form with the image
        files = {'image': (os.path.basename(image_path), image_file, 'image/jpeg')}
        
        # Send the request
        try:
            response = requests.post(url, files=files)
            
            # Print the status code
            print(f"Status Code: {response.status_code}")
            
            # Print the response
            if response.status_code == 200:
                print("Success! Generated description:")
                print(response.json().get('description', 'No description generated'))
            else:
                print("Error response:")
                print(response.text)
        except Exception as e:
            print(f"Exception occurred: {e}")

if __name__ == "__main__":
    test_image_analysis() 