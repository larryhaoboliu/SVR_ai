import os
import io
import base64
import tempfile
from datetime import datetime
from PIL import Image as PILImage
from fpdf import FPDF
import logging
import re

logger = logging.getLogger(__name__)

# Monkey patch FPDF to handle Unicode characters
original_putpages = FPDF._putpages

def patched_putpages(self):
    # Fix encoding issues by replacing Unicode characters that can't be encoded in latin-1
    for i in range(1, len(self.pages) + 1):
        if self.pages.get(i) and hasattr(self.pages[i], 'replace'):
            # Replace problematic characters
            self.pages[i] = self.pages[i].replace('\u2122', '(TM)')  # Trademark symbol
            self.pages[i] = self.pages[i].replace('\u2013', '-')     # En dash
            self.pages[i] = self.pages[i].replace('\u2014', '--')    # Em dash
            self.pages[i] = self.pages[i].replace('\u2018', "'")     # Left single quote
            self.pages[i] = self.pages[i].replace('\u2019', "'")     # Right single quote
            self.pages[i] = self.pages[i].replace('\u201c', '"')     # Left double quote
            self.pages[i] = self.pages[i].replace('\u201d', '"')     # Right double quote
            self.pages[i] = self.pages[i].replace('\u2022', '*')     # Bullet point
            self.pages[i] = self.pages[i].replace('\u00A9', '(C)')   # Copyright symbol
            self.pages[i] = self.pages[i].replace('\u00AE', '(R)')   # Registered trademark
            self.pages[i] = self.pages[i].replace('\u2026', '...')   # Ellipsis
    
    # Call the original method
    original_putpages(self)

# Apply the monkey patch
FPDF._putpages = patched_putpages

class ReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        # Define standard margins (in mm)
        self.left_margin = 20  # Increased for better readability
        self.right_margin = 20
        self.top_margin = 20
        self.bottom_margin = 25  # Increased bottom margin to prevent content in footer
        self.set_margins(self.left_margin, self.top_margin, self.right_margin)
        self.set_auto_page_break(True, margin=self.bottom_margin)
        
        # Define colors
        self.heading_color = (42, 86, 153)  # Professional blue
        self.subheading_color = (70, 130, 180)  # Steel blue
        self.accent_color = (220, 220, 220)  # Light gray
        
        # Flag to track if we need a new page for sections
        self.new_section = False

    def header(self):
        # Save current position
        top = self.get_y()
        
        # Add logo or company name on the left
        self.set_font('Arial', 'B', 20)  # Larger font for better visibility
        self.set_text_color(*self.heading_color)
        self.cell(0, 12, 'Site Visit Report', 0, 1, 'C')
        
        # Add horizontal line
        self.set_line_width(0.8)  # Thicker line
        self.set_draw_color(*self.heading_color)
        self.line(self.left_margin, top + 14, self.w - self.right_margin, top + 14)
        
        # Add date below the line
        self.set_font('Arial', '', 10)
        self.set_text_color(100, 100, 100)  # Dark gray
        self.cell(0, 10, f'Generated: {datetime.now().strftime("%B %d, %Y")}', 0, 1, 'C')
        self.ln(5)
        
        # Reset text color for main content
        self.set_text_color(0, 0, 0)
        
        # If this is a new section page, mark the flag as handled
        if self.new_section:
            self.new_section = False

    def footer(self):
        # Set position at specified distance from bottom
        self.set_y(-self.bottom_margin)
        
        # Add horizontal line
        self.set_line_width(0.5)
        self.set_draw_color(*self.heading_color)
        self.line(self.left_margin, self.get_y() - 2, self.w - self.right_margin, self.get_y() - 2)
        
        # Add page number
        self.set_font('Arial', 'I', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def add_section_title(self, title, new_page=True):
        """Add a formatted section title, optionally starting on a new page"""
        # Start new page if requested
        if new_page:
            # Set flag for new section page
            self.new_section = True
            self.add_page()
        
        self.set_font('Arial', 'B', 14)  # Larger font
        self.set_text_color(*self.heading_color)
        
        # Create a gradient effect
        self.set_fill_color(*self.accent_color)
        self.set_draw_color(*self.heading_color)
        self.set_line_width(0.3)
        
        # Add title with bottom border and subtle background
        self.cell(0, 12, '  ' + title, 'B', 1, 'L', True)
        self.ln(4)  # Additional spacing after title
        
        # Reset text color
        self.set_text_color(0, 0, 0)

    def add_field(self, label, value):
        """Add a formatted field with label and value"""
        # Label with style
        self.set_font('Arial', 'B', 11)
        self.set_text_color(*self.subheading_color)
        self.cell(45, 8, label, 0, 0)
        
        # Value with style
        self.set_text_color(0, 0, 0)
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 8, value)
        self.ln(1)  # Small extra spacing between fields

    def write_styled_text(self, text, is_bold=False, size=11):
        """Write text with given style"""
        style = 'B' if is_bold else ''
        self.set_font('Arial', style, size)
        self.write(7, text)

    def add_formatted_line(self, line):
        """Add a line with proper formatting based on markdown-style markers"""
        if not line.strip():
            self.ln(7)
            return

        # Store initial X position
        x_start = self.get_x()
        
        # Handle leading spaces for indentation
        leading_spaces = len(line) - len(line.lstrip())
        if leading_spaces > 0:
            self.set_x(x_start + (leading_spaces * 2.5))

        # Special handling for header lines
        if line.lstrip().startswith('#'):
            hash_count = len(re.match(r'^#+', line.lstrip()).group())
            text = line.lstrip('#').lstrip()
            
            # Vary size and color based on header level
            size = 16 - hash_count  # H1=15, H2=14, H3=13...
            if hash_count == 1:
                self.set_text_color(*self.heading_color)
            elif hash_count == 2:
                self.set_text_color(*self.subheading_color)
            else:
                self.set_text_color(80, 80, 80)
                
            self.set_font('Arial', 'B', size)
            self.multi_cell(0, 8, text)
            self.set_text_color(0, 0, 0)  # Reset color
            self.ln(3)  # Extra spacing after headers
            return

        # Handle bulleted lists
        if line.lstrip().startswith('- ') or line.lstrip().startswith('* '):
            bullet_indent = 5
            self.set_x(x_start + bullet_indent)
            
            # Use a proper bullet character
            self.set_font('Arial', 'B', 11)
            self.set_text_color(*self.subheading_color)
            self.write(7, '• ')
            
            # Reset color and process the text
            self.set_text_color(0, 0, 0)
            self.set_font('Arial', '', 11)
            text = line.lstrip().lstrip('-*').lstrip()
            self.multi_cell(0, 7, text)
            return

        # Handle numbered lists with better formatting
        number_match = re.match(r'^(\d+\.|\d+\))\s', line.lstrip())
        if number_match:
            indent = 5
            self.set_x(x_start + indent)
            
            # Style the number
            self.set_font('Arial', 'B', 11)
            self.set_text_color(*self.subheading_color)
            self.write(7, number_match.group(1) + ' ')
            
            # Reset color and process the text
            self.set_text_color(0, 0, 0)
            remaining_text = line.lstrip()[len(number_match.group(0)):]
            self.set_font('Arial', '', 11)
            self.multi_cell(0, 7, remaining_text)
            return
        
        # Check if line contains any bold markers
        has_bold_markers = '**' in line
        
        # If no bold markers at all, treat as normal paragraph text
        if not has_bold_markers:
            self.set_font('Arial', '', 11)
            self.multi_cell(0, 7, line)
            return
        
        # Process bold text and regular text
        # Use a more precise pattern to avoid false matches in longer paragraphs
        parts = re.split(r'(\*\*[^*]+?\*\*)', line)
        
        for part in parts:
            if part.startswith('**') and part.endswith('**') and len(part) > 4:  # At least one character between **
                # Bold text with blue color for emphasis
                text = part[2:-2]  # Remove ** markers
                self.set_font('Arial', 'B', 11)
                self.set_text_color(*self.subheading_color)
                self.write(7, text)
                self.set_text_color(0, 0, 0)  # Reset color
            else:
                # Regular text
                self.set_font('Arial', '', 11)
                self.write(7, part)
        
        self.ln(7)

    def add_formatted_text(self, text):
        """Add text with markdown-style formatting"""
        if not text:
            return
            
        # Split text into paragraphs
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                self.ln(7)
                continue
                
            # Process each line in the paragraph
            lines = paragraph.split('\n')
            for line in lines:
                self.add_formatted_line(line.rstrip())
            
            # Add extra space between paragraphs
            self.ln(5)

    def check_page_break(self, height):
        """Check if adding content of given height would cause a page break,
        and add a new page if needed"""
        if self.get_y() + height > self.h - self.bottom_margin:
            self.add_page()
            return True
        return False

def generate_pdf_report(report_data):
    """Generate a PDF report using FPDF"""
    try:
        # Extract data
        project_name = report_data.get('projectName', 'Unknown Project')
        report_number = report_data.get('reportNumber', '')
        subject = report_data.get('subject', '')
        description = report_data.get('description', '')
        action = report_data.get('action', '')
        image_data = report_data.get('images', [])
        
        # Initialize temp_files list
        temp_files = []
        
        logger.info(f"Generating PDF for project: {project_name}")
        
        # Create PDF instance
        pdf = ReportPDF()
        pdf.add_page()
        
        # Project details section - first section doesn't need a new page
        pdf.add_section_title('Project Details', new_page=False)
        pdf.add_field('Project:', project_name)
        pdf.add_field('Report Number:', report_number)
        pdf.add_field('Subject:', subject)
        pdf.ln(8)  # More spacing between sections
        
        # Observations section - starts on a new page
        if description:
            pdf.add_section_title('Site Observations and Discussions', new_page=True)
            pdf.add_formatted_text(description)
            pdf.ln(8)
        
        # Action Items section - starts on a new page
        if action:
            pdf.add_section_title('Action Items', new_page=True)
            pdf.add_formatted_text(action)
            pdf.ln(8)
        
        # Images section - starts on a new page
        if image_data:
            pdf.add_section_title('Site Photos', new_page=True)
            pdf.ln(5)  # Extra space before images
            
            processed_images = 0
            
            for idx, img_info in enumerate(image_data):
                try:
                    if not img_info.get('dataUrl') or not isinstance(img_info['dataUrl'], str) or not img_info['dataUrl'].startswith('data:'):
                        logger.warning(f"Invalid image data for image {idx+1}")
                        continue
                    
                    # Extract base64 data
                    base64_data = img_info['dataUrl'].split(',')[1] if ',' in img_info['dataUrl'] else None
                    if not base64_data:
                        logger.warning(f"Could not extract base64 data for image {idx+1}")
                        continue
                    
                    # Process image
                    try:
                        img_bytes = base64.b64decode(base64_data)
                        
                        # Create temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                            tmp.write(img_bytes)
                            temp_img_path = tmp.name
                            temp_files.append(temp_img_path)
                        
                        # Process with PIL
                        with PILImage.open(temp_img_path) as img:
                            # Convert to RGB if needed
                            if img.mode != 'RGB':
                                img = img.convert('RGB')
                            
                            # Calculate dimensions
                            max_width = 170  # Maximum width in mm - slightly smaller for better margins
                            max_height = 130  # Maximum height in mm
                            
                            # Convert image dimensions to mm (assuming 72 DPI)
                            img_width_mm = (img.width * 25.4) / 72
                            img_height_mm = (img.height * 25.4) / 72
                            
                            # Calculate scaling ratio
                            width_ratio = max_width / img_width_mm
                            height_ratio = max_height / img_height_mm
                            ratio = min(width_ratio, height_ratio)
                            
                            if ratio < 1:
                                new_width = int(img.width * ratio)
                                new_height = int(img.height * ratio)
                                img = img.resize((new_width, new_height), PILImage.LANCZOS)
                            
                            # Enhance image quality
                            processed_path = f"{temp_img_path}_processed.jpg"
                            img.save(processed_path, 'JPEG', quality=90)  # Higher quality
                            temp_files.append(processed_path)
                        
                        # Calculate caption height (approximate)
                        caption_height = 0
                        if 'caption' in img_info and img_info['caption']:
                            caption_text = img_info['caption']
                            # Rough estimate: 5mm per line, with 170mm width allows ~35 chars per line
                            estimated_lines = max(1, len(caption_text) // 35 + (1 if len(caption_text) % 35 > 0 else 0))
                            caption_height = 5 * estimated_lines + 10  # 5mm per line + padding
                        
                        # Calculate total image section height
                        image_height = 120  # The image height
                        total_section_height = 10 + image_height + 8 + caption_height + 15  # Title + image + spacing + caption + spacing
                        
                        # Check if new page is needed with more precise margin calculation
                        if pdf.get_y() + total_section_height > pdf.h - pdf.bottom_margin:
                            pdf.add_page()
                        
                        # Add image number and caption - with styling
                        pdf.set_font('Arial', 'B', 12)
                        pdf.set_text_color(*pdf.subheading_color)
                        pdf.cell(0, 10, f"Photo {idx + 1}", 0, 1)
                        
                        # Add image with border and shadow effect
                        image_x = (pdf.w - 170) / 2  # Center image
                        
                        # Draw a subtle background rectangle for the image
                        current_y = pdf.get_y()
                        pdf.set_fill_color(245, 245, 245)  # Very light gray
                        pdf.set_draw_color(200, 200, 200)  # Medium gray
                        pdf.rect(image_x - 2, current_y - 2, 174, image_height + 4, style='DF')
                        
                        # Add the actual image
                        pdf.image(processed_path, x=image_x, y=current_y, w=170, h=image_height)
                        
                        # Move to position below the image for caption
                        pdf.set_y(current_y + image_height + 6)  # Position after image with spacing
                        
                        # Add caption if available - with improved caption styling
                        if 'caption' in img_info and img_info['caption']:
                            # Add a caption box with light background
                            caption_y = pdf.get_y()
                            pdf.set_fill_color(240, 240, 245)  # Very light blue-gray background
                            pdf.set_draw_color(200, 200, 220)  # Light blue-gray border
                            
                            # Draw caption background and border
                            pdf.rect(image_x - 2, caption_y - 2, 174, caption_height, style='DF')
                            
                            # Add the caption text
                            pdf.set_font('Arial', 'I', 10)
                            pdf.set_text_color(40, 40, 40)  # Darker text for better readability
                            pdf.set_xy(image_x + 4, caption_y)  # Set position inside the box with padding
                            pdf.multi_cell(166, 5, caption_text)  # Width reduced for padding
                            
                            # Move cursor to after the caption
                            pdf.set_y(caption_y + caption_height + 2)
                        
                        # Reset colors
                        pdf.set_text_color(0, 0, 0)
                        
                        # Add a light separator line between images
                        if idx < len(image_data) - 1:  # Don't add after the last image
                            # Check if there's enough space for another image
                            next_img_will_fit = pdf.get_y() + 15 + total_section_height <= pdf.h - pdf.bottom_margin
                            
                            if next_img_will_fit:
                                separator_y = pdf.get_y() + 5
                                pdf.set_draw_color(220, 220, 220)  # Light gray separator
                                pdf.set_line_width(0.2)  # Thin line
                                pdf.line(pdf.left_margin + 20, separator_y, pdf.w - pdf.right_margin - 20, separator_y)
                                pdf.ln(15)  # More space between images
                            else:
                                # Start a new page for the next image
                                pdf.add_page()
                        else:
                            pdf.ln(10)  # Less space after the last image
                        processed_images += 1
                        
                    except Exception as img_proc_error:
                        logger.error(f"Error processing image {idx+1}: {str(img_proc_error)}")
                        pdf.set_font('Arial', '', 10)
                        pdf.set_text_color(200, 0, 0)  # Red color for error
                        pdf.cell(0, 10, f"[Image {idx+1} could not be processed]", 0, 1)
                        pdf.set_text_color(0, 0, 0)  # Reset color
                
                except Exception as general_error:
                    logger.error(f"General error processing image {idx+1}: {str(general_error)}")
            
            logger.info(f"Successfully processed {processed_images} out of {len(image_data)} images")
        
        # Generate PDF
        pdf_buffer = io.BytesIO()
        pdf.output(dest='F', name='temp.pdf')
        
        # Read the temp PDF file into the buffer
        with open('temp.pdf', 'rb') as temp_pdf:
            pdf_buffer.write(temp_pdf.read())
        
        # Clean up the temp PDF file
        try:
            os.remove('temp.pdf')
        except Exception as cleanup_error:
            logger.error(f"Error cleaning up temp PDF file: {str(cleanup_error)}")
            
        pdf_buffer.seek(0)
        
        # Clean up temp files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up temp file {temp_file}: {str(cleanup_error)}")
        
        return pdf_buffer
    
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        raise 