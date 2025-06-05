import base64
import requests
from flask import Flask, request, jsonify, send_file, send_from_directory
import os
import sys
import traceback
from flask_cors import CORS
from dotenv import load_dotenv
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import tempfile
from PIL import Image as PILImage, ImageFile, ExifTags
from datetime import datetime
import logging
import json
import re
import rag_service

# Import the alternative PDF generator
from generate_pdf import generate_pdf_report

# Import security middleware
from security import setup_security, rate_limit, require_api_key, sanitize_input

# Import access code management
import access_management

# Import storage factory
from storage.storage_factory import get_storage

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='')

# Apply security middleware
app = setup_security(app)

# Anthropic API Key
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
if not anthropic_api_key:
    print("WARNING: Anthropic API key not found in environment variables. Please add it to your .env file.")

# Initialize RAG service
rag_service_instance = rag_service.get_rag_service()

# Initialize storage
storage_instance = get_storage()

# Serve React App
@app.route('/')
def serve_react_app():
    """Serve the React app's index.html"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_react_static(path):
    """Serve React static files or fallback to index.html for client-side routing"""
    # Don't handle API routes here
    if path.startswith('api/'):
        from flask import abort
        abort(404)
    
    # Check if it's a static file that exists
    static_file_path = os.path.join(app.static_folder, path)
    if os.path.isfile(static_file_path):
        return send_from_directory(app.static_folder, path)
    
    # For all other routes (like /admin/access), serve the React app
    return send_from_directory(app.static_folder, 'index.html')

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint to verify the server is running"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    """Endpoint to collect user feedback"""
    try:
        # Get feedback data from request
        feedback_data = request.json
        
        # Add timestamp
        feedback_data['timestamp'] = datetime.now().isoformat()
        
        # For testing: store feedback locally
        # In production, you'd want to store this in a database
        feedback_dir = os.path.join(os.path.dirname(__file__), 'feedback')
        os.makedirs(feedback_dir, exist_ok=True)
        
        # Create a unique filename
        filename = f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(feedback_dir, filename)
        
        # Write feedback to file
        with open(filepath, 'w') as f:
            json.dump(feedback_data, f, indent=2)
            
        return jsonify({"status": "success", "message": "Feedback received. Thank you!"})
    
    except Exception as e:
        logger.error(f"Error processing feedback: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to process feedback"}), 500

# Function to encode the image to base64
def encode_image(image_file):
    return base64.b64encode(image_file.read()).decode('utf-8')

# Endpoint to handle image analysis
@app.route("/analyze-image", methods=["POST"])
@rate_limit
@sanitize_input
def analyze_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    image = request.files['image']
    hashtags = request.form.get('hashtags', '').strip()
    
    # Check if there are specific product mentions in hashtags
    product_queries = []
    if hashtags:
        # Extract potential product mentions from hashtags
        product_terms = re.findall(r'#(\w+)', hashtags)
        if product_terms:
            product_queries = [term for term in product_terms if len(term) > 3]  # Filter out short terms

    try:
        # Determine the image content type
        content_type = image.content_type
        if not content_type or content_type not in ['image/jpeg', 'image/png']:
            # Default to JPEG if content type is not specified or not supported
            content_type = 'image/jpeg'
            logger.info(f"Using default content type: {content_type}")
        else:
            logger.info(f"Detected image content type: {content_type}")
        
        # Save the image to storage
        # First, we need to rewind the file pointer to the beginning
        image.seek(0)
        storage_result = storage_instance.upload_file(image, image.filename, directory='photos')
        if storage_result:
            logger.info(f"Image saved to storage: {storage_result}")
        
        # Rewind the file pointer again for base64 encoding
        image.seek(0)
        # Encode the image to base64
        base64_image = encode_image(image)

        headers = {
            "Content-Type": "application/json",
            "x-api-key": anthropic_api_key,
            "anthropic-version": "2023-06-01"
        }

        # Create prompt for image captioning
        prompt = """As a building envelope specialist, analyze this construction photo with extreme precision:

1. IDENTIFICATION
- First identify the main building component(s) visible in the image
- Confirm any specific materials or assemblies you can clearly see
- Note the perspective and viewing angle of the photo
- Please carefully reference the exact annotations in the image.

