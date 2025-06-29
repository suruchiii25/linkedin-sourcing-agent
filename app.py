#!/usr/bin/env python3
"""
LinkedIn Sourcing Agent - Streamlit App for Hugging Face
Professional demo interface for the Synapse Hackathon
"""

import streamlit as st
import sys
import os
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Streamlit server settings
st.set_page_config(
    page_title="LinkedIn Sourcing Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set longer timeout for API calls
os.environ['STREAMLIT_SERVER_MAX_SIZE'] = '100'
os.environ['STREAMLIT_SERVER_TIMEOUT'] = '60'

# Initialize components as None
searcher = None
scorer = None
message_generator = None
modules_loaded = False

# Import our modules (before API key is set)
try:
    # Try different import paths
    try:
        from src.linkedin_search import LinkedInSearcher
        from src.enhanced_candidate_scorer import EnhancedCandidateScorer, CandidateProfile
        from src.message_generator import OutreachGenerator
    except ImportError:
        # Fallback to direct import (for Hugging Face)
        from linkedin_search import LinkedInSearcher
        from enhanced_candidate_scorer import EnhancedCandidateScorer, CandidateProfile
        from message_generator import OutreachGenerator
    
    modules_loaded = True
    logger.info("✅ All modules loaded successfully!")
    
except Exception as e:
    modules_loaded = False
    logger.error(f"❌ Module loading failed: {e}")

# Title and description
st.title("🚀 LinkedIn Sourcing Agent")
st.subheader("AI-Powered Candidate Sourcing for Synapse Hackathon")

# Sidebar for API key
with st.sidebar:
    st.header("🔧 Configuration")
    groq_key = st.text_input("Groq API Key", type="password", help="Enter your Groq API key")
    
    if groq_key:
        os.environ['GROQ_API_KEY'] = groq_key
        st.success("✅ API Key configured!")
        
        # Initialize components after API key is set
        if modules_loaded and not searcher:  # Only initialize if not already initialized
            try:
                searcher = LinkedInSearcher()
                scorer = EnhancedCandidateScorer()
                message_generator = OutreachGenerator()
                st.sidebar.success("✅ Components initialized successfully!")
            except Exception as e:
                st.sidebar.error(f"❌ Component initialization failed: {e}")
                modules_loaded = False
                logger.error(f"Component initialization error: {e}")
    else:
        st.warning("⚠️ Please enter your Groq API key to enable AI features")

# Main interface
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Quick Demo", "🔍 Custom Search", "📊 Results Analysis", "💬 Generated Messages"])

with tab1:
    st.header("🎯 Quick Demo - Windsurf ML Engineer Role")
    
    # Windsurf job description
    windsurf_job = """Software Engineer, ML Research
Windsurf • Full Time • Mountain View, CA • On-site • $140,000 – $300,000 + Equity

About the Company:
Windsurf (formerly Codeium) is a Forbes AI 50 company building the future of developer productivity through AI. With over 200 employees and $243M raised across multiple rounds including a Series C, Windsurf provides cutting-edge in-editor autocomplete, chat assistants, and full IDEs powered by proprietary LLMs.

Job Requirements:
• 2+ years in software engineering with fast promotions
• Strong software engineering and systems thinking skills
• Proven experience training and iterating on large production neural networks
• Strong GPA from a top CS undergrad program (MIT, Stanford, CMU, UIUC, etc.)
• Familiarity with tools like Copilot, ChatGPT, or Windsurf is preferred
• Deep curiosity for the code generation space
• Must be able to work in Mountain View, CA full-time onsite"""
    
    st.text_area("Job Description", windsurf_job, height=200, disabled=True)
    
    if st.button("🚀 Run Complete Analysis", type="primary"):
        if not groq_key:
            st.error("❌ Please enter your Groq API key in the sidebar first!")
        else:
                try:
                    if modules_loaded:
                    # Step 1: Get candidates (fast mock data)
                    with st.spinner("🔍 Finding candidates..."):
                        try:
                        candidates = searcher.search_linkedin_profiles(windsurf_job)
                            if not candidates:
                                st.error("❌ No candidates found!")
                                st.stop()
                        st.success(f"✅ Found {len(candidates)} candidates")
                        except Exception as e:
                            st.error(f"❌ Search failed: {str(e)}")
                            st.stop()
                    
                    # Convert to CandidateProfile objects
                    candidate_profiles = []
                    for candidate in candidates:
                        try:
                            profile = CandidateProfile(
                                name=candidate['name'],
                                linkedin_url=candidate['linkedin_url'],
                                headline=candidate['headline'],
                                company=candidate['company'],
                                location=candidate['location']
                            )
                            candidate_profiles.append(profile)
                        except Exception as e:
                            logger.warning(f"Failed to convert candidate {candidate.get('name', 'Unknown')}: {e}")
                            continue
                    
                    if not candidate_profiles:
                        st.error("❌ Failed to process candidate data!")
                        st.stop()
                    
                    # Step 2: Score candidates
                        with st.spinner("🎯 Scoring candidates..."):
                        try:
                            scored_candidates = scorer.score_candidates_batch(candidate_profiles, windsurf_job)
                            if not scored_candidates:
                                st.error("❌ Scoring failed!")
                                st.stop()
                            scored_candidates.sort(key=lambda x: x['total_score'], reverse=True)
                            st.success("✅ Candidates scored successfully!")
                        except Exception as e:
                            st.error(f"❌ Scoring error: {str(e)}")
                            st.stop()
                    
                    # Store results
                        st.session_state['candidates'] = scored_candidates
                        st.session_state['job_desc'] = windsurf_job
                        
                    # Step 3: Generate messages
                        with st.spinner("💬 Generating personalized messages..."):
                        try:
                            top_5_for_outreach = []
                            for candidate in scored_candidates[:5]:
                                outreach_candidate = {
                                    "name": candidate['name'],
                                    "linkedin_url": candidate['linkedin_url'],
                                    "headline": candidate.get('skills_analysis', {}).get('reasoning', candidate.get('headline', '')),
                                    "company": candidate['company'],
                                    "location": candidate['location'],
                                    "fit_score": candidate['total_score'],
                                    "score_breakdown": candidate['score_breakdown'],
                                    "key_strengths": candidate.get('skills_analysis', {}).get('key_strengths', [])
                                }
                                top_5_for_outreach.append(outreach_candidate)
                            
                            messages = message_generator.generate_batch_messages(top_5_for_outreach, windsurf_job, top_n=5)
                            if not messages:
                                st.error("❌ Message generation failed!")
                                st.stop()
                            st.session_state['messages'] = messages
                            st.success("✅ Messages generated successfully!")
                        except Exception as e:
                            st.error(f"❌ Message generation error: {str(e)}")
                            st.stop()
                        
                        st.success("🎉 Analysis complete! Check the other tabs for detailed results.")
                        
                    else:
                        # Demo mode with sample data
                        st.info("📋 Running in demo mode with sample data...")
                        sample_candidates = [
                            {
                                "name": "Sarah Chen",
                                "linkedin_url": "https://linkedin.com/in/sarah-chen-ml",
                                "headline": "Senior ML Engineer at OpenAI",
                                "company": "OpenAI",
                                "location": "San Francisco, CA",
                                "fit_score": 8.7,
                                "score_breakdown": {
                                    "education": 9.0,
                                    "trajectory": 8.5,
                                    "company": 9.5,
                                    "skills": 9.0,
                                    "location": 8.0,
                                    "tenure": 8.0
                                }
                            },
                            {
                                "name": "Alex Kumar", 
                                "linkedin_url": "https://linkedin.com/in/alex-kumar-ai",
                                "headline": "AI Research Scientist at Google DeepMind",
                                "company": "Google DeepMind",
                                "location": "Mountain View, CA",
                                "fit_score": 8.4,
                                "score_breakdown": {
                                    "education": 8.5,
                                    "trajectory": 7.5,
                                    "company": 9.5,
                                    "skills": 8.5,
                                    "location": 10.0,
                                    "tenure": 7.0
                                }
                            },
                            {
                                "name": "Priya Patel",
                                "linkedin_url": "https://linkedin.com/in/priya-patel-ml", 
                                "headline": "Machine Learning Engineer at Anthropic",
                                "company": "Anthropic",
                                "location": "San Francisco, CA",
                                "fit_score": 7.9,
                                "score_breakdown": {
                                    "education": 7.0,
                                    "trajectory": 7.5,
                                    "company": 9.0,
                                    "skills": 8.0,
                                    "location": 8.0,
                                    "tenure": 8.5
                                }
                            }
                        ]
                        
                        st.session_state['candidates'] = sample_candidates
                        st.session_state['job_desc'] = windsurf_job
                        st.success("✅ Demo data loaded! Check other tabs for results.")
                        
                except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                logger.error(f"Analysis failed: {e}")
                st.stop()

with tab2:
    st.header("🔍 Custom Job Search")
    
    custom_job = st.text_area(
        "Enter Job Description", 
        placeholder="Paste any job description here...",
        height=200
    )
    
    if st.button("🔍 Search Custom Job") and custom_job:
        if not groq_key:
            st.error("❌ Please enter your Groq API key in the sidebar first!")
        else:
            try:
                if modules_loaded:
                    # Step 1: Get candidates (fast mock data)
                    with st.spinner("🔍 Finding candidates..."):
                        try:
                            candidates = searcher.search_linkedin_profiles(custom_job)
                            if not candidates:
                                st.error("❌ No candidates found!")
                                st.stop()
                            st.success(f"✅ Found {len(candidates)} candidates")
                        except Exception as e:
                            st.error(f"❌ Search failed: {str(e)}")
                            st.stop()
                    
                    # Convert to CandidateProfile objects
                    candidate_profiles = []
                    for candidate in candidates:
                        try:
                            profile = CandidateProfile(
                                name=candidate['name'],
                                linkedin_url=candidate['linkedin_url'],
                                headline=candidate['headline'],
                                company=candidate['company'],
                                location=candidate['location']
                            )
                            candidate_profiles.append(profile)
                        except Exception as e:
                            logger.warning(f"Failed to convert candidate {candidate.get('name', 'Unknown')}: {e}")
                            continue
                    
                    if not candidate_profiles:
                        st.error("❌ Failed to process candidate data!")
                        st.stop()
                    
                    # Step 2: Score candidates
                    with st.spinner("🎯 Scoring candidates..."):
                        try:
                            scored_candidates = scorer.score_candidates_batch(candidate_profiles, custom_job)
                            if not scored_candidates:
                                st.error("❌ Scoring failed!")
                                st.stop()
                            scored_candidates.sort(key=lambda x: x['total_score'], reverse=True)
                            st.success("✅ Candidates scored successfully!")
                        except Exception as e:
                            st.error(f"❌ Scoring error: {str(e)}")
                            st.stop()
                    
                    # Store results
                    st.session_state['candidates'] = scored_candidates
                    st.session_state['job_desc'] = custom_job
                    
                    # Step 3: Generate messages
                    with st.spinner("💬 Generating personalized messages..."):
                        try:
                            top_5_for_outreach = []
                            for candidate in scored_candidates[:5]:
                                outreach_candidate = {
                                    "name": candidate['name'],
                                    "linkedin_url": candidate['linkedin_url'],
                                    "headline": candidate.get('skills_analysis', {}).get('reasoning', candidate.get('headline', '')),
                                    "company": candidate['company'],
                                    "location": candidate['location'],
                                    "fit_score": candidate['total_score'],
                                    "score_breakdown": candidate['score_breakdown'],
                                    "key_strengths": candidate.get('skills_analysis', {}).get('key_strengths', [])
                                }
                                top_5_for_outreach.append(outreach_candidate)
                            
                            messages = message_generator.generate_batch_messages(top_5_for_outreach, custom_job, top_n=5)
                            if not messages:
                                st.error("❌ Message generation failed!")
                                st.stop()
                            st.session_state['messages'] = messages
                            st.success("✅ Messages generated successfully!")
                        except Exception as e:
                            st.error(f"❌ Message generation error: {str(e)}")
                            st.stop()
                    
                    st.success("🎉 Analysis complete! Check the other tabs for detailed results.")
                    
                else:
                    st.error("❌ Modules not loaded. Please check your API key and try again.")
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                logger.error(f"Analysis failed: {e}")
                st.stop()

with tab3:
    st.header("📊 Candidate Analysis Results")
    
    if 'candidates' in st.session_state:
        candidates = st.session_state['candidates']
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Candidates", len(candidates))
        with col2:
            avg_score = sum(c.get('total_score', 0) for c in candidates) / len(candidates)
            st.metric("Average Score", f"{avg_score:.1f}/10")
        with col3:
            top_score = max(c.get('total_score', 0) for c in candidates)
            st.metric("Top Score", f"{top_score:.1f}/10")
        with col4:
            qualified = len([c for c in candidates if c.get('total_score', 0) >= 7.0])
            st.metric("Qualified (7+)", qualified)
        
        # Detailed candidate cards
        st.subheader("🏆 Ranked Candidates")
        
        for i, candidate in enumerate(candidates, 1):
            with st.expander(f"#{i} {candidate['name']} - Score: {candidate.get('total_score', 0):.1f}/10"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Company:** {candidate.get('company', 'N/A')}")
                    st.write(f"**Role:** {candidate.get('skills_analysis', {}).get('reasoning', candidate.get('headline', 'N/A'))}")
                    st.write(f"**Location:** {candidate.get('location', 'N/A')}")
                    st.write(f"**LinkedIn:** {candidate.get('linkedin_url', 'N/A')}")
                    
                    # Add key strengths if available
                    key_strengths = candidate.get('skills_analysis', {}).get('key_strengths', [])
                    if key_strengths:
                        st.write("**Key Strengths:**")
                        for strength in key_strengths:
                            st.write(f"• {strength}")
                
                with col2:
                    if 'score_breakdown' in candidate:
                        breakdown = candidate['score_breakdown']
                        st.write("**Score Breakdown:**")
                        for factor, score in breakdown.items():
                            st.write(f"• {factor.title()}: {score:.1f}/10")
    else:
        st.info("👆 Run the analysis in the 'Quick Demo' tab first!")

with tab4:
    st.header("💬 Generated Outreach Messages")
    
    if 'messages' in st.session_state:
        messages = st.session_state['messages']
        
        st.subheader("📨 Personalized LinkedIn Messages")
        st.info("💡 These messages reference specific candidate details and explain why they're a good fit!")
        
        for i, msg_data in enumerate(messages, 1):
            # Handle OutreachMessage objects properly
            candidate_name = msg_data.candidate_name if hasattr(msg_data, 'candidate_name') else f'Candidate {i}'
            message = msg_data.message if hasattr(msg_data, 'message') else 'Message generation failed'
            personalization = msg_data.personalization_elements if hasattr(msg_data, 'personalization_elements') else []
            message_length = msg_data.message_length if hasattr(msg_data, 'message_length') else len(message)
            
            with st.expander(f"📧 Message for {candidate_name}"):
                st.text_area(
                    f"LinkedIn Message #{i}",
                    message,
                    height=200,
                    key=f"message_{i}"
                )
                
                # Message stats
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Message Length", f"{message_length} chars")
                with col2:
                    st.metric("Personalization Elements", len(personalization))
                
                # Show personalization details
                if personalization:
                    st.write("**Personalization Elements:**")
                    for element in personalization:
                        st.write(f"• {element}")
    
    elif 'candidates' in st.session_state:
        st.info("💬 Messages will be generated automatically when you run the analysis!")
        
        if st.button("🔄 Generate Messages Now"):
            if groq_key and modules_loaded:
                try:
                    message_generator = OutreachGenerator()
                    top_candidates = st.session_state['candidates'][:3]
                    job_desc = st.session_state.get('job_desc', '')
                    
                    with st.spinner("💬 Generating personalized messages..."):
                        messages = message_generator.generate_batch_messages(top_candidates, job_desc)
                        st.session_state['messages'] = messages
                        st.success("✅ Messages generated! Refresh to see them.")
                        
                except Exception as e:
                    st.error(f"❌ Error generating messages: {e}")
            else:
                st.warning("⚠️ Please ensure API key is set and modules are loaded!")
    else:
        st.info("👆 Run the analysis in the 'Quick Demo' tab first!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p><strong>🚀 LinkedIn Sourcing Agent</strong> - Built for Synapse AI Hackathon</p>
    <p>Autonomous AI agent for candidate sourcing, scoring, and outreach generation</p>
</div>
""", unsafe_allow_html=True)

# Debug info in sidebar
with st.sidebar:
    st.markdown("---")
    st.header("🐛 Debug Info")
    st.write(f"**Modules Loaded:** {'✅' if modules_loaded else '❌'}")
    st.write(f"**API Key Set:** {'✅' if groq_key else '❌'}")
    if 'candidates' in st.session_state:
        st.write(f"**Candidates:** {len(st.session_state['candidates'])}")
    if 'messages' in st.session_state:
        st.write(f"**Messages:** {len(st.session_state['messages'])}")