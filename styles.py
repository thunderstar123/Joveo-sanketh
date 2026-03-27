"""
Custom CSS Styles for GitLab Handbook Chatbot
Premium dark theme inspired by GitLab's handbook design.
"""


def get_custom_css():
    """Return custom CSS for the Streamlit app."""
    return """
    <style>
    /* ============================================
       IMPORTS
       ============================================ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ============================================
       ROOT & GLOBAL
       ============================================ */
    :root {
        --gitlab-orange: #FC6D26;
        --gitlab-red: #E24329;
        --gitlab-purple: #6B4FBB;
        --gitlab-dark: #171321;
        --gitlab-darker: #0d0b14;
        --surface-1: #1e1a2e;
        --surface-2: #252036;
        --surface-3: #2d2840;
        --text-primary: #E8E6F0;
        --text-secondary: #A0A0B8;
        --accent-gradient: linear-gradient(135deg, #FC6D26, #E24329, #6B4FBB);
        --glass-bg: rgba(37, 32, 54, 0.7);
        --glass-border: rgba(255, 255, 255, 0.06);
    }

    .stApp {
        background: var(--gitlab-darker) !important;
        font-family: 'Inter', sans-serif !important;
    }

    .stApp > header {
        background: transparent !important;
    }

    /* ============================================
       SIDEBAR
       ============================================ */
    section[data-testid="stSidebar"] {
        background: var(--surface-1) !important;
        border-right: 1px solid var(--glass-border) !important;
    }

    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }

    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {
        color: var(--text-secondary) !important;
        font-size: 0.9rem !important;
    }

    /* ============================================
       MAIN CONTENT AREA
       ============================================ */
    .main .block-container {
        padding-top: 2rem !important;
        max-width: 900px !important;
    }

    /* ============================================
       CHAT MESSAGES
       ============================================ */
    .stChatMessage {
        background: var(--surface-2) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 16px !important;
        padding: 1rem 1.2rem !important;
        margin-bottom: 0.8rem !important;
        backdrop-filter: blur(10px) !important;
    }

    .stChatMessage[data-testid="chat-message-user"] {
        background: linear-gradient(135deg, rgba(252, 109, 38, 0.12), rgba(107, 79, 187, 0.12)) !important;
        border: 1px solid rgba(252, 109, 38, 0.2) !important;
    }

    .stChatMessage p, .stChatMessage li {
        color: var(--text-primary) !important;
        line-height: 1.7 !important;
    }

    .stChatMessage strong {
        color: #FF9B6A !important;
    }

    .stChatMessage a {
        color: var(--gitlab-orange) !important;
        text-decoration: none !important;
        border-bottom: 1px dashed rgba(252, 109, 38, 0.4) !important;
        transition: all 0.2s ease !important;
    }

    .stChatMessage a:hover {
        color: #FF9B6A !important;
        border-bottom-color: #FF9B6A !important;
    }

    .stChatMessage code {
        background: var(--surface-3) !important;
        color: var(--gitlab-orange) !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
    }

    /* ============================================
       CHAT INPUT
       ============================================ */
    .stChatInput {
        border-color: var(--glass-border) !important;
    }

    .stChatInput > div {
        background: var(--surface-2) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 12px !important;
    }

    .stChatInput textarea {
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ============================================
       BUTTONS
       ============================================ */
    .stButton > button {
        background: linear-gradient(135deg, rgba(252, 109, 38, 0.15), rgba(107, 79, 187, 0.15)) !important;
        color: var(--text-primary) !important;
        border: 1px solid rgba(252, 109, 38, 0.3) !important;
        border-radius: 10px !important;
        padding: 0.5rem 1rem !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        font-size: 0.85rem !important;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(252, 109, 38, 0.3), rgba(107, 79, 187, 0.3)) !important;
        border-color: var(--gitlab-orange) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 15px rgba(252, 109, 38, 0.2) !important;
    }

    /* ============================================
       EXPANDERS (Source Citations)
       ============================================ */
    .streamlit-expanderHeader {
        background: var(--surface-3) !important;
        color: var(--text-secondary) !important;
        border-radius: 8px !important;
        font-size: 0.85rem !important;
    }

    .streamlit-expanderContent {
        background: var(--surface-2) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 0 0 8px 8px !important;
    }

    /* ============================================
       HERO HEADER
       ============================================ */
    .hero-header {
        text-align: center;
        padding: 2rem 1rem;
        margin-bottom: 1rem;
    }

    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FC6D26, #E24329, #6B4FBB);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }

    .hero-subtitle {
        color: var(--text-secondary);
        font-size: 1rem;
        font-weight: 400;
        margin-top: 0;
    }

    /* ============================================
       SOURCE CARDS
       ============================================ */
    .source-card {
        background: var(--surface-3);
        border: 1px solid var(--glass-border);
        border-radius: 10px;
        padding: 0.7rem 1rem;
        margin: 0.3rem 0;
        transition: all 0.2s ease;
    }

    .source-card:hover {
        border-color: rgba(252, 109, 38, 0.3);
        background: rgba(252, 109, 38, 0.05);
    }

    .source-section {
        color: var(--gitlab-orange);
        font-weight: 600;
        font-size: 0.85rem;
    }

    .source-link {
        color: var(--text-secondary);
        font-size: 0.78rem;
        text-decoration: none;
    }

    /* ============================================
       CONFIDENCE BADGE
       ============================================ */
    .confidence-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: var(--surface-3);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        color: var(--text-secondary);
        border: 1px solid var(--glass-border);
        margin-top: 0.5rem;
    }

    .confidence-high { border-color: rgba(46, 204, 113, 0.3); color: #2ecc71; }
    .confidence-medium { border-color: rgba(241, 196, 15, 0.3); color: #f1c40f; }
    .confidence-low { border-color: rgba(231, 76, 60, 0.3); color: #e74c3c; }

    /* ============================================
       TOPIC PILLS
       ============================================ */
    .topic-pill {
        display: inline-block;
        background: linear-gradient(135deg, rgba(252, 109, 38, 0.1), rgba(107, 79, 187, 0.1));
        border: 1px solid rgba(252, 109, 38, 0.2);
        border-radius: 20px;
        padding: 6px 14px;
        margin: 3px;
        font-size: 0.8rem;
        color: var(--text-primary);
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .topic-pill:hover {
        background: linear-gradient(135deg, rgba(252, 109, 38, 0.25), rgba(107, 79, 187, 0.25));
        transform: translateY(-1px);
    }

    /* ============================================
       MISC
       ============================================ */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: var(--text-primary) !important;
    }

    .stMarkdown p {
        color: var(--text-secondary) !important;
    }

    div[data-testid="stStatusWidget"] {
        visibility: hidden;
    }

    /* Divider */
    .custom-divider {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(252, 109, 38, 0.3), transparent);
        margin: 1.5rem 0;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: var(--gitlab-darker); }
    ::-webkit-scrollbar-thumb {
        background: var(--surface-3);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover { background: var(--gitlab-orange); }

    /* Spinner */
    .stSpinner > div { color: var(--gitlab-orange) !important; }

    /* ============================================
       MODULE BADGE & SELECTOR
       ============================================ */
    .module-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: linear-gradient(135deg, rgba(252, 109, 38, 0.15), rgba(107, 79, 187, 0.15));
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 500;
        color: var(--gitlab-orange);
        border: 1px solid rgba(252, 109, 38, 0.3);
        letter-spacing: 0.3px;
    }

    /* Selectbox styling for module selector */
    section[data-testid="stSidebar"] .stSelectbox > div > div {
        background: var(--surface-3) !important;
        border: 1px solid rgba(252, 109, 38, 0.25) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
    }

    section[data-testid="stSidebar"] .stSelectbox > div > div:hover {
        border-color: var(--gitlab-orange) !important;
    }
    </style>
    """
