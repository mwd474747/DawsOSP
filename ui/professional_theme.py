"""
Trinity 3.0 Professional Theme
Bloomberg Terminal meets modern fintech design
No icons - pure typography and sophisticated layouts
"""

import streamlit as st
from typing import Dict, Any

class ProfessionalTheme:
    """Professional financial platform theme - expensive, minimal, sophisticated"""
    
    # Color Palette - Deep, sophisticated colors
    COLORS = {
        # Primary palette - Deep navy and charcoal
        'background': '#0A0E27',  # Deep space blue
        'surface': '#0F1629',     # Slightly lighter surface
        'surface_light': '#141B35', # Card backgrounds
        
        # Text hierarchy
        'text_primary': '#E8E9F3',   # Bright white-blue
        'text_secondary': '#A0A4B8',  # Muted gray-blue
        'text_tertiary': '#6B7290',   # Subdued gray
        
        # Accent colors - Subtle but sophisticated
        'accent_primary': '#4A9EFF',   # Bright sky blue
        'accent_success': '#10B981',   # Emerald green
        'accent_warning': '#F59E0B',   # Amber
        'accent_danger': '#EF4444',    # Red
        
        # Data visualization
        'chart_primary': '#4A9EFF',
        'chart_secondary': '#8B5CF6',
        'chart_tertiary': '#10B981',
        'chart_quaternary': '#F59E0B',
        
        # Borders and dividers
        'border': '#1E2740',
        'border_light': '#2A3451',
        
        # Gradients for premium feel
        'gradient_start': '#4A9EFF',
        'gradient_end': '#8B5CF6'
    }
    
    # Typography - Clean, professional hierarchy
    TYPOGRAPHY = {
        'font_family': '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        'font_mono': '"JetBrains Mono", "SF Mono", Monaco, monospace',
        
        # Font sizes
        'size_hero': '3.5rem',      # 56px - Main headlines
        'size_display': '2.5rem',    # 40px - Section headers
        'size_title': '1.875rem',    # 30px - Card titles
        'size_heading': '1.5rem',    # 24px - Subsections
        'size_subheading': '1.25rem', # 20px - Minor headers
        'size_body': '1rem',         # 16px - Body text
        'size_small': '0.875rem',    # 14px - Secondary text
        'size_micro': '0.75rem',     # 12px - Labels
        
        # Font weights
        'weight_light': '300',
        'weight_regular': '400',
        'weight_medium': '500',
        'weight_semibold': '600',
        'weight_bold': '700',
        
        # Letter spacing
        'tracking_tight': '-0.02em',
        'tracking_normal': '0',
        'tracking_wide': '0.02em',
        'tracking_wider': '0.05em',
    }
    
    # Spacing system - Consistent, luxurious spacing
    SPACING = {
        'xs': '0.25rem',   # 4px
        'sm': '0.5rem',    # 8px
        'md': '1rem',      # 16px
        'lg': '1.5rem',    # 24px
        'xl': '2rem',      # 32px
        'xxl': '3rem',     # 48px
        'xxxl': '4rem',    # 64px
    }
    
    @classmethod
    def apply_theme(cls):
        """Apply the professional theme to Streamlit"""
        
        # Main theme CSS
        theme_css = f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
            
            /* Global Styles */
            .stApp {{
                background: linear-gradient(180deg, {cls.COLORS['background']} 0%, {cls.COLORS['surface']} 100%);
                font-family: {cls.TYPOGRAPHY['font_family']};
                color: {cls.COLORS['text_primary']};
            }}
            
            /* Remove default Streamlit branding and sidebar */
            #MainMenu {{visibility: hidden;}}
            footer {{visibility: hidden;}}
            header {{visibility: hidden;}}
            section[data-testid="stSidebar"] {{display: none;}}
            .main .block-container {{max-width: 100%; padding: 2rem 3rem;}}
            
            /* Professional Header */
            .main-header {{
                padding: {cls.SPACING['xl']} 0;
                border-bottom: 1px solid {cls.COLORS['border']};
                margin-bottom: {cls.SPACING['xxl']};
                background: {cls.COLORS['surface']};
            }}
            
            .main-title {{
                font-size: {cls.TYPOGRAPHY['size_hero']};
                font-weight: {cls.TYPOGRAPHY['weight_light']};
                letter-spacing: {cls.TYPOGRAPHY['tracking_tight']};
                background: linear-gradient(135deg, {cls.COLORS['gradient_start']}, {cls.COLORS['gradient_end']});
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin: 0;
                line-height: 1;
            }}
            
            .main-subtitle {{
                font-size: {cls.TYPOGRAPHY['size_body']};
                color: {cls.COLORS['text_secondary']};
                font-weight: {cls.TYPOGRAPHY['weight_regular']};
                letter-spacing: {cls.TYPOGRAPHY['tracking_wider']};
                text-transform: uppercase;
                margin-top: {cls.SPACING['sm']};
            }}
            
            /* Professional Cards */
            .metric-card {{
                background: {cls.COLORS['surface_light']};
                border: 1px solid {cls.COLORS['border']};
                border-radius: 0;  /* Sharp corners for professional look */
                padding: {cls.SPACING['lg']};
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
                overflow: hidden;
            }}
            
            .metric-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 2px;
                background: linear-gradient(90deg, {cls.COLORS['gradient_start']}, {cls.COLORS['gradient_end']});
                transform: translateX(-100%);
                transition: transform 0.3s ease;
            }}
            
            .metric-card:hover::before {{
                transform: translateX(0);
            }}
            
            .metric-card:hover {{
                background: {cls.COLORS['surface']};
                border-color: {cls.COLORS['border_light']};
                transform: translateY(-2px);
            }}
            
            /* Data Tables - Bloomberg Style */
            .data-table {{
                background: {cls.COLORS['surface_light']};
                border: 1px solid {cls.COLORS['border']};
                font-family: {cls.TYPOGRAPHY['font_mono']};
                font-size: {cls.TYPOGRAPHY['size_small']};
            }}
            
            .data-table thead {{
                background: {cls.COLORS['surface']};
                border-bottom: 2px solid {cls.COLORS['border_light']};
            }}
            
            .data-table th {{
                color: {cls.COLORS['text_secondary']};
                font-weight: {cls.TYPOGRAPHY['weight_semibold']};
                letter-spacing: {cls.TYPOGRAPHY['tracking_wide']};
                text-transform: uppercase;
                padding: {cls.SPACING['md']};
            }}
            
            .data-table td {{
                color: {cls.COLORS['text_primary']};
                padding: {cls.SPACING['sm']} {cls.SPACING['md']};
                border-bottom: 1px solid {cls.COLORS['border']};
            }}
            
            /* Professional Buttons */
            .stButton > button {{
                background: transparent;
                border: 1px solid {cls.COLORS['border_light']};
                color: {cls.COLORS['text_primary']};
                font-weight: {cls.TYPOGRAPHY['weight_medium']};
                letter-spacing: {cls.TYPOGRAPHY['tracking_wide']};
                text-transform: uppercase;
                padding: {cls.SPACING['md']} {cls.SPACING['xl']};
                font-size: {cls.TYPOGRAPHY['size_small']};
                transition: all 0.2s ease;
                border-radius: 0;
            }}
            
            .stButton > button:hover {{
                background: {cls.COLORS['surface_light']};
                border-color: {cls.COLORS['accent_primary']};
                color: {cls.COLORS['accent_primary']};
                transform: translateX(2px);
            }}
            
            /* Input Fields - Minimal and Elegant */
            .stTextInput > div > div > input,
            .stSelectbox > div > div > div,
            .stMultiSelect > div > div > div {{
                background: {cls.COLORS['surface']};
                border: 1px solid {cls.COLORS['border']};
                color: {cls.COLORS['text_primary']};
                font-family: {cls.TYPOGRAPHY['font_family']};
                border-radius: 0;
                padding: {cls.SPACING['md']};
            }}
            
            .stTextInput > div > div > input:focus,
            .stSelectbox > div > div > div:focus {{
                border-color: {cls.COLORS['accent_primary']};
                box-shadow: 0 0 0 1px {cls.COLORS['accent_primary']};
            }}
            
            /* Metrics Display */
            div[data-testid="metric-container"] {{
                background: {cls.COLORS['surface_light']};
                border-left: 3px solid {cls.COLORS['accent_primary']};
                padding: {cls.SPACING['lg']};
                border-radius: 0;
            }}
            
            div[data-testid="metric-container"] > div:first-child {{
                color: {cls.COLORS['text_secondary']};
                font-size: {cls.TYPOGRAPHY['size_small']};
                font-weight: {cls.TYPOGRAPHY['weight_medium']};
                letter-spacing: {cls.TYPOGRAPHY['tracking_wider']};
                text-transform: uppercase;
            }}
            
            div[data-testid="metric-container"] > div:nth-child(2) {{
                font-size: {cls.TYPOGRAPHY['size_display']};
                font-weight: {cls.TYPOGRAPHY['weight_light']};
                color: {cls.COLORS['text_primary']};
                font-family: {cls.TYPOGRAPHY['font_mono']};
            }}
            
            /* Sidebar Styling */
            section[data-testid="stSidebar"] {{
                background: {cls.COLORS['background']};
                border-right: 1px solid {cls.COLORS['border']};
            }}
            
            section[data-testid="stSidebar"] .element-container {{
                padding: {cls.SPACING['sm']} 0;
            }}
            
            /* Expander - Clean Accordion Style */
            .streamlit-expanderHeader {{
                background: {cls.COLORS['surface']};
                border: 1px solid {cls.COLORS['border']};
                border-radius: 0;
                color: {cls.COLORS['text_primary']};
                font-weight: {cls.TYPOGRAPHY['weight_medium']};
            }}
            
            .streamlit-expanderHeader:hover {{
                background: {cls.COLORS['surface_light']};
                border-color: {cls.COLORS['border_light']};
            }}
            
            /* Tabs - Minimal Design */
            .stTabs [data-baseweb="tab-list"] {{
                gap: {cls.SPACING['md']};
                border-bottom: 1px solid {cls.COLORS['border']};
            }}
            
            .stTabs [data-baseweb="tab"] {{
                height: auto;
                background: transparent;
                border: none;
                color: {cls.COLORS['text_secondary']};
                font-weight: {cls.TYPOGRAPHY['weight_medium']};
                letter-spacing: {cls.TYPOGRAPHY['tracking_wide']};
                text-transform: uppercase;
                font-size: {cls.TYPOGRAPHY['size_small']};
                padding: {cls.SPACING['md']} {cls.SPACING['lg']};
            }}
            
            .stTabs [aria-selected="true"] {{
                color: {cls.COLORS['accent_primary']};
                border-bottom: 2px solid {cls.COLORS['accent_primary']};
            }}
            
            /* Professional Dividers */
            hr {{
                border: none;
                border-top: 1px solid {cls.COLORS['border']};
                margin: {cls.SPACING['xl']} 0;
            }}
            
            /* Code Blocks - Terminal Style */
            .stCodeBlock {{
                background: {cls.COLORS['background']};
                border: 1px solid {cls.COLORS['border']};
                border-radius: 0;
            }}
            
            /* Tooltips */
            div[role="tooltip"] {{
                background: {cls.COLORS['surface']};
                border: 1px solid {cls.COLORS['border_light']};
                color: {cls.COLORS['text_primary']};
                font-size: {cls.TYPOGRAPHY['size_small']};
                border-radius: 0;
            }}
            
            /* Success/Error Messages */
            .stSuccess {{
                background: rgba(16, 185, 129, 0.1);
                border-left: 3px solid {cls.COLORS['accent_success']};
                color: {cls.COLORS['accent_success']};
                border-radius: 0;
            }}
            
            .stError {{
                background: rgba(239, 68, 68, 0.1);
                border-left: 3px solid {cls.COLORS['accent_danger']};
                color: {cls.COLORS['accent_danger']};
                border-radius: 0;
            }}
            
            /* Loading States */
            .stProgress > div > div > div {{
                background: {cls.COLORS['accent_primary']};
            }}
            
            /* Custom Scrollbar */
            ::-webkit-scrollbar {{
                width: 8px;
                height: 8px;
            }}
            
            ::-webkit-scrollbar-track {{
                background: {cls.COLORS['background']};
            }}
            
            ::-webkit-scrollbar-thumb {{
                background: {cls.COLORS['border_light']};
                border-radius: 0;
            }}
            
            ::-webkit-scrollbar-thumb:hover {{
                background: {cls.COLORS['accent_primary']};
            }}
        </style>
        """
        
        st.markdown(theme_css, unsafe_allow_html=True)
    
    @classmethod
    def render_header(cls, title: str = "DawsOS", subtitle: str = "Professional Financial Intelligence Platform"):
        """Render professional header with modern gradient banner"""
        # Use Streamlit columns for better layout control
        st.markdown("""
        <style>
            .stApp > header {display: none}
            .main .block-container {padding-top: 0;}
        </style>
        """, unsafe_allow_html=True)
        
        # Create gradient background container
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #f5576c 75%, #4facfe 100%); 
                    padding: 2rem; margin: -4rem -4rem 2rem -4rem; border-radius: 0 0 20px 20px;'>
            <div style='background: rgba(10, 14, 39, 0.95); border-radius: 15px; padding: 2rem; 
                        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);'>
                <div style='display: flex; align-items: center; justify-content: space-between;'>
                    <div>
                        <h1 style='font-size: 3.5rem; font-weight: 200; margin: 0; color: #ffffff;'>
                            {title}
                        </h1>
                        <p style='font-size: 1rem; color: #a0a4b8; margin: 0.5rem 0 0 0; 
                                  letter-spacing: 0.1em; text-transform: uppercase;'>
                            {subtitle}
                        </p>
                    </div>
                    <div style='display: flex; gap: 1rem;'>
                        <span style='padding: 0.5rem 1rem; background: rgba(16, 185, 129, 0.2); 
                                     border: 1px solid #10B981; border-radius: 8px; color: #10B981; 
                                     font-size: 0.875rem;'>● LIVE</span>
                        <span style='padding: 0.5rem 1rem; background: rgba(74, 158, 255, 0.2); 
                                     border: 1px solid #4A9EFF; border-radius: 8px; color: #4A9EFF; 
                                     font-size: 0.875rem;'>v3.0</span>
                    </div>
                </div>
                <hr style='margin: 1.5rem 0; border: 0; height: 1px; background: rgba(255, 255, 255, 0.1);'>
                <div style='display: flex; gap: 2rem; font-size: 0.875rem;'>
                    <span style='color: #6b7290;'>MARKET <span style='color: #10B981;'>● OPEN</span></span>
                    <span style='color: #6b7290;'>DATA <span style='color: #10B981;'>● CONNECTED</span></span>
                    <span style='color: #6b7290;'>UPDATE <span style='color: #e8e9f3;'>REAL-TIME</span></span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @classmethod
    def render_metric_card(cls, label: str, value: Any, delta: Any = None, color: str = None):
        """Render a professional metric card"""
        delta_html = ""
        if delta is not None:
            delta_color = cls.COLORS['accent_success'] if delta > 0 else cls.COLORS['accent_danger']
            delta_symbol = "↑" if delta > 0 else "↓"
            delta_html = f'<div style="color: {delta_color}; font-size: {cls.TYPOGRAPHY["size_small"]};">{delta_symbol} {abs(delta):.2f}%</div>'
        
        value_color = color or cls.COLORS['text_primary']
        
        card_html = f"""
        <div class="metric-card">
            <div style="color: {cls.COLORS['text_secondary']}; font-size: {cls.TYPOGRAPHY['size_micro']}; font-weight: {cls.TYPOGRAPHY['weight_medium']}; letter-spacing: {cls.TYPOGRAPHY['tracking_wider']}; text-transform: uppercase; margin-bottom: {cls.SPACING['sm']};">
                {label}
            </div>
            <div style="font-size: {cls.TYPOGRAPHY['size_title']}; font-weight: {cls.TYPOGRAPHY['weight_light']}; color: {value_color}; font-family: {cls.TYPOGRAPHY['font_mono']};">
                {value}
            </div>
            {delta_html}
        </div>
        """
        
        st.markdown(card_html, unsafe_allow_html=True)
    
    @classmethod
    def render_section_header(cls, title: str, description: str = None):
        """Render a section header with optional description"""
        desc_html = f'<p style="color: {cls.COLORS["text_secondary"]}; font-size: {cls.TYPOGRAPHY["size_body"]}; margin-top: {cls.SPACING["sm"]};">{description}</p>' if description else ""
        
        header_html = f"""
        <div style="margin: {cls.SPACING['xxl']} 0 {cls.SPACING['xl']} 0;">
            <h2 style="font-size: {cls.TYPOGRAPHY['size_display']}; font-weight: {cls.TYPOGRAPHY['weight_light']}; color: {cls.COLORS['text_primary']}; margin: 0;">
                {title}
            </h2>
            {desc_html}
            <div style="width: 60px; height: 2px; background: linear-gradient(90deg, {cls.COLORS['gradient_start']}, {cls.COLORS['gradient_end']}); margin-top: {cls.SPACING['lg']};"></div>
        </div>
        """
        
        st.markdown(header_html, unsafe_allow_html=True)