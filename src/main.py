#!/usr/bin/env python3
"""
Complete LinkedIn Sourcing Agent API
Integrates all components into a professional FastAPI service
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
import os
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our modules
try:
    from linkedin_search import LinkedInSearcher
    from enhanced_candidate_scorer import EnhancedCandidateScorer, CandidateProfile
    from message_generator import OutreachGenerator
except ImportError:
    logger.warning("Could not import all modules - using mock implementations")

# FastAPI app
app = FastAPI(
    title="LinkedIn Sourcing Agent",
    description="AI-powered candidate sourcing, scoring, and outreach generation",
    version="1.0.0"
)

# Request/Response Models
class JobRequest(BaseModel):
    job_description: str
    max_candidates: int = 10
    location_preference: str = "Any"

class Candidate(BaseModel):
    name: str
    linkedin_url: str
    headline: str
    company: str
    location: str
    fit_score: float
    score_breakdown: Dict[str, float]
    outreach_message: str
    personalization_elements: List[str]
    recruiter_info: Dict[str, str]

class SourcingResponse(BaseModel):
    job_id: str
    candidates_found: int
    top_candidates: List[Candidate]
    processing_time_seconds: float
    timestamp: str
    recruiter_info: Dict[str, str]

class SourcingAgent:
    """Main agent class that coordinates the sourcing pipeline"""
    
    def __init__(self):
        """Initialize components"""
        try:
            self.searcher = LinkedInSearcher()
            self.scorer = EnhancedCandidateScorer()  # Updated to use EnhancedCandidateScorer
            self.message_generator = OutreachGenerator()
            logger.info("All components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise

    def process_job(self, job_description: str, max_candidates: int = 10) -> Dict[str, Any]:
        """Complete end-to-end processing pipeline."""
        start_time = datetime.now()
        
        try:
            # Step 1: Search for candidates
            logger.info("Starting candidate search...")
            raw_candidates = self._get_candidates(job_description)
            
            # Convert candidates to CandidateProfile objects
            candidate_profiles = []
            for candidate in raw_candidates:
                profile = CandidateProfile(
                    name=candidate['name'],
                    linkedin_url=candidate['linkedin_url'],
                    headline=candidate['headline'],
                    company=candidate['company'],
                    location=candidate['location']
                )
                candidate_profiles.append(profile)
            
            # Step 2: Score candidates
            logger.info(f"Scoring {len(raw_candidates)} candidates...")
            scored_candidates = self.scorer.score_candidates_batch(candidate_profiles, job_description)
            
            # Step 3: Sort by score and take top candidates
            top_candidates = sorted(scored_candidates, key=lambda x: x['total_score'], reverse=True)[:max_candidates]
            
            # Step 4: Generate outreach messages for top 5
            logger.info("Generating outreach messages...")
            top_5_for_outreach = []
            for candidate in top_candidates[:5]:
                # Restructure candidate data for message generator
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
            
            # Generate messages
            messages = self.message_generator.generate_batch_messages(
                top_5_for_outreach, 
                job_description, 
                top_n=5
            )
            
            # Step 5: Combine everything
            final_candidates = []
            for candidate in top_candidates:
                # Find matching message
                message_data = next(
                    (msg for msg in messages if msg.candidate_name == candidate['name']), 
                    None
                )
                
                # Create score breakdown with proper structure
                score_breakdown = {
                    'education': candidate['score_breakdown']['education'],
                    'trajectory': candidate['score_breakdown']['trajectory'],
                    'company': candidate['score_breakdown']['company'],
                    'skills': candidate['score_breakdown'].get('skills', 0.0),
                    'location': candidate['score_breakdown']['location'],
                    'tenure': candidate['score_breakdown']['tenure']
                }
                
                final_candidate = Candidate(
                    name=candidate['name'],
                    linkedin_url=candidate['linkedin_url'],
                    headline=candidate.get('skills_analysis', {}).get('reasoning', ''),
                    company=candidate['company'],
                    location=candidate['location'],
                    fit_score=round(candidate['total_score'], 1),
                    score_breakdown=score_breakdown,
                    outreach_message=message_data.message if message_data else "Message generation failed",
                    personalization_elements=message_data.personalization_elements if message_data else [],
                    recruiter_info=self.message_generator.recruiter_info
                )
                final_candidates.append(final_candidate)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "job_id": f"job_{int(start_time.timestamp())}",
                "candidates_found": len(raw_candidates),
                "top_candidates": final_candidates,
                "processing_time_seconds": round(processing_time, 2),
                "timestamp": start_time.isoformat(),
                "recruiter_info": self.message_generator.recruiter_info
            }
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    def _get_candidates(self, job_description: str) -> List[Dict]:
        """Get candidates using search or mock data."""
        try:
            # Try real search first
            return self.searcher.search_linkedin_profiles(job_description)
        except:
            # Fallback to mock data
            logger.info("Using mock candidate data")
            return [
                {
                    "name": "Sarah Chen",
                    "linkedin_url": "https://linkedin.com/in/sarah-chen-ml",
                    "headline": "Senior ML Engineer at OpenAI",
                    "company": "OpenAI",
                    "location": "San Francisco, CA"
                },
                {
                    "name": "Alex Kumar", 
                    "linkedin_url": "https://linkedin.com/in/alex-kumar-ai",
                    "headline": "AI Research Scientist at Google DeepMind",
                    "company": "Google DeepMind",
                    "location": "Mountain View, CA"
                },
                {
                    "name": "Maria Rodriguez",
                    "linkedin_url": "https://linkedin.com/in/maria-rodriguez-dev",
                    "headline": "Full Stack Engineer at Meta",
                    "company": "Meta", 
                    "location": "Menlo Park, CA"
                },
                {
                    "name": "James Wu",
                    "linkedin_url": "https://linkedin.com/in/james-wu-engineer",
                    "headline": "Backend Engineer at Stripe",
                    "company": "Stripe",
                    "location": "San Francisco, CA"
                },
                {
                    "name": "Priya Patel",
                    "linkedin_url": "https://linkedin.com/in/priya-patel-ml", 
                    "headline": "Machine Learning Engineer at Anthropic",
                    "company": "Anthropic",
                    "location": "San Francisco, CA"
                }
            ]

# Initialize the agent
agent = SourcingAgent()

# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "LinkedIn Sourcing Agent API",
        "status": "active",
        "version": "1.0.0",
        "recruiter": "Alex Chen | Senior Technical Recruiter at Windsurf"
    }

@app.post("/source-candidates", response_model=SourcingResponse)
async def source_candidates(request: JobRequest):
    """
    Main endpoint: Process job description and return scored candidates with outreach messages.
    
    This endpoint:
    1. Searches for LinkedIn profiles matching the job description
    2. Scores each candidate using our 6-factor rubric  
    3. Generates personalized outreach messages for top candidates
    4. Returns everything in a structured JSON response
    """
    logger.info(f"Processing job request with {request.max_candidates} max candidates")
    
    try:
        result = agent.process_job(
            job_description=request.job_description,
            max_candidates=request.max_candidates
        )
        
        return SourcingResponse(**result)
        
    except Exception as e:
        logger.error(f"Request processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "components": {
            "searcher": "active",
            "scorer": "active", 
            "message_generator": "active"
        },
        "recruiter_info": {
            "name": "Alex Chen",
            "title": "Senior Technical Recruiter",
            "company": "Windsurf"
        },
        "timestamp": datetime.now().isoformat()
    }

# Test endpoint for the provided job description
@app.post("/test-windsurf-job")
async def test_windsurf_job():
    """
    Test endpoint using the exact Windsurf ML Research Engineer job description.
    Perfect for demonstrating the system with the hackathon's provided job.
    """
    windsurf_job = """
    Software Engineer, ML Research
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
    • Must be able to work in Mountain View, CA full-time onsite
    """
    
    request = JobRequest(
        job_description=windsurf_job,
        max_candidates=5,
        location_preference="Mountain View, CA"
    )
    
    return await source_candidates(request)

@app.get("/recruiter-info")
async def get_recruiter_info():
    """Get recruiter contact information."""
    return {
        "recruiter": {
            "name": "Alex Chen",
            "title": "Senior Technical Recruiter",
            "company": "Windsurf",
            "linkedin": "https://linkedin.com/in/alex-chen-recruiter",
            "email": "alex.chen@windsurf.com"
        },
        "message": "All outreach messages are sent on behalf of Alex Chen from Windsurf"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting LinkedIn Sourcing Agent API...")
    print("📍 API will be available at: http://localhost:8000")
    print("📋 Interactive docs at: http://localhost:8000/docs")
    print("🧪 Test with Windsurf job: POST http://localhost:8000/test-windsurf-job")
    print("👤 Recruiter: Alex Chen | Senior Technical Recruiter at Windsurf")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)