"""
GitLab Assistant — Streamlit App
A premium GenAI chatbot for exploring GitLab's Handbook and Direction.
"""

import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
import os
import subprocess

if not os.path.exists("data/faiss_index"):
    subprocess.run(["python", "scraper.py", "--module", "handbook"])
    subprocess.run(["python", "build_vectorstore.py", "--module", "handbook"])
# Page config (MUST be first Streamlit command)
st.set_page_config(
    page_title="GitLab Assistant",
    page_icon="🦊",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Import custom styles and chatbot
from styles import get_custom_css
from chatbot import HandbookChatbot

# Apply custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)


# ============================================
# MODULE CONFIGURATION
# ============================================
MODULE_CONFIG = {
    "handbook": {
        "label": "📖 Handbook",
        "title": "GitLab Handbook Assistant",
        "subtitle": "Ask me anything about GitLab's values, processes, hiring, engineering, and more.",
        "chat_placeholder": "Ask me about GitLab's handbook...",
        "welcome": """
        **Welcome to the GitLab Handbook Assistant!** 👋

        I can help you explore GitLab's handbook. Here are some things you can ask me:

        - 🏢 **Company & Culture** — "What makes GitLab unique as a company?"
        - 💡 **Values** — "What are GitLab's CREDIT values?"
        - 👥 **Hiring** — "What does GitLab's interview process look like?"
        - ⚙️ **Engineering** — "How is GitLab's engineering team organized?"
        - 🌍 **Remote Work** — "How does GitLab work as a fully remote company?"

        *Try clicking a topic in the sidebar or just type your question below!*
        """,
        "topics": {
            "🏢 Company & Culture": "Tell me about GitLab as a company and its culture",
            "💡 Core Values": "What are GitLab's core values? Explain each one.",
            "🎯 Mission": "What is GitLab's mission statement?",
            "💬 Communication": "How does GitLab handle communication as a remote company?",
            "👥 Hiring Process": "How does GitLab's hiring process work?",
            "🌍 Diversity & Inclusion": "How does GitLab approach diversity, inclusion and belonging?",
            "⚙️ Engineering": "Tell me about GitLab's engineering department and practices",
            "🛡️ Security": "What are GitLab's security practices and standards?",
            "📦 Product": "What are GitLab's product principles?",
            "💰 Total Rewards": "What is GitLab's approach to total rewards and compensation?",
            "🎓 Learning & Development": "What learning and development opportunities does GitLab offer?",
            "👔 Leadership": "What are GitLab's leadership principles?",
        },
        "about_link": "[📖 GitLab Handbook](https://handbook.gitlab.com)",
    },
    "directions": {
        "label": "🧭 Direction",
        "title": "GitLab Direction Assistant",
        "subtitle": "Ask me anything about GitLab's product strategy, roadmap, and investment themes.",
        "chat_placeholder": "Ask me about GitLab's product direction...",
        "welcome": """
        **Welcome to the GitLab Direction Assistant!** 🧭

        I can help you explore GitLab's product direction and strategy:

        - 📊 **3-Year Strategy** — "What is GitLab's 3-year product strategy?"
        - 🎯 **Investment Themes** — "What are the FY26 R&D investment themes?"
        - 🔒 **DevSecOps** — "How does GitLab approach DevSecOps?"
        - 🤖 **AI/ML** — "What is GitLab's AI direction?"
        - 📈 **Releases** — "How does GitLab plan releases?"

        *Try clicking a topic in the sidebar or just type your question below!*
        """,
        "topics": {
            "📊 3-Year Strategy": "What is GitLab's 3-year product strategy?",
            "🎯 Strategic Challenges": "What are GitLab's strategic challenges?",
            "💰 FY26 Investment Themes": "What are the FY26 R&D investment themes?",
            "🔒 DevSecOps Platform": "How does GitLab approach DevSecOps platform completeness?",
            "🤖 AI & ML Direction": "What is GitLab's AI and ML product direction?",
            "📈 Release Planning": "How does GitLab plan releases?",
            "🛡️ Security Direction": "What is GitLab's security product direction?",
            "📦 CI/CD Direction": "What is GitLab's CI/CD direction?",
            "🔍 Analytics Direction": "What is GitLab's analytics direction?",
            "🌐 SaaS & Cloud": "What is GitLab's SaaS and cloud strategy?",
            "👥 Personas": "Who are GitLab's target personas?",
            "📋 OKRs": "What are GitLab's quarterly OKRs?",
        },
        "about_link": "[🧭 GitLab Direction](https://about.gitlab.com/direction/)",
    },
}


# ============================================
# SESSION STATE INITIALIZATION
# ============================================
def init_session_state():
    """Initialize all session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "active_module" not in st.session_state:
        st.session_state.active_module = "handbook"
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = None
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None
    if "chatbot_module" not in st.session_state:
        st.session_state.chatbot_module = None


def initialize_chatbot(module_key):
    """Initialize or reinitialize the chatbot for the given module."""
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        try:
            api_key = st.secrets.get("OPENROUTER_API_KEY", "")
        except Exception:
            pass

    if api_key:
        with st.spinner(f"🔄 Loading {MODULE_CONFIG[module_key]['label']} knowledge base..."):
            st.session_state.chatbot = HandbookChatbot(api_key=api_key, module=module_key)
            st.session_state.chatbot_module = module_key
    else:
        st.session_state.chatbot = None
        st.session_state.chatbot_module = None


init_session_state()

# Initialize chatbot if needed
if st.session_state.chatbot is None and st.session_state.chatbot_module is None:
    initialize_chatbot(st.session_state.active_module)


# ============================================
# SIDEBAR
# ============================================
def render_sidebar():
    """Render the sidebar with module selector, topic explorer and info."""
    with st.sidebar:
        # Logo/Brand
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <div style="font-size: 2.5rem;">🦊</div>
            <h2 style="margin: 0.3rem 0 0 0; font-size: 1.2rem; 
                background: linear-gradient(135deg, #FC6D26, #6B4FBB);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                GitLab Assistant
            </h2>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

        # ── Module Selector ──
        st.markdown("### 📂 Knowledge Base")

        module_options = list(MODULE_CONFIG.keys())
        module_labels = [MODULE_CONFIG[k]["label"] for k in module_options]

        current_idx = module_options.index(st.session_state.active_module)

        selected_label = st.selectbox(
            "Select source:",
            module_labels,
            index=current_idx,
            key="module_selector",
            label_visibility="collapsed",
        )

        selected_module = module_options[module_labels.index(selected_label)]

        # If module changed, reinitialize
        if selected_module != st.session_state.active_module:
            st.session_state.active_module = selected_module
            st.session_state.messages = []  # Clear chat on switch
            initialize_chatbot(selected_module)
            st.rerun()

        st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

        # ── Quick Topics ──
        config = MODULE_CONFIG[st.session_state.active_module]
        st.markdown("### 🗂️ Quick Topics")

        for label, question in config["topics"].items():
            if st.button(label, key=f"topic_{label}", use_container_width=True):
                st.session_state.pending_question = question

        st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

        # ── About section ──
        st.markdown("### ℹ️ About")
        st.markdown(
            f"""
            This chatbot uses **RAG** (Retrieval-Augmented Generation) 
            to answer questions from GitLab's public {config['label'].split(' ')[-1].lower()}.

            **Powered by:**
            - 🧠 OpenRouter AI
            - 📚 FAISS Vector Store
            - 🔍 Semantic Search

            {config['about_link']}
            """,
            unsafe_allow_html=True
        )

        st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

        # Reset conversation
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


render_sidebar()


# ============================================
# MAIN CHAT AREA
# ============================================
config = MODULE_CONFIG[st.session_state.active_module]

# Hero Header
st.markdown(f"""
<div class="hero-header">
    <div class="hero-title">{config['title']}</div>
    <p class="hero-subtitle">
        {config['subtitle']}
    </p>
</div>
""", unsafe_allow_html=True)

# Module indicator badge
module_emoji = "📖" if st.session_state.active_module == "handbook" else "🧭"
module_name = config['label'].split(' ')[-1]
st.markdown(f"""
<div style="text-align: center; margin-bottom: 1rem;">
    <span class="module-badge">{module_emoji} Active: {module_name}</span>
</div>
""", unsafe_allow_html=True)

# Check for API key
if st.session_state.chatbot is None:
    st.warning("⚠️ **OpenRouter API key not found.** Please set your API key to get started.")

    api_key_input = st.text_input(
        "Enter your OpenRouter API Key:",
        type="password",
        placeholder="sk-or-...",
        help="Get your free API key at https://openrouter.ai/keys"
    )

    if api_key_input:
        with st.spinner("🔄 Initializing chatbot..."):
            st.session_state.chatbot = HandbookChatbot(
                api_key=api_key_input,
                module=st.session_state.active_module
            )
            st.session_state.chatbot_module = st.session_state.active_module
            if st.session_state.chatbot.is_ready:
                st.success("✅ Chatbot initialized successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to initialize. Check your API key and make sure the vector store is built.")
                st.session_state.chatbot = None

    st.info("💡 **Tip:** You can also set the `OPENROUTER_API_KEY` environment variable or add it to a `.env` file.")
    st.stop()

# Check if chatbot is ready
if not st.session_state.chatbot.is_ready:
    st.error("❌ Chatbot failed to initialize. Please check that:")
    module_key = st.session_state.active_module
    st.markdown(f"""
    1. The FAISS index exists (run `python scraper.py --module {module_key}` then `python build_vectorstore.py --module {module_key}`)
    2. Your OpenRouter API key is valid
    """)
    st.stop()

# Reinitialize if module mismatch
if st.session_state.chatbot_module != st.session_state.active_module:
    initialize_chatbot(st.session_state.active_module)
    st.rerun()


# Welcome message for empty chat
if not st.session_state.messages:
    with st.chat_message("assistant", avatar="🦊"):
        st.markdown(config["welcome"])


# Display chat history
for message in st.session_state.messages:
    avatar = "🦊" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

        # Show sources if available
        if message["role"] == "assistant" and "sources" in message and message["sources"]:
            with st.expander(f"📚 Sources ({len(message['sources'])} references)", expanded=False):
                for src in message["sources"]:
                    relevance_pct = round(src.get('relevance', 0) * 100)
                    st.markdown(f"""
                    <div class="source-card">
                        <span class="source-section">📄 {src['section']}</span><br>
                        <a class="source-link" href="{src['url']}" target="_blank">🔗 {src['url']}</a>
                    </div>
                    """, unsafe_allow_html=True)




# ============================================
# HANDLE INPUT
# ============================================

def process_question(question):
    """Process a user question and generate a response."""
    # Add user message
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user", avatar="👤"):
        st.markdown(question)

    # Generate response
    with st.chat_message("assistant", avatar="🦊"):
        source_label = "handbook" if st.session_state.active_module == "handbook" else "direction"
        with st.spinner(f"🔍 Searching {source_label} & generating response..."):
            # Build history for context
            history = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages[:-1]
            ]

            result = st.session_state.chatbot.generate_response(question, history)

        # Display response
        st.markdown(result['response'])

        # Show sources
        if result['sources']:
            with st.expander(f"📚 Sources ({len(result['sources'])} references)", expanded=False):
                for src in result['sources']:
                    st.markdown(f"""
                    <div class="source-card">
                        <span class="source-section">📄 {src['section']}</span><br>
                        <a class="source-link" href="{src['url']}" target="_blank">🔗 {src['url']}</a>
                    </div>
                    """, unsafe_allow_html=True)



    # Save assistant response
    st.session_state.messages.append({
        "role": "assistant",
        "content": result['response'],
        "sources": result.get('sources', []),
        "confidence": result.get('confidence', 0),
        "chunks_retrieved": result.get('chunks_retrieved', 0)
    })


# Handle pending question from sidebar
if st.session_state.pending_question:
    question = st.session_state.pending_question
    st.session_state.pending_question = None
    process_question(question)

# Chat input
if prompt := st.chat_input(config["chat_placeholder"]):
    process_question(prompt)
