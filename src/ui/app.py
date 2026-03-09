import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))
import streamlit as st
import json
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from src.graph import app, EmailState
from typing import Optional

# Page configuration
st.set_page_config(
    page_title="AI Email Assistant",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .email-preview {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 20px;
        margin: 10px 0;
    }
    .email-header {
        font-weight: 600;
        color: #495057;
        margin-bottom: 5px;
    }
    .status-success {
        color: #28a745;
        font-weight: 600;
    }
    .status-warning {
        color: #ffc107;
        font-weight: 600;
    }
    .stTextArea textarea {
        font-family: 'Courier New', monospace;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'email_history' not in st.session_state:
    st.session_state.email_history = []
if 'current_email' not in st.session_state:
    st.session_state.current_email = {
        'to': '',
        'cc': '',
        'subject': '',
        'body': ''
    }
if 'parsed_input' not in st.session_state:
    st.session_state.parsed_input = None

# Helper Functions
# def parse_user_input(user_input, context, tone):
#     """Simulate input parsing (replace with actual AI agent call)"""
#     # This is a placeholder - integrate with your actual Input Parsing Agent
#     parsed = {
#         "intent": "compose_email",
#         "confidence": 0.95,
#         "entities": {
#             "recipients": {"to": [], "cc": [], "bcc": []},
#             "subject": None,
#             "content_instructions": user_input,
#             "tone": tone,
#             "context": context
#         },
#         "timestamp": datetime.now().isoformat()
#     }
#     return parsed

# def generate_email_content(parsed_input, tone, additional_context=""):
#     """Simulate email generation (replace with actual AI agent call)"""
#     # Placeholder for AI-generated content
#     instructions = parsed_input['entities']['content_instructions']
    
#     sample_body = f"""Dear Recipient,

# {instructions}

# {additional_context}

# Best regards,
# [Your Name]"""
    
#     return {
#         'subject': f"Regarding: {instructions[:50]}...",
#         'body': sample_body
#     }

def export_to_pdf(email_data):
    """Export email to PDF format"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Custom styles
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor='#2c3e50',
        spaceAfter=6
    )
    
    # Add email headers
    story.append(Paragraph(f"<b>To:</b> {email_data['to']}", styles['Normal']))
    if email_data['cc']:
        story.append(Paragraph(f"<b>Cc:</b> {email_data['cc']}", styles['Normal']))
    story.append(Paragraph(f"<b>Subject:</b> {email_data['subject']}", styles['Normal']))
    story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Add body
    for para in email_data['body'].split('\n\n'):
        if para.strip():
            story.append(Paragraph(para.replace('\n', '<br/>'), styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def create_email_client_mailto(email_data):
    """Generate mailto link"""
    import urllib.parse
    
    to = email_data.get('to', '')
    cc = email_data.get('cc', '')
    subject = email_data.get('subject', '')
    body = email_data.get('body', '')
    
    mailto_parts = [f"mailto:{to}"]
    params = []
    
    if cc:
        params.append(f"cc={urllib.parse.quote(cc)}")
    if subject:
        params.append(f"subject={urllib.parse.quote(subject)}")
    if body:
        params.append(f"body={urllib.parse.quote(body)}")
    
    if params:
        mailto_parts.append("?" + "&".join(params))
    
    return "".join(mailto_parts)

# Main App Layout
st.markdown('<div class="main-header">📧 AI Email Assistant</div>', unsafe_allow_html=True)
st.markdown("Generate professional emails with AI assistance and human-in-the-loop feedback")

# Sidebar Configuration
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    
    # Context Selector
    st.markdown("#### Context")
    context_type = st.selectbox(
        "Email Context",
        ["Business - Formal", "Business - Casual", "Personal", "Customer Support", 
         "Sales Outreach", "Follow-up", "Internal Team", "Job Application"],
        help="Select the context for your email"
    )
    
    additional_context = st.text_area(
        "Additional Context (Optional)",
        placeholder="E.g., This is a follow-up to our meeting last week...",
        height=100,
    )
    
    st.markdown("---")
    
    # Tone Selector
    st.markdown("#### Tone & Style")
    tone = st.select_slider(
        "Tone",
        options=["Very Formal", "Formal", "Professional", "Friendly", "Casual", "Enthusiastic"],
        value=st.session_state.get("tone_selector", "Professional"),
        help="Adjust the tone of your email",
    )
    
    length_preference = st.radio(
        "Length",
        ["Brief (2-3 sentences)", "Medium (1 paragraph)", "Detailed (Multiple paragraphs)"],
        index=1
    )
    
    st.markdown("---")
    
    # Intent Selector
    st.markdown("#### Intent")
    intent = st.selectbox(
        "Email Intent",
        ["Compose New", "Reply", "Follow-up", "Request Information", 
         "Schedule Meeting", "Thank You", "Apology", "Announcement"],
        help="What is the primary purpose of this email?"
    )
    
    st.markdown("---")
    
    # Advanced Options
    with st.expander("🔧 Advanced Options"):
        include_greeting = st.checkbox("Include greeting", value=True)
        include_signature = st.checkbox("Include signature", value=True)
        urgency = st.select_slider(
            "Urgency",
            options=["Low", "Normal", "High", "Urgent"],
            value="Normal"
        )

# Main Content Area - Two Columns
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<div class="section-header">✍️ Input</div>', unsafe_allow_html=True)
    
    # User Input
    user_input = st.text_area(
        "Describe what you want to write",
        placeholder="E.g., Write an email to John about the Q4 budget meeting scheduled for next Tuesday. Ask him to prepare the financial reports.",
        value=f"Subject: {context_type}\nTone: {tone}\nAdditional context: {additional_context}\nIntent: {intent}",
        height=150,
        help="Describe your email in natural language",
    )
    
    # Email Recipients
    st.markdown("##### Recipients")
    recipient_to = st.text_input(
        "To",
        placeholder="john@company.com",
        help="Primary recipients (comma-separated for multiple)"
    )
    
    recipient_cc = st.text_input(
        "Cc (Optional)",
        placeholder="manager@company.com",
        help="CC recipients (comma-separated for multiple)"
    )
    
    # Generate Button
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    
    with col_btn1:
        generate_button = st.button("🚀 Generate Email", type="primary", use_container_width=True)
    
    with col_btn2:
        clear_button = st.button("🔄 Clear", use_container_width=True)
    
    with col_btn3:
        refine_button = st.button("✨ Refine", use_container_width=True)
    
    # Processing
    if generate_button and user_input:
        with st.spinner("Parsing input and generating email..."):
            # Build raw prompt including recipient_to so parser can extract it
            raw_prompt = f"{user_input}\nTo: {recipient_to}" if recipient_to else user_input
            # Parse input
            init = EmailState(raw=raw_prompt)
            out = app.invoke(init)

            #st.session_state.parsed_input = parse_user_input(user_input, context_type, tone)
            
            # Generate email
            # generated = generate_email_content(
            #     st.session_state.parsed_input, 
            #     tone, 
            #     additional_context
            # )
            
            # Update current email
            st.session_state.current_email = {
                'to': recipient_to,
                'cc': recipient_cc,
                'subject': out.get("draft_subject"),
                'body': out.get('draft_body')
            }
            
            st.success("✅ Email generated successfully!")
    
    if clear_button:
        st.session_state.current_email = {'to': '', 'cc': '', 'subject': '', 'body': ''}
        st.session_state.parsed_input = None
        # Clear input widgets
        st.session_state["subject_editor"] = ""
        st.session_state["body_editor"] = ""
        st.session_state["user_input_editor"] = ""
        st.session_state["additional_context"] = ""
        st.session_state["tone_selector"] = "Professional"
        st.rerun()
    
    if refine_button and st.session_state.current_email['body']:
        st.info("💡 Tip: Modify the content in the editor and regenerate for refinements")
    
    # Display parsed input (for debugging/transparency)
    if st.session_state.parsed_input:
        with st.expander("🔍 View Parsed Input (Debug)"):
            st.json(st.session_state.parsed_input)

with col2:
    st.markdown('<div class="section-header">📧 Email Preview & Editor</div>', unsafe_allow_html=True)
    
    preview_to = st.session_state.current_email.get('to', recipient_to)
    preview_cc = st.session_state.current_email.get('cc', recipient_cc)
    preview_subject = st.session_state.current_email.get('subject', '')
    
    # st.markdown(f"""
    # <div class="email-preview">
    #     <div class="email-header">To: {preview_to if preview_to else '<em>Not specified</em>'}</div>
    #     {f'<div class="email-header">Cc: {preview_cc}</div>' if preview_cc else ''}
    #     <div class="email-header">Subject: {preview_subject if preview_subject else '<em>Not specified</em>'}</div>
    # </div>
    # """, unsafe_allow_html=True)
    preview_body = st.session_state.current_email.get('body', '')

    # Use native Streamlit components for reliable rendering
    preview_box = st.container(border=True)
    with preview_box:
        st.caption("Email Preview")
        st.write(f"To: {preview_to if preview_to else 'Not specified'}")
        if preview_cc:
            st.write(f"Cc: {preview_cc}")
        st.write(f"Subject: {preview_subject if preview_subject else 'Not specified'}")
        st.divider()
        st.text_area("Body (preview)", value={preview_body}, height=200)

    # Editable Email Fields
    st.markdown("##### Edit Email")
    
    edited_subject: Optional[str] = st.text_input(
        "Subject Line",
        value=st.session_state.current_email.get('subject'),
        placeholder="Enter email subject",
    )
    
    edited_body: Optional[str] = st.text_area(
        "Email Body",
        value=st.session_state.current_email.get('body'),
        placeholder="Email content will appear here...",
        height=300,
    )
    
    # Update session state with edits
    if edited_subject != st.session_state.current_email.get('subject', ''):
        st.session_state.current_email['subject'] = edited_subject

    if edited_body != st.session_state.current_email.get('body', ''):
        st.session_state.current_email['body'] = edited_body

    # edited_subject = st.session_state.current_email.get('subject', '')
    # edited_body = st.session_state.current_email.get('body', '')

    # Action Buttons
    st.markdown("---")
    st.markdown("##### Actions")
    
    action_col1, action_col2, action_col3 = st.columns(3)
    
    with action_col1:
        if st.button("📋 Copy to Clipboard", use_container_width=True):
            email_text = f"To: {preview_to}\n"
            if preview_cc:
                email_text += f"Cc: {preview_cc}\n"
            email_text += f"Subject: {edited_subject}\n\n{edited_body}"
            
            st.code(email_text, language=None)
            st.success("✅ Email ready to copy!")
    
    with action_col2:
        if edited_body:
            pdf_buffer = export_to_pdf({
                'to': preview_to,
                'cc': preview_cc,
                'subject': edited_subject,
                'body': edited_body
            })
            
            st.download_button(
                label="📄 Export PDF",
                data=pdf_buffer,
                file_name=f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    
    with action_col3:
        if edited_body:
            mailto_link = create_email_client_mailto({
                'to': preview_to,
                'cc': preview_cc,
                'subject': edited_subject,
                'body': edited_body
            })
            
            st.markdown(f'<a href="{mailto_link}" target="_blank"><button style="width:100%; padding:0.5rem; background-color:#0066cc; color:white; border:none; border-radius:5px; cursor:pointer;">📧 Open in Email Client</button></a>', 
                       unsafe_allow_html=True)
    
    # Feedback Section
    st.markdown("---")
    st.markdown("##### 💬 Feedback")
    
    feedback_col1, feedback_col2 = st.columns(2)
    
    with feedback_col1:
        quality_rating = st.select_slider(
            "Quality",
            options=["Poor", "Fair", "Good", "Excellent"],
            value="Good"
        )
    
    with feedback_col2:
        tone_match = st.select_slider(
            "Tone Match",
            options=["Off", "Close", "Perfect"],
            value="Close"
        )
    
    feedback_notes = st.text_area(
        "Additional Feedback",
        placeholder="Any suggestions or issues?",
        height=80
    )
    
    if st.button("Submit Feedback", use_container_width=True):
        feedback_data = {
            'quality': quality_rating,
            'tone_match': tone_match,
            'notes': feedback_notes,
            'timestamp': datetime.now().isoformat()
        }
        st.success("✅ Thank you for your feedback!")
        # Here you would send feedback to your backend

# Email History Section (Bottom)
st.markdown("---")
st.markdown('<div class="section-header">📚 Email History</div>', unsafe_allow_html=True)

if st.session_state.current_email['body']:
    if st.button("💾 Save to History"):
        st.session_state.email_history.append({
            **st.session_state.current_email,
            'timestamp': datetime.now().isoformat(),
            'context': context_type,
            'tone': tone
        })
        st.success("Email saved to history!")

if st.session_state.email_history:
    for idx, email in enumerate(reversed(st.session_state.email_history[-5:])):
        with st.expander(f"📧 {email['subject'][:50]}... ({email['timestamp'][:10]})"):
            st.markdown(f"**To:** {email['to']}")
            if email['cc']:
                st.markdown(f"**Cc:** {email['cc']}")
            st.markdown(f"**Context:** {email['context']} | **Tone:** {email['tone']}")
            st.text_area("Body", email['body'], height=150, key=f"history_{idx}", disabled=True)
else:
    st.info("No emails in history yet. Generate and save emails to see them here.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6c757d; font-size: 0.9rem;">
    🤖 AI Email Assistant | Built with Streamlit | Human-in-the-Loop Design
</div>
""", unsafe_allow_html=True)

# Replace deprecated experimental API usage
# Note: if present elsewhere in this file, update to st.user