# Fix for main function tabs section
def main():
    """Main application entry point"""
    
    # Initialize services
    initialize_services()
    
    # Professional header
    ProfessionalTheme.render_header(
        "DawsOS",
        "Professional Financial Intelligence Platform"
    )
    
    # API Status indicator
    if hasattr(st.session_state, 'api_status'):
        st.markdown(f"""
        <div style="position: fixed; 
                    top: 10px; 
                    right: 10px; 
                    background: {ProfessionalTheme.COLORS['surface']}; 
                    border: 1px solid {ProfessionalTheme.COLORS['border']}; 
                    padding: 0.5rem 1rem; 
                    font-size: 0.75rem; 
                    color: {ProfessionalTheme.COLORS['text_secondary']}; 
                    z-index: 999;">
            {st.session_state.api_status}
        </div>
        """, unsafe_allow_html=True)
    
    # Main navigation
    tabs = st.tabs([
        "MARKET OVERVIEW",
        "ECONOMIC ANALYSIS",
        "AI TERMINAL",
        "PREDICTIONS",
        "PORTFOLIO"
    ])
    
    with tabs[0]:
        render_market_overview()
    
    with tabs[1]:
        render_economic_dashboard()
    
    with tabs[2]:
        render_ai_chat_interface()
    
    with tabs[3]:
        render_predictions_tracker()
    
    with tabs[4]:
        ProfessionalTheme.render_section_header(
            "Portfolio Analytics",
            "Professional portfolio management and optimization"
        )
        st.info("Portfolio management features coming soon...")

if __name__ == "__main__":
    main()