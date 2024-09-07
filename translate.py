import fitz  # PyMuPDF
from deep_translator import GoogleTranslator

def translate_text(text, src='en', dest='de'):
    """Translate text from source language to destination language using deep_translator."""
    try:
        translator = GoogleTranslator(source=src, target=dest)
        translated_text = translator.translate(text)
        return translated_text if translated_text else ""
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return original text if translation fails

def get_text_dimensions(text, font_size):
    """Estimate the dimensions of the text with the given font size using a standard font."""
    dummy_doc = fitz.open()
    dummy_page = dummy_doc.new_page()
    font_name = "helv"  # Helvetica font available by default
    # Render text into a dummy page
    text_instance = dummy_page.insert_text((0, 0), text, fontsize=font_size, fontname=font_name)
    text_dict = dummy_page.get_text("dict")
    if text_dict['blocks']:
        bbox = text_dict['blocks'][0]['lines'][0]['spans'][0]['bbox']
        dummy_doc.close()
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    else:
        dummy_doc.close()
        return 0, 0  # Return zero dimensions if no text is rendered

def wrap_text(text, font_size, max_width):
    """Wrap text to fit within a given width using a standard font."""
    dummy_doc = fitz.open()
    dummy_page = dummy_doc.new_page()
    font_name = "helv"  # Helvetica font available by default
    lines = []
    current_line = ""
    for word in text.split():
        # Check if adding the word exceeds the width
        test_line = f"{current_line} {word}".strip()
        text_width, _ = get_text_dimensions(test_line, font_size)
        if text_width > max_width:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)
    dummy_doc.close()
    return lines

def translate_pdf(input_pdf_path, output_pdf_path):
    """Translate text in a PDF from English to German, saving as a new file."""
    doc = fitz.open(input_pdf_path)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        
        # Extract text blocks from the original page
        text_blocks = page.get_text("dict")['blocks']
        
        # Collect text and bounding boxes
        text_spans = []
        for block in text_blocks:
            if block['type'] == 0:  # Text block
                for line in block['lines']:
                    for span in line['spans']:
                        text_spans.append((span['text'], fitz.Rect(span['bbox']), span['size'], span['font']))

        # Clear the original text area
        for _, bbox, _, _ in text_spans:
            page.draw_rect(bbox, color=(1, 1, 1), fill=True)
        
        # Insert the translated text
        for text, bbox, size, font in text_spans:
            translated_text = translate_text(text)
            # Wrap text to fit within the bounding box
            wrapped_lines = wrap_text(translated_text, size, bbox.width)
            
            # Get dimensions of original text
            original_text_width, original_text_height = get_text_dimensions(text, size)
            
            if original_text_width == 0 or original_text_height == 0:
                original_text_width = bbox.width
                original_text_height = bbox.height

            # Calculate scaling factor
            scaling_factor = min(bbox.width / original_text_width, bbox.height / original_text_height)
            new_font_size = size * scaling_factor
            
            # Adjust font size if necessary
            while new_font_size > 4:
                text_height = 0
                wrapped_lines = wrap_text(translated_text, new_font_size, bbox.width)
                for line in wrapped_lines:
                    _, line_height = get_text_dimensions(line, new_font_size)
                    text_height += line_height
                if text_height <= bbox.height:
                    break
                new_font_size -= 1
            
            # Position text within the bounding box
            y_offset = bbox.y0 + (bbox.height - text_height) / 2
            for line in wrapped_lines:
                text_width, _ = get_text_dimensions(line, new_font_size)
                x_left = bbox.x0
                page.insert_text((x_left, y_offset), line, fontsize=new_font_size, fontname="helv", color=(0, 0, 0))
                y_offset += get_text_dimensions(line, new_font_size)[1]
        
    # Save the modified PDF to a new file
    doc.save(output_pdf_path)
    doc.close()

# Get file paths from the user
input_pdf = input("Enter the path to the input PDF file: ")
output_pdf = input("Enter the path for the output PDF file: ")

translate_pdf(input_pdf, output_pdf)