2. DESCRIPTION REQUIREMENTS
- Priority order: 1) Verbatim annotation text, 2) Visual context, 3) General knowledge
- Describe only what is definitively visible in the image
- Use industry-standard terminology for materials and components
- Note spatial relationships between components
- Mention any visible measurements or scale references
- Note any visible damage or defects

3. FORMAT
- Provide a 1-2 sentence technical description
- Use clear, precise language
- Focus on factual observations only

4. QUALITY CHECK
- Verify that each element mentioned is clearly visible in the image
- Double-check terminology accuracy
- Ensure description matches what you can see with high confidence"""

        # Add hashtags to the prompt if provided
        if hashtags:
            prompt += f"\n\nAdditional context from hashtags: {hashtags}\n\nUse these hashtags (name of building material) to help identify and describe the key elements in the image more accurately. The response should include the name of the building material in the hashtags."

        # Add product information from RAG if available
        product_info = ""
        if product_queries:
            all_product_results = []
            for query in product_queries:
                results = rag_service_instance.query_product_data(query, k=1)
                if results:
                    all_product_results.extend(results)
            
            if all_product_results:
                product_info = "\n\nRELEVANT PRODUCT INFORMATION:\n"
                for i, result in enumerate(all_product_results[:2]):  # Limit to 2 product references
                    source = os.path.basename(result.get("source", "Unknown"))
                    content = result.get("content", "")
                    
                    # Extract the most relevant parts (first 300 chars)
                    content_summary = content[:300] + "..." if len(content) > 300 else content
                    product_info += f"Product {i+1}: {source}\n{content_summary}\n\n"
        
        if product_info:
            prompt += product_info
            prompt += "\nRefer to this product information when it's relevant to what you can see in the image."

        prompt += "\n\nProvide only the captions in the following format:\nWrite a concise caption (1-2 sentences) describing the visual elements of the building envelope in the photo."

        # Requesting Anthropic API
        payload = {
            "model": "claude-3-7-sonnet-20250219",
            "max_tokens": 10000,
            "temperature": 1,
            "system": "You are an architectural engineer who is an expert in construction materials, installation best practices, and construction QA/QC.",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": content_type,
                                "data": base64_image
                            }
                        }
                    ]
                }
            ]
        }

        # Send the request to Anthropic API
        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)

        # Return the generated description or error
        if response.status_code == 200:
            data = response.json()
            description = data['content'][0]['text']  # Get the caption from Anthropic's response
            logger.info("Successfully generated caption using Anthropic API")
            
            # Include the storage info in the response if available
            result = {"description": description}
            if storage_result:
                result["storage_info"] = storage_result
                
            return jsonify(result)
        else:
            logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
            return jsonify({"error": response.text}), response.status_code

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# New endpoint to summarize captions using Anthropic's Claude
@app.route("/summarize-captions", methods=["POST"])
@rate_limit
@sanitize_input
def summarize_captions():
    data = request.json
    
    if not data or 'captions' not in data or not data['captions']:
        return jsonify({"error": "No captions provided"}), 400
    
    captions = data['captions']
    
    try:
        # Format captions as a string, with each caption on a new line
        formatted_captions = "\n".join(captions)
        
        # Prepare the prompt for Claude
        prompt = f"""You will be provided with a set of captions describing observations made on construction sites. Your task is to write a comprehensive report based on these captions. The report should include three main sections: a summary of observations, a discussion of implications, and recommendations based on the findings.

Here are the captions:
<captions>
{formatted_captions}
</captions>

Please follow these steps to create your report:

1. Summarize Observations:
   - Carefully read through all the provided captions.
   - Identify the key observations.
   - Organize these observations into two lists: building envelope related and others.
   - Present the summary list in a clear and concise manner.

2. Discuss Implications:
   - Analyze the observations and consider their potential impacts from a construction quality perspective.
   - Identify any trends, patterns, or significant findings that may adversely affect the performance of the building.
   - Discuss the implications of these observations as an industry professional.
   - Consider both short-term and long-term effects.

3. Provide action items/recommendations:
   - Based on the observations and implications, develop actionable recommendations.
   - Ensure your recommendations are specific, practical, and relevant.
   - The recommendations should focus on high priority issues that need to be addressed immediately in regards to the building envelope.

Format your report using the following structure:

<summary_of_observations>
[Insert your summary list of observations here]
</summary_of_observations>

<discussion>
[Insert your discussion of implications here]
</discussion>

<recommendations>
[Insert your recommendations here]
</recommendations>

Do not include any section headers or titles.  

Ensure that your report is well-structured, logically organized, and written in a professional tone. Use clear and concise language throughout. If you need to make any assumptions or inferences beyond the provided captions, clearly state them as such."""

        headers = {
            "Content-Type": "application/json",
            "x-api-key": anthropic_api_key,
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": "claude-3-7-sonnet-20250219",
            "max_tokens": 10000,
            "temperature": 1,
            "system": "You are a professional architectural engineer who is an expert in construction engineering, administration, and quality control.",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        # Send the request to Anthropic API
        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            summary = data['content'][0]['text']
            return jsonify({"summary": summary})
        else:
            logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
            return jsonify({"error": response.text}), response.status_code
            
    except Exception as e:
        logger.error(f"Error summarizing captions: {str(e)}")
        return jsonify({"error": str(e)}), 500

# New endpoint to generate PDF report
@app.route("/generate-report", methods=["POST"])
@rate_limit
@sanitize_input
def generate_pdf_report_endpoint():
    try:
        # Get form data
        data = request.json
        if not data:
            return jsonify({"error": "No report data provided"}), 400
        
        logger.info("Received report data for PDF generation")
        
        # Use our enhanced PDF generator
        try:
            # Use the improved FPDF generator from generate_pdf.py
            pdf_buffer = generate_pdf_report(data)
            
            # Save the PDF to storage if we have a storage instance
            storage_result = None
            report_number = data.get('reportNumber', 'report')
            filename = f"Site_Visit_Report_{report_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            try:
                # Save the PDF to storage
                pdf_buffer.seek(0)  # Reset buffer position to beginning
                storage_result = storage_instance.upload_file(pdf_buffer, filename, directory='reports')
                if storage_result:
                    logger.info(f"PDF saved to storage: {storage_result}")
            except Exception as storage_error:
                logger.error(f"Error saving PDF to storage: {str(storage_error)}")
            
            # Reset buffer position for sending as response
            pdf_buffer.seek(0)
            
            # Create the download response
            response = send_file(
                pdf_buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
            
            return response
            
        except Exception as pdf_error:
            logger.error(f"Error using enhanced PDF generator: {str(pdf_error)}")
            logger.error(traceback.format_exc())
            
            # Fall back to the original reportlab generator
            logger.info("Falling back to ReportLab PDF generator")
            return _generate_pdf_using_reportlab(data)
            
    except Exception as e:
        # Get detailed error information
        exc_type, exc_obj, exc_tb = sys.exc_info()
        tb_details = traceback.format_exc()
        
        logger.error(f"Error generating PDF: {str(e)}")
        logger.error(f"Error type: {exc_type}, Traceback: {tb_details}")
        
        return jsonify({"error": str(e)}), 500

# Rename the original function to use as fallback
def _generate_pdf_using_reportlab(data):
    pdf_filename = None
    try:
        # Extract report data
        project_name = data.get('projectName', 'Unknown Project')
        report_number = data.get('reportNumber', '')
        subject = data.get('subject', '')
        description = data.get('description', '')
        action = data.get('action', '')
        image_data = data.get('images', [])
        
        logger.info(f"Processing report for {project_name} with {len(image_data)} images")
        
        # Create a temporary file to store the PDF
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf_filename = temp_file.name
        temp_file.close()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            pdf_filename,
            pagesize=letter,
            rightMargin=72, leftMargin=72,
            topMargin=72, bottomMargin=72
        )
        
        # Create styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        title_style.alignment = 1  # Center alignment
        
        heading_style = ParagraphStyle(
            'CustomHeading2',
            parent=styles['Heading2'],
            spaceBefore=12,
            spaceAfter=6,
            keepWithNext=True,
            fontSize=14
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            spaceBefore=6,
            spaceAfter=6,
            leading=14  # Line spacing
        )
        
        # Custom styles
        header_style = ParagraphStyle(
            'Header',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.gray
        )
        
        # Style for formatted content with proper spacing and bullet handling
        formatted_style = ParagraphStyle(
            'Formatted',
            parent=normal_style,
            spaceAfter=6,
            spaceBefore=6,
            bulletIndent=20,
            leftIndent=20
        )
        
        # Style specifically for list items with better indentation and spacing
        list_style = ParagraphStyle(
            'ListItem',
            parent=normal_style,
            leftIndent=36,
            firstLineIndent=-18,
            spaceBefore=3,
            spaceAfter=3,
            leading=14
        )
        
        # Style for sub-lists with additional indentation
        sublist_style = ParagraphStyle(
            'SubListItem',
            parent=list_style,
            leftIndent=72,  # Increased from 54 to 72 for better nesting
            firstLineIndent=-18,
            spaceBefore=3,
            spaceAfter=3,
            bulletIndent=12
        )
        
        # Build content
        content = []
        
        # Report header
        date_str = datetime.now().strftime('%B %d, %Y')
        content.append(Paragraph(f"Site Visit Report - {date_str}", title_style))
        content.append(Spacer(1, 0.25*inch))
        
        # Project details
        content.append(Paragraph(f"<b>Project:</b> {project_name}", normal_style))
        content.append(Paragraph(f"<b>Report Number:</b> {report_number}", normal_style))
        content.append(Paragraph(f"<b>Subject:</b> {subject}", normal_style))
        content.append(Spacer(1, 0.25*inch))
        
        # Observations
        content.append(Paragraph("Observations", heading_style))
        
        # Process description - convert markdown to HTML tags that ReportLab can handle
        if description:
            # Replace markdown headers with HTML equivalents
            description = re.sub(r'^#\s+(.+)$', r'<font size="14"><b>\1</b></font>', description, flags=re.MULTILINE)
            description = re.sub(r'^##\s+(.+)$', r'<font size="12"><b>\1</b></font>', description, flags=re.MULTILINE)
            description = re.sub(r'^###\s+(.+)$', r'<font size="11"><b>\1</b></font>', description, flags=re.MULTILINE)
            
            # Replace bold text
            description = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', description)
            
            # First check if we have a "Title: 1. Item 2. Item..." pattern and reformat it
            # Use a more flexible pattern to match different variations of the format
            sections_with_numbered_items = re.findall(r'([A-Za-z][^:]+?):\s+((?:\d+\.\s+[^.0-9\n].*?(?:\n|$))(?:\d+\.\s+[^.0-9\n].*?(?:\n|$))*)', description, re.DOTALL)
            description_modified = description
            
            # Flag to track if we processed any sections with this pattern
            processed_sections = False
            
            # Process sections with "Title: 1. Item..." format
            for section_title, numbered_items in sections_with_numbered_items:
                processed_sections = True
                # Extract the original text to replace
                original_text = f"{section_title}: {numbered_items}"
                
                # Format the section title as bold
                formatted_title = f"<b>{section_title.strip()}:</b>"
                
                # Extract the individual numbered items - use a more robust regex to handle multi-line items
                items = re.findall(r'(\d+)\.\s+(.*?)(?=\n\d+\.|$)', numbered_items.strip(), re.DOTALL)
                
                # If we didn't capture any items, try a different pattern (for single-line items)
                if not items:
                    items = re.findall(r'(\d+)\.\s+(.*?)(?=\s+\d+\.|$)', numbered_items.strip())
                
                # Replace the original text with our formatted version in the modified description
                # (for future processing of other content)
                description_modified = description_modified.replace(original_text, "")
                
                # Add the section title as a separate paragraph
                content.append(Paragraph(formatted_title, normal_style))
                content.append(Spacer(1, 0.05*inch))  # Small space after the title
                
                # Add each numbered item as a separate list item with proper formatting
                for number, item_text in items:
                    # Clean up the item text (remove extra whitespace, newlines)
                    cleaned_text = re.sub(r'\s+', ' ', item_text.strip())
                    list_para = Paragraph(f"{number}. {cleaned_text}", list_style)
                    content.append(list_para)
                
                # Add spacing after the list
                content.append(Spacer(1, 0.1*inch))
            
            # If no special pattern was found or if there's remaining content, process it as regular paragraphs
            if not processed_sections or description_modified.strip():
                # Process remaining text or original text if no patterns matched
                remaining_text = description_modified if processed_sections else description
                
                # Split into paragraphs
                paragraphs = remaining_text.split('\n\n')
                
                for para in paragraphs:
                    if not para.strip():
                        continue
                        
                    # Regular paragraph - add directly to content
                    content.append(Paragraph(para.strip(), normal_style))
                    content.append(Spacer(1, 0.1*inch))
        else:
            # If no description was provided
            content.append(Paragraph("No observations provided.", normal_style))
            
        content.append(Spacer(1, 0.15*inch))
        
        # Action Items
        if action:
            content.append(Paragraph("Action Items", heading_style))
            
            # Process action text - convert markdown to HTML tags
            # Replace markdown headers with HTML equivalents
            action = re.sub(r'^#\s+(.+)$', r'<font size="14"><b>\1</b></font>', action, flags=re.MULTILINE)
            action = re.sub(r'^##\s+(.+)$', r'<font size="12"><b>\1</b></font>', action, flags=re.MULTILINE)
            action = re.sub(r'^###\s+(.+)$', r'<font size="11"><b>\1</b></font>', action, flags=re.MULTILINE)
            
            # Replace bold text
            action = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', action)
            
            # Process the text paragraph by paragraph
            paragraphs = action.split('\n\n')
            
            for para in paragraphs:
                if not para.strip():
                    continue
                
                # Check if this is a bulleted list or sub-list
                if re.match(r'^[ \t]*[-*][ \t]', para.strip()):
                    # Process bulleted lists
                    list_items = para.strip().split('\n')
                    for item in list_items:
                        if re.match(r'^[ \t]*[-*][ \t]', item.strip()):
                            # Determine indentation level by counting leading spaces
                            indent_level = len(item) - len(item.lstrip())
                            text = re.sub(r'^[ \t]*[-*][ \t]', '', item.strip())
                            
                            # Use appropriate style based on indentation
                            if indent_level > 2:
                                list_para = Paragraph(f"• {text}", sublist_style)
                            else:
                                list_para = Paragraph(f"• {text}", list_style)
                            content.append(list_para)
                
                # Check if this is a numbered list
                elif re.match(r'^\d+\.[ \t]', para.strip()):
                    # Process numbered lists by creating separate paragraphs with proper indentation
                    list_items = para.strip().split('\n')
                    in_sublist = False
                    current_number = None
                    
                    for i, item in enumerate(list_items):
                        # Check if this is a main numbered item
                        if re.match(r'^\d+\.[ \t]', item.strip()):
                            in_sublist = False
                            # Extract the number and text
                            match = re.match(r'^(\d+)\.?\s+(.+)$', item.strip())
                            if match:
                                current_number = match.group(1)
                                text = match.group(2)
                                # Create a properly formatted list item
                                list_para = Paragraph(f"{current_number}. {text}", list_style)
                                content.append(list_para)
                        # Check if this is a sub-item (indented with spaces or dash)
                        elif item.strip().startswith('-') or item.strip().startswith('*'):
                            # Sub-item with bullet
                            in_sublist = True
                            text = re.sub(r'^[-*]\s+', '', item.strip())
                            sublist_para = Paragraph(f"• {text}", sublist_style)
                            content.append(sublist_para)
                        elif item.strip() and in_sublist:
                            # Continuation of previous sub-item or additional text
                            text = item.strip()
                            sublist_para = Paragraph(text, sublist_style)
                            content.append(sublist_para)
                        elif item.strip():
                            # Text associated with the numbered item but not a bullet point
                            indent_level = len(item) - len(item.lstrip())
                            if indent_level >= 2:
                                # This is indented text under a numbered item
                                text = item.strip()
                                sub_para = Paragraph(text, sublist_style)
                                content.append(sub_para)
                            else:
                                # Regular continuation text
                                text = item.strip()
                                para_text = Paragraph(text, normal_style)
                                content.append(para_text)
                    
                    # Add extra spacing after the list
                    content.append(Spacer(1, 0.1*inch))
            
            content.append(Spacer(1, 0.15*inch))
        
        # Images section
        if image_data:
            content.append(Paragraph("Site Photographs", heading_style))
            content.append(Spacer(1, 0.1*inch))
            
            # Keep track of all temporary files to clean up at the end
            temp_files = []
            
            processed_images = 0
            for idx, img_info in enumerate(image_data):
                if 'dataUrl' in img_info and img_info['dataUrl'] and isinstance(img_info['dataUrl'], str):
                    temp_img_name = None
                    validated_img_name = None
                    
                    try:
                        logger.info(f"Processing image {idx+1}")
                        
                        # Skip if dataUrl is empty or invalid
                        if not img_info['dataUrl'].startswith('data:'):
                            logger.warning(f"Invalid image data URL for image {idx+1}, skipping. URL starts with: {img_info['dataUrl'][:20]}...")
                            continue
                        
                        # Find the base64 part after the comma
                        if ',' not in img_info['dataUrl']:
                            logger.warning(f"Invalid data URL format for image {idx+1}, missing comma separator")
                            continue
                            
                        # Extract base64 data
                        try:
                            base64_data = img_info['dataUrl'].split(',')[1]
                            img_bytes = base64.b64decode(base64_data)
                        except Exception as decode_error:
                            logger.error(f"Error decoding base64 for image {idx+1}: {str(decode_error)}")
                            continue
                        
                        # Create a temporary image file
                        temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                        temp_img_name = temp_img.name
                        temp_img.write(img_bytes)
                        temp_img.close()
                        temp_files.append(temp_img_name)
                        
                        logger.info(f"Temp file created at {temp_img_name} with size {os.path.getsize(temp_img_name)}")
                        
                        # Open with PIL first to validate the image
                        try:
                            pil_image = PILImage.open(temp_img_name)
                        except Exception as pil_error:
                            logger.error(f"PIL could not open image {idx+1}: {str(pil_error)}")
                            continue
                        
                        # Create a new validated image file
                        validated_img = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                        validated_img_name = validated_img.name
                        validated_img.close()
                        temp_files.append(validated_img_name)
                        
                        # Save as JPEG for consistency
                        try:
                            if pil_image.mode != 'RGB':
                                pil_image = pil_image.convert('RGB')
                            
                            pil_image.save(validated_img_name, format='JPEG')
                            logger.info(f"Validated file created at {validated_img_name} with size {os.path.getsize(validated_img_name)}")
                        except Exception as save_error:
                            logger.error(f"Error saving image {idx+1}: {str(save_error)}")
                            continue
                        
                        # Add image to the report
                        img = ReportLabImage(validated_img_name, width=5*inch, height=3.5*inch)
                        content.append(img)
                        processed_images += 1
                        
                        # Add caption
                        if 'caption' in img_info and img_info['caption']:
                            caption_text = f"Photo {idx+1}: {img_info['caption']}"
                            content.append(Paragraph(caption_text, normal_style))
                        
                        content.append(Spacer(1, 0.25*inch))
                        
                    except Exception as img_error:
                        logger.error(f"Error processing image {idx+1}: {str(img_error)}")
                        logger.error(traceback.format_exc())
                        # Add a placeholder text instead of the image
                        content.append(Paragraph(f"[Image {idx+1} could not be processed]", normal_style))
                        if 'caption' in img_info and img_info['caption']:
                            caption_text = f"Photo {idx+1} caption: {img_info['caption']}"
                            content.append(Paragraph(caption_text, normal_style))
                        content.append(Spacer(1, 0.25*inch))
                else:
                    logger.warning(f"No valid dataUrl found for image {idx+1}, skipping")
            
            logger.info(f"Successfully processed {processed_images} out of {len(image_data)} images")
        
        # Build the PDF
        doc.build(content)
        
        # Return the PDF file
        response = send_file(
            pdf_filename,
            as_attachment=True,
            download_name=f"Site_Visit_Report_{report_number}.pdf",
            mimetype='application/pdf'
        )
        
        # Clean up temporary files after the PDF is generated and sent
        @response.call_on_close
        def on_close():
            # Clean up the temporary image files
            if 'temp_files' in locals():
                for tmp_file in temp_files:
                    try:
                        if tmp_file and os.path.exists(tmp_file):
                            os.remove(tmp_file)
                    except Exception as cleanup_error:
                        logger.error(f"Error cleaning up temp file {tmp_file}: {str(cleanup_error)}")
            
            # Clean up the PDF file
            if pdf_filename and os.path.exists(pdf_filename):
                try:
                    os.remove(pdf_filename)
                except Exception as cleanup_error:
                    logger.error(f"Error cleaning up PDF file: {str(cleanup_error)}")
        
        return response
        
    except Exception as e:
        # Clean up the file if an error occurs
        if pdf_filename and os.path.exists(pdf_filename):
            try:
                os.remove(pdf_filename)
            except:
                pass
        
        raise e
        
@app.route("/upload-product-data", methods=["POST"])
@rate_limit
@require_api_key
@sanitize_input
def upload_product_data():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    allowed_extensions = {'pdf', 'txt'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return jsonify({"error": "File type not supported. Please upload PDF or TXT files."}), 400
    
    try:
        # Save the file using our storage factory
        file.seek(0)
        storage_result = storage_instance.upload_file(file, file.filename, directory='product-data')
        
        if not storage_result:
            return jsonify({"error": "Failed to save the file to storage."}), 500
        
        # Save the file to the product_data directory for RAG processing
        file.seek(0)
        file_path = os.path.join(rag_service.PRODUCT_DATA_DIR, file.filename)
        file.save(file_path)
        
        # Add to RAG service
        success = rag_service_instance.add_product_data(file_path)
        
        if success:
            return jsonify({
                "message": f"Product data '{file.filename}' uploaded and indexed successfully.",
                "storage_info": storage_result
            }), 200
        else:
            return jsonify({"error": "Failed to process the product data."}), 500
    
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500

@app.route("/list-product-data", methods=["GET"])
def list_product_data():
    try:
        # Get all PDF and TXT files in the product_data directory
        pdf_files = [f for f in os.listdir(rag_service.PRODUCT_DATA_DIR) if f.lower().endswith('.pdf')]
        txt_files = [f for f in os.listdir(rag_service.PRODUCT_DATA_DIR) if f.lower().endswith('.txt')]
        
        all_files = pdf_files + txt_files
        
        return jsonify({
            "files": all_files,
            "count": len(all_files)
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"Error listing product data: {str(e)}"}), 500

@app.route("/delete-product-data/<filename>", methods=["DELETE"])
@require_api_key
def delete_product_data(filename):
    try:
        file_path = os.path.join(rag_service.PRODUCT_DATA_DIR, filename)
        
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found."}), 404
        
        # Delete the file
        os.remove(file_path)
        
        # Rebuild the vector store
        success = rag_service_instance.rebuild_vector_store()
        
        if success:
            return jsonify({"message": f"Product data '{filename}' deleted and index rebuilt successfully."}), 200
        else:
            return jsonify({"error": "File deleted but failed to rebuild the index."}), 500
    
    except Exception as e:
        return jsonify({"error": f"Error deleting product data: {str(e)}"}), 500

@app.route("/query-product-data", methods=["POST"])
@rate_limit
@sanitize_input
def query_product_data():
    data = request.json
    
    if not data or 'query' not in data:
        return jsonify({"error": "No query provided"}), 400
    
    query = data['query']
    k = data.get('k', 3)  # Default to 3 results
    
    try:
        results = rag_service_instance.query_product_data(query, k=k)
        
        return jsonify({
            "query": query,
            "results": results,
            "count": len(results)
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"Error querying product data: {str(e)}"}), 500

# Access Code Management Endpoints

@app.route("/api/access/validate", methods=["POST"])
@rate_limit
@sanitize_input
def validate_access_code():
    """Validate an access code and provide access information"""
    try:
        # Get access code from request
        data = request.json
        if not data or "access_code" not in data:
            return jsonify({"status": "error", "message": "No access code provided"}), 400
            
        access_code = data["access_code"]
        
        # Validate the access code
        result = access_management.validate_access_code(access_code)
        
        if result["valid"]:
            return jsonify({
                "status": "success",
                "message": result["message"],
                "user_name": result["user_name"],
                "access_level": result["access_level"],
                "permissions": result["permissions"],
                "expires_at": result["expires_at"],
                "uses_remaining": result["uses_remaining"]
            })
        else:
            return jsonify({"status": "error", "message": result["message"]}), 401
    
    except Exception as e:
        logger.error(f"Error validating access code: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to validate access code"}), 500

# Admin endpoints for access code management - protected by API key

@app.route("/api/admin/access/create", methods=["POST"])
@require_api_key
@sanitize_input
def create_access_code():
    """Create a new access code for a tester"""
    try:
        # Get data from request
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
            
        # Validate required fields
        required_fields = ["assigned_to", "email"]
        for field in required_fields:
            if field not in data:
                return jsonify({"status": "error", "message": f"Missing required field: {field}"}), 400
                
        # Optional fields with defaults
        expiry_days = data.get("expiry_days", access_management.DEFAULT_EXPIRY_DAYS)
        uses = data.get("uses", access_management.DEFAULT_USES)
        notes = data.get("notes", "")
        access_level = data.get("access_level", "standard")
        
        # Create the access code
        access_code = access_management.create_access_code(
            assigned_to=data["assigned_to"],
            email=data["email"],
            expiry_days=expiry_days,
            uses=uses,
            notes=notes,
            access_level=access_level
        )
        
        if access_code:
            return jsonify({
                "status": "success", 
                "message": "Access code created successfully",
                "access_code": access_code
            })
        else:
            return jsonify({"status": "error", "message": "Failed to create access code"}), 500
    
    except Exception as e:
        logger.error(f"Error creating access code: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to create access code"}), 500

@app.route("/api/admin/access/list", methods=["GET"])
@require_api_key
def list_access_codes():
    """List all access codes with their details"""
    try:
        # Get all access codes
        codes = access_management.list_access_codes()
        
        return jsonify({
            "status": "success", 
            "count": len(codes),
            "access_codes": codes
        })
    
    except Exception as e:
        logger.error(f"Error listing access codes: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to list access codes"}), 500

@app.route("/api/admin/access/disable/<access_code>", methods=["POST"])
@require_api_key
def disable_access_code(access_code):
    """Disable an access code"""
    try:
        # Disable the access code
        success = access_management.disable_access_code(access_code)
        
        if success:
            return jsonify({
                "status": "success", 
                "message": f"Access code {access_code} disabled successfully"
            })
        else:
            return jsonify({
                "status": "error", 
                "message": f"Failed to disable access code {access_code}"
            }), 404
    
    except Exception as e:
        logger.error(f"Error disabling access code: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to disable access code"}), 500

@app.route("/api/admin/access/update/<access_code>", methods=["POST"])
@require_api_key
@sanitize_input
def update_access_code(access_code):
    """Update an access code's properties"""
    try:
        # Get data from request
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No update data provided"}), 400
            
        # Update the access code
        success = access_management.update_access_code(access_code, data)
        
        if success:
            return jsonify({
                "status": "success", 
                "message": f"Access code {access_code} updated successfully"
            })
        else:
            return jsonify({
                "status": "error", 
                "message": f"Failed to update access code {access_code}"
            }), 404
    
    except Exception as e:
        logger.error(f"Error updating access code: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to update access code"}), 500

@app.route("/api/admin/access/logs", methods=["GET"])
@require_api_key
def get_access_logs():
    """Get access logs with optional filtering"""
    try:
        # Get filter parameters from query string
        filters = {}
        for key in ["access_code", "user", "action"]:
            if key in request.args:
                filters[key] = request.args[key]
                
        # Get access logs
        logs = access_management.get_access_logs(filters)
        
        return jsonify({
            "status": "success", 
            "count": len(logs),
            "logs": logs
        })
    
    except Exception as e:
        logger.error(f"Error getting access logs: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to get access logs"}), 500

@app.route("/api/admin/access/stats", methods=["GET"])
@require_api_key
def get_access_stats():
    """Get usage statistics for access codes"""
    try:
        # Get usage statistics
        stats = access_management.get_usage_stats()
        
        return jsonify({
            "status": "success", 
            "stats": stats
        })
    
    except Exception as e:
        logger.error(f"Error getting access stats: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to get access statistics"}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port)