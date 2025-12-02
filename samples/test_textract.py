"""
Task #10: Study Textract AnalyzeDocument API
Sample code để extract text từ PDF documents

Textract APIs:
1. DetectDocumentText - Extract text từ single-page document
2. AnalyzeDocument - Extract text + forms + tables từ single-page
3. StartDocumentTextDetection - Async cho multi-page PDF (S3)
4. StartDocumentAnalysis - Async với forms/tables cho multi-page PDF (S3)

Pricing (ap-southeast-1):
- DetectDocumentText: $1.50 per 1,000 pages
- AnalyzeDocument: $15 per 1,000 pages (forms), $15 per 1,000 pages (tables)
"""

import boto3
import json
from pathlib import Path


def extract_text_from_local_image(image_path: str) -> dict:
    """
    Extract text từ local image file (PNG, JPEG, PDF single page)
    Sử dụng DetectDocumentText API (synchronous)
    
    Giới hạn:
    - Max file size: 5MB
    - Formats: PNG, JPEG, PDF (single page only)
    """
    textract = boto3.client('textract', region_name='ap-southeast-1')
    
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    response = textract.detect_document_text(
        Document={'Bytes': image_bytes}
    )
    
    # Extract all LINE blocks
    lines = []
    for block in response['Blocks']:
        if block['BlockType'] == 'LINE':
            lines.append({
                'text': block['Text'],
                'confidence': block['Confidence'],
                'geometry': block['Geometry']['BoundingBox']
            })
    
    return {
        'full_text': '\n'.join([line['text'] for line in lines]),
        'lines': lines,
        'page_count': 1
    }


def extract_text_from_s3(bucket: str, key: str) -> dict:
    """
    Extract text từ document trong S3
    Sử dụng DetectDocumentText API (synchronous)
    """
    textract = boto3.client('textract', region_name='ap-southeast-1')
    
    response = textract.detect_document_text(
        Document={
            'S3Object': {
                'Bucket': bucket,
                'Name': key
            }
        }
    )
    
    lines = []
    for block in response['Blocks']:
        if block['BlockType'] == 'LINE':
            lines.append(block['Text'])
    
    return {
        'full_text': '\n'.join(lines),
        'line_count': len(lines)
    }


def analyze_document_with_forms_tables(bucket: str, key: str) -> dict:
    """
    Extract text + forms + tables từ document
    Sử dụng AnalyzeDocument API (synchronous, single page)
    
    FeatureTypes:
    - TABLES: Extract table structure
    - FORMS: Extract key-value pairs
    - SIGNATURES: Detect signatures
    - LAYOUT: Detect document layout
    """
    textract = boto3.client('textract', region_name='ap-southeast-1')
    
    response = textract.analyze_document(
        Document={
            'S3Object': {
                'Bucket': bucket,
                'Name': key
            }
        },
        FeatureTypes=['TABLES', 'FORMS']
    )
    
    result = {
        'text_lines': [],
        'key_value_pairs': [],
        'tables': []
    }
    
    # Build block map for relationship lookup
    block_map = {block['Id']: block for block in response['Blocks']}
    
    for block in response['Blocks']:
        if block['BlockType'] == 'LINE':
            result['text_lines'].append(block['Text'])
        
        elif block['BlockType'] == 'KEY_VALUE_SET':
            if 'KEY' in block.get('EntityTypes', []):
                key_text = get_text_from_children(block, block_map)
                value_block = get_value_block(block, block_map)
                value_text = get_text_from_children(value_block, block_map) if value_block else ''
                result['key_value_pairs'].append({
                    'key': key_text,
                    'value': value_text
                })
        
        elif block['BlockType'] == 'TABLE':
            table = extract_table(block, block_map)
            result['tables'].append(table)
    
    return result


def get_text_from_children(block: dict, block_map: dict) -> str:
    """Helper: Get text from child blocks"""
    if not block or 'Relationships' not in block:
        return ''
    
    text_parts = []
    for rel in block['Relationships']:
        if rel['Type'] == 'CHILD':
            for child_id in rel['Ids']:
                child = block_map.get(child_id, {})
                if child.get('BlockType') == 'WORD':
                    text_parts.append(child.get('Text', ''))
    
    return ' '.join(text_parts)


def get_value_block(key_block: dict, block_map: dict) -> dict:
    """Helper: Get VALUE block from KEY block"""
    if 'Relationships' not in key_block:
        return None
    
    for rel in key_block['Relationships']:
        if rel['Type'] == 'VALUE':
            for value_id in rel['Ids']:
                return block_map.get(value_id)
    return None


