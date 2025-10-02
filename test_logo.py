#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'isercom_website.settings')
django.setup()

from backend.email_utils import get_logo_html

def create_test_logo_file():
    try:
        # Get logo HTML
        logo_html = get_logo_html()
        
        print('Logo HTML length:', len(logo_html))
        print('Logo HTML preview (first 200 chars):', logo_html[:200])
        
        # Create simple HTML test file
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Logo Test</title>
</head>
<body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
    <h1>Isercom Clinic Logo Test</h1>
    <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h2>Logo Display Test:</h2>
        {logo_html}
    </div>
    <p>If you see the logo above, the base64 encoding is working correctly.</p>
    <p>If not, there may be an issue with email client compatibility.</p>
</body>
</html>'''
        
        # Save to file
        with open('test_logo.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print('Logo test HTML saved to test_logo.html')
        print('Please open this file in a web browser to test the logo display.')
        
        # Also save just the base64 data to check
        if 'data:image' in logo_html:
            start = logo_html.find('data:image')
            end = logo_html.find('"', start)
            base64_data = logo_html[start:end]
            print('Base64 data length:', len(base64_data))
            print('Base64 starts with:', base64_data[:50] + '...')
        
    except Exception as e:
        print('Error:', str(e))
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_test_logo_file()
