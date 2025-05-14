import io
import os
import base64
from pathlib import Path
import requests
from generate_pdf import generate_pdf_report

# Function to get an image from URL and convert to base64
def get_image_base64(image_url):
    response = requests.get(image_url, stream=True)
    response.raise_for_status()
    img_buffer = io.BytesIO(response.content)
    return f"data:image/jpeg;base64,{base64.b64encode(img_buffer.getvalue()).decode('utf-8')}"

# Sample test images with building envelope features
image_urls = [
    "https://images.pexels.com/photos/2219024/pexels-photo-2219024.jpeg",  # Construction site
    "https://images.pexels.com/photos/1838640/pexels-photo-1838640.jpeg",  # Building exterior
]

# Download images and convert to base64
print("Downloading test images...")
images_with_data = []
for i, url in enumerate(image_urls):
    try:
        base64_data = get_image_base64(url)
        caption = "Close-up view of a single-ply membrane roofing system showing a mechanical fastener with a stress plate/washer centered in a cut-out access panel or repair patch, with visible seam lines and minor surface soiling around the perimeter." if i == 0 else "Exterior view of building envelope showing Tyvek weather barrier tape installation with visible wrinkled application at seam connections."
        images_with_data.append({
            "dataUrl": base64_data,
            "caption": caption
        })
        print(f"Downloaded image {i+1}")
    except Exception as e:
        print(f"Error downloading image {i+1}: {str(e)}")

# Create a long description text to test footer overflow
long_observation = """# Observations

Building Envelope Related:

1. Single-ply membrane roofing system with visible mechanical fastener and stress plate/washer installed in what appears to be a cut-out access panel or repair patch.

2. Seam lines visible on the membrane roofing with minor surface soiling around the perimeter.

3. DuPont Tyvek weather barrier tape showing wrinkled installation at a seam connection.

4. Compromised adhesion highlighted in a red box on the Tyvek tape installation, creating a potential pathway for air or water infiltration.

The observations reveal several concerning issues related to the building envelope that could compromise the structure's weather resistance and energy efficiency if not addressed properly. The single-ply membrane roofing system observation indicates possible repair work or an inspection access point. While the presence of a mechanical fastener with stress plate is standard practice for securing membranes, the context of it being within what appears to be a cut-out panel raises questions about whether this represents proper detailing or a field modification. 

The minor surface soiling around the perimeter could indicate early stages of ponding water or dirt accumulation, which may eventually lead to degraded membrane performance if not monitored. More concerning is the Tyvek weather barrier tape installation. The wrinkled application and compromised adhesion represent significant quality control failures during installation. Weather barriers serve as critical components in the building envelope system, providing the primary defense against water intrusion while allowing vapor transmission. Properly sealed seams are essential to this performance. The compromised adhesion highlighted in the red box presents an immediate vulnerability in the building envelope. These deficiencies create potential pathways for water infiltration, which can lead to several serious long-term consequences:

1. Water damage to structural components, including potential wood rot, steel corrosion, or concrete degradation

2. Mold and mildew growth, leading to indoor air quality issues and potential health concerns

3. Insulation degradation, reducing R-values and causing increased energy consumption

4. Decreased interior comfort and potential occupant health issues due to moisture intrusion

5. Possible reduction in the overall service life of the building components and systems

More concerning is the Tyvek weather barrier tape installation. The wrinkled application and compromised adhesion represent significant quality control failures during installation. Weather barriers serve as critical components in the building envelope system, providing the primary defense against water intrusion while allowing vapor transmission. Properly sealed seams are essential to this performance. The compromised adhesion highlighted in the red box presents an immediate vulnerability in the building envelope."""

# Sample report data with formats that showcase all the formatting enhancements
sample_report_data = {
    "projectName": "Building Envelope Assessment - Layout Test",
    "reportNumber": "TEST-LAYOUT-001",
    "subject": "Testing Page Layout Fixes",
    "description": long_observation,
    "action": """## Recommended Action Items

**Immediate Actions Required**:

1. Inspect the single-ply membrane repair area to verify proper installation and sealing.

2. Clean the soiled perimeter areas to prevent further accumulation and inspect for proper drainage.

3. Remove and reinstall the wrinkled Tyvek weather barrier tape according to manufacturer specifications.

4. Apply new adhesive to the compromised section of tape to ensure proper sealing and water resistance.

**Follow-up Items**:

1. Schedule a follow-up inspection after repairs to verify proper performance.

2. Consider water testing the repaired areas to ensure proper sealing.

3. Review installation practices with the construction team to prevent similar issues.

4. Document all corrections for project records.

5. Conduct regular inspections of the building envelope to identify any additional issues.""",
    "images": images_with_data
}

# Create a directory to save the PDF
output_dir = Path("./pdf_samples")
output_dir.mkdir(exist_ok=True)

# Generate the PDF using our enhanced generator
try:
    print("Generating PDF with improved page layout...")
    pdf_buffer = generate_pdf_report(sample_report_data)
    
    # Save the PDF to a file
    output_file = output_dir / "page_layout_test.pdf"
    with open(output_file, "wb") as f:
        f.write(pdf_buffer.getbuffer())
    
    print(f"PDF generated successfully and saved to {output_file}")
    print(f"PDF size: {os.path.getsize(output_file) / 1024:.2f} KB")
except Exception as e:
    print(f"Error generating PDF: {str(e)}")
    import traceback
    traceback.print_exc() 