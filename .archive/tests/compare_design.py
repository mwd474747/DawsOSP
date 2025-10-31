#!/usr/bin/env python3
"""
Compare the design elements between DawsOS and daws-os-draft
"""

import requests
from bs4 import BeautifulSoup

def analyze_design(html_content):
    """Extract key design elements from HTML"""
    design_elements = {
        'gradient': [],
        'colors': [],
        'fonts': [],
        'border_radius': [],
        'shadows': []
    }
    
    # Look for gradient backgrounds
    if 'linear-gradient(135deg, #8b5cf6, #ec4899)' in html_content:
        design_elements['gradient'].append('Purple-Pink main gradient')
    
    # Look for font specifications
    if 'system-ui' in html_content:
        design_elements['fonts'].append('System UI font')
    
    # Look for border radius
    if 'border-radius: 20px' in html_content:
        design_elements['border_radius'].append('20px cards')
    if 'border-radius: 12px' in html_content:
        design_elements['border_radius'].append('12px buttons')
    
    # Look for shadows
    if '0 4px 20px rgba(0,0,0,0.1)' in html_content:
        design_elements['shadows'].append('Subtle card shadows')
    
    # Look for color scheme
    if '#8b5cf6' in html_content:
        design_elements['colors'].append('#8b5cf6 - Purple')
    if '#ec4899' in html_content:
        design_elements['colors'].append('#ec4899 - Pink')
    
    return design_elements

def main():
    # Fetch current DawsOS page
    response = requests.get('http://localhost:5000/')
    current_html = response.text
    
    print("=" * 60)
    print("DESIGN COMPARISON: DawsOS vs daws-os-draft")
    print("=" * 60)
    
    # Expected design from draft site
    print("\n📋 EXPECTED DESIGN (from daws-os-draft):")
    print("-" * 40)
    print("✅ Gradient: Purple (#8b5cf6) to Pink (#ec4899)")
    print("✅ Typography: system-ui font stack")
    print("✅ Cards: 20px border-radius, white background")
    print("✅ Buttons: 12px border-radius, gradient background")
    print("✅ Shadows: 0 4px 20px rgba(0,0,0,0.1)")
    
    # Analyze current implementation
    current_design = analyze_design(current_html)
    
    print("\n🎨 CURRENT IMPLEMENTATION:")
    print("-" * 40)
    
    # Check each design aspect
    checks = {
        'Gradient Background': 'Purple-Pink main gradient' in current_design['gradient'],
        'System Font': 'System UI font' in current_design['fonts'],
        'Card Border Radius': '20px cards' in current_design['border_radius'],
        'Button Border Radius': '12px buttons' in current_design['border_radius'],
        'Card Shadows': 'Subtle card shadows' in current_design['shadows'],
        'Purple Color': '#8b5cf6 - Purple' in current_design['colors'],
        'Pink Color': '#ec4899 - Pink' in current_design['colors']
    }
    
    all_match = True
    for element, present in checks.items():
        status = '✅' if present else '❌'
        if not present:
            all_match = False
        print(f"{status} {element}")
    
    # Visual layout check
    print("\n📐 LAYOUT STRUCTURE:")
    print("-" * 40)
    
    # Check for key structural elements
    has_login_card = 'login-card' in current_html
    has_header = 'DawsOS Portfolio Intelligence' in current_html
    has_gradient_button = 'background: linear-gradient' in current_html and 'Login' in current_html
    
    print(f"{'✅' if has_login_card else '❌'} Login Card Present")
    print(f"{'✅' if has_header else '❌'} Header with Title")
    print(f"{'✅' if has_gradient_button else '❌'} Gradient Login Button")
    
    # Summary
    print("\n" + "=" * 60)
    if all_match:
        print("✨ SUCCESS: Design matches daws-os-draft perfectly!")
        print("All key design elements are properly implemented.")
    else:
        print("⚠️  Some design elements need adjustment")
        print("Please review the missing elements above.")
    print("=" * 60)

if __name__ == "__main__":
    main()