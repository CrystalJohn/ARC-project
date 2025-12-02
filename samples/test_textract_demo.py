"""
Demo test Textract với một image đơn giản
"""
import boto3
from PIL import Image, ImageDraw, ImageFont
import io

def create_test_image():
    """Tạo một image với text để test Textract"""
    # Tạo image trắng
    img = Image.new('RGB', (800, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    # Vẽ text lên image
    text_lines = [
        "Academic Research Chatbot",
        "Document Processing Test",
        "",
        "Name: Nguyen Van A",
        "Student ID: 12345678",
        "Department: Computer Science",
        "",
        "This is a test document for AWS Textract OCR."
    ]
    
    y_position = 30
    for line in text_lines:
        draw.text((50, y_position), line, fill='black')
        y_position += 40
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes.getvalue()


def upload_and_test():
    """Upload test image và chạy Textract"""
    s3 = boto3.client('s3', region_name='ap-southeast-1')
    textract = boto3.client('textract', region_name='ap-southeast-1')
    
    bucket = 'arc-chatbot-documents-427995028618'
    key = 'test/sample_text.png'
    
    # Tạo và upload test image
    print("1. Creating test image...")
    image_bytes = create_test_image()
    
    print(f"2. Uploading to s3://{bucket}/{key}...")
    s3.put_object(Bucket=bucket, Key=key, Body=image_bytes, ContentType='image/png')
    print("   Upload successful!")
    
    # Test Textract
    print("\n3. Calling Textract DetectDocumentText...")
    response = textract.detect_document_text(
        Document={
            'S3Object': {
                'Bucket': bucket,
                'Name': key
            }
        }
    )
    
    # Extract results
    print("\n" + "="*50)
    print("TEXTRACT RESULTS:")
    print("="*50)
    
    lines = []
    for block in response['Blocks']:
        if block['BlockType'] == 'LINE':
            lines.append({
                'text': block['Text'],
                'confidence': round(block['Confidence'], 2)
            })
    
    for i, line in enumerate(lines, 1):
        print(f"{i}. [{line['confidence']}%] {line['text']}")
    
    print("\n" + "="*50)
    print(f"Total lines extracted: {len(lines)}")
    print("="*50)
    
    return lines


if __name__ == '__main__':
    try:
        from PIL import Image, ImageDraw
        upload_and_test()
    except ImportError:
        print("Cần cài Pillow: pip install Pillow")
        print("\nHoặc test trực tiếp với file có sẵn:")
        print("  python -c \"import boto3; print(boto3.client('textract').detect_document_text.__doc__)\"")