def extract_table(table_block: dict, block_map: dict) -> list:
    """Helper: Extract table as 2D array"""
    rows = {}
    
    if 'Relationships' not in table_block:
        return []
    
    for rel in table_block['Relationships']:
        if rel['Type'] == 'CHILD':
            for cell_id in rel['Ids']:
                cell = block_map.get(cell_id, {})
                if cell.get('BlockType') == 'CELL':
                    row_idx = cell['RowIndex']
                    col_idx = cell['ColumnIndex']
                    cell_text = get_text_from_children(cell, block_map)
                    
                    if row_idx not in rows:
                        rows[row_idx] = {}
                    rows[row_idx][col_idx] = cell_text
    
    # Convert to 2D array
    table = []
    for row_idx in sorted(rows.keys()):
        row = []
        for col_idx in sorted(rows[row_idx].keys()):
            row.append(rows[row_idx][col_idx])
        table.append(row)
    
    return table


def start_async_text_detection(bucket: str, key: str) -> str:
    """
    Start async text detection cho multi-page PDF
    Returns JobId để poll kết quả
    
    Sử dụng cho PDF > 1 page hoặc file lớn
    """
    textract = boto3.client('textract', region_name='ap-southeast-1')
    
    response = textract.start_document_text_detection(
        DocumentLocation={
            'S3Object': {
                'Bucket': bucket,
                'Name': key
            }
        }
    )
    
    return response['JobId']


def get_async_job_result(job_id: str) -> dict:
    """
    Get result từ async job
    Poll cho đến khi JobStatus = SUCCEEDED
    """
    textract = boto3.client('textract', region_name='ap-southeast-1')
    
    response = textract.get_document_text_detection(JobId=job_id)
    
    if response['JobStatus'] == 'IN_PROGRESS':
        return {'status': 'IN_PROGRESS', 'message': 'Job still processing...'}
    
    if response['JobStatus'] == 'FAILED':
        return {'status': 'FAILED', 'message': response.get('StatusMessage', 'Unknown error')}
    
    # SUCCEEDED - extract text
    all_lines = []
    
    # Handle pagination
    while True:
        for block in response['Blocks']:
            if block['BlockType'] == 'LINE':
                all_lines.append({
                    'text': block['Text'],
                    'page': block.get('Page', 1)
                })
        
        if 'NextToken' not in response:
            break
        
        response = textract.get_document_text_detection(
            JobId=job_id,
            NextToken=response['NextToken']
        )
    
    return {
        'status': 'SUCCEEDED',
        'lines': all_lines,
        'full_text': '\n'.join([l['text'] for l in all_lines])
    }


# ============ TEST FUNCTIONS ============

def test_with_s3_document():
    """Test với document đã upload lên S3"""
    bucket = 'arc-chatbot-documents-427995028618'
    key = 'test/sample.pdf'  # Upload test file trước
    
    print("Testing DetectDocumentText with S3...")
    result = extract_text_from_s3(bucket, key)
    print(f"Extracted {result['line_count']} lines")
    print(f"Text preview: {result['full_text'][:500]}...")


def test_async_multipage():
    """Test async processing cho multi-page PDF"""
    bucket = 'arc-chatbot-documents-427995028618'
    key = 'test/multipage.pdf'
    
    print("Starting async job...")
    job_id = start_async_text_detection(bucket, key)
    print(f"Job ID: {job_id}")
    
    # Poll for result (trong production dùng SNS notification)
    import time
    while True:
        result = get_async_job_result(job_id)
        if result['status'] != 'IN_PROGRESS':
            break
        print("Still processing...")
        time.sleep(5)
    
    print(f"Final status: {result['status']}")
    if result['status'] == 'SUCCEEDED':
        print(f"Extracted text: {result['full_text'][:500]}...")


if __name__ == '__main__':
    print("=" * 50)
    print("Textract API Study - Task #10")
    print("=" * 50)
    
    # Uncomment để test:
    # test_with_s3_document()
    # test_async_multipage()
    
    print("\nAPI Notes:")
    print("- Sync APIs: Max 5MB, single page PDF/image")
    print("- Async APIs: Multi-page PDF, results via polling or SNS")
    print("- AnalyzeDocument: Thêm $15/1000 pages cho forms/tables")
    print("- VPC Endpoint đã setup: vpce-0d3ddeeca4fad7919")
