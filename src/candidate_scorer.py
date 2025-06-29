#!/usr/bin/env python3
"""
AI-Powered Candidate Scoring System for LinkedIn Sourcing Agent
Implements Synapse's scoring rubric with AI analysis
"""

import os
import logging
import json
from typing import List, Dict, Any, Optional
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CandidateScorer:
    """
    AI-powered candidate scoring system using Synapse's rubric:
    - Education (20%)
    - Career Trajectory (20%) 
    - Company Relevance (15%)
    - Skills Match (25%)
    - Location Match (10%)
    - Tenure (10%)
    """
    
    def __init__(self):
        """Initialize the scorer with AI client and scoring weights."""
        try:
            self.groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
            self.ai_available = True
            logger.info("AI client initialized successfully")
        except Exception as e:
            logger.warning(f"AI client failed to initialize: {e}")
            self.ai_available = False
        
        # Scoring weights from Synapse rubric
        self.weights = {
            'education': 0.20,
            'trajectory': 0.20,
            'company': 0.15,
            'skills': 0.25,  # Most important factor
            'location': 0.10,
            'tenure': 0.10
        }
        
        # Elite institutions for education scoring
        self.elite_schools = {
            'mit', 'stanford', 'harvard', 'berkeley', 'cmu', 'caltech',
            'princeton', 'yale', 'columbia', 'cornell', 'uiuc', 'georgia tech'
        }
        
        # Top companies for company scoring  
        self.top_companies = {
            'google', 'apple', 'microsoft', 'amazon', 'meta', 'tesla',
            'openai', 'anthropic', 'deepmind', 'nvidia', 'stripe', 'airbnb'
        }

    def score_education(self, candidate: Dict[str, Any]) -> float:
        """
        Score education based on school prestige and clear progression.
        Returns score 1-10.
        """
        company = candidate.get('company', '').lower()
        headline = candidate.get('headline', '').lower()
        
        # Check if candidate comes from elite companies (often indicates good education)
        if any(elite in company for elite in self.elite_schools):
            return 9.5
        
        # Check for advanced degrees or research roles
        if any(term in headline for term in ['phd', 'research', 'scientist', 'principal']):
            return 8.5
        
        # Check for senior roles (indicates progression)
        if any(term in headline for term in ['senior', 'lead', 'staff', 'director']):
            return 7.5
        
        # Default for standard experience
        return 6.0
    
    def score_trajectory(self, candidate: Dict[str, Any]) -> float:
        """
        Score career trajectory based on role seniority and progression.
        Returns score 1-10.
        """
        headline = candidate.get('headline', '').lower()
        
        # Excellent progression indicators
        if any(term in headline for term in ['principal', 'staff', 'director', 'vp']):
            return 9.0
        
        # Good progression
        elif any(term in headline for term in ['senior', 'lead', 'manager']):
            return 7.5
        
        # Some progression
        elif any(term in headline for term in ['engineer', 'developer', 'scientist']):
            return 6.0
        
        # Limited progression indicators
        else:
            return 4.0
    
    def score_company_relevance(self, candidate: Dict[str, Any]) -> float:
        """
        Score based on company tier and industry relevance.
        Returns score 1-10.
        """
        company = candidate.get('company', '').lower()
        
        # Top tier tech companies
        if any(top_company in company for top_company in self.top_companies):
            return 9.5
        
        # Well-known tech companies or startups
        tech_indicators = ['tech', 'ai', 'ml', 'software', 'data', 'cloud']
        if any(indicator in company for indicator in tech_indicators):
            return 7.5
        
        # Any professional experience
        return 5.5

    def score_skills_match_with_ai(self, candidate: Dict[str, Any], job_description: str) -> float:
        """
        Use AI to analyze skills match between candidate and job.
        Returns score 1-10.
        """
        if not self.ai_available:
            return self.score_skills_match_fallback(candidate, job_description)
        
        try:
            candidate_profile = f"""
            Name: {candidate.get('name', 'Unknown')}
            Headline: {candidate.get('headline', 'No headline')}
            Company: {candidate.get('company', 'No company')}
            """
            
            prompt = f"""
            Analyze this candidate's skills match for the job:

            CANDIDATE PROFILE:
            {candidate_profile}

            JOB DESCRIPTION:
            {job_description}

            Rate the skills match from 1-10 where:
            - 9-10: Perfect match, candidate has all key skills
            - 7-8: Strong match, candidate has most important skills
            - 5-6: Some relevant skills, moderate fit
            - 3-4: Limited relevant skills
            - 1-2: Poor match, few relevant skills

            Respond with just a number from 1-10.
            """
            
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                max_tokens=10,
                temperature=0.1
            )
            
            # Extract numeric score
            content = response.choices[0].message.content.strip()
            score = float(content)
            
            # Ensure score is in valid range
            return max(1.0, min(10.0, score))
            
        except Exception as e:
            logger.warning(f"AI skills analysis failed: {e}")
            return self.score_skills_match_fallback(candidate, job_description)
    
    def score_skills_match_fallback(self, candidate: Dict[str, Any], job_description: str) -> float:
        """
        Fallback skills matching without AI.
        Returns score 1-10.
        """
        headline = candidate.get('headline', '').lower()
        job_desc_lower = job_description.lower()
        
        # Extract key skills from job description
        key_skills = ['ml', 'machine learning', 'ai', 'python', 'tensorflow', 'pytorch', 
                     'research', 'engineer', 'software', 'data', 'algorithm']
        
        matches = 0
        for skill in key_skills:
            if skill in headline and skill in job_desc_lower:
                matches += 1
        
        # Convert matches to score
        if matches >= 4:
            return 9.0
        elif matches >= 2:
            return 7.0
        elif matches >= 1:
            return 5.0
        else:
            return 3.0

    def score_location_match(self, candidate: Dict[str, Any], job_location: str = "Mountain View, CA") -> float:
        """
        Score location match based on proximity to job location.
        Returns score 1-10.
        """
        candidate_location = candidate.get('location', '').lower()
        job_location_lower = job_location.lower()
        
        # Exact city match
        if 'mountain view' in candidate_location or 'palo alto' in candidate_location:
            return 10.0
        
        # Same metro area (Bay Area)
        bay_area_cities = ['san francisco', 'sf', 'menlo park', 'cupertino', 'sunnyvale', 
                          'santa clara', 'san jose', 'redwood city']
        if any(city in candidate_location for city in bay_area_cities):
            return 8.0
        
        # California (easier relocation)
        if 'california' in candidate_location or 'ca' in candidate_location:
            return 6.0
        
        # Remote-friendly roles or major tech hubs
        tech_hubs = ['seattle', 'austin', 'denver', 'boston', 'new york', 'chicago']
        if any(hub in candidate_location for hub in tech_hubs):
            return 6.0
        
        # Other locations
        return 4.0

    def score_tenure(self, candidate: Dict[str, Any]) -> float:
        """
        Score tenure stability based on role indicators.
        Returns score 1-10.
        """
        headline = candidate.get('headline', '').lower()
        
        # Senior roles typically indicate good tenure
        if any(term in headline for term in ['senior', 'principal', 'staff', 'lead']):
            return 8.5
        
        # Standard engineering roles
        elif 'engineer' in headline:
            return 7.0
        
        # Newer or unclear roles
        else:
            return 6.0

    def calculate_weighted_score(self, scores: Dict[str, float]) -> float:
        """
        Calculate final weighted score using Synapse's rubric.
        Returns score 1-10.
        """
        weighted_sum = 0.0
        for factor, score in scores.items():
            if factor in self.weights:
                weighted_sum += score * self.weights[factor]
        
        return round(weighted_sum, 1)

    def score_candidate(self, candidate: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """
        Score a single candidate using all factors.
        Returns detailed scoring breakdown.
        """
        logger.info(f"Scoring candidate: {candidate.get('name', 'Unknown')}")
        
        # Calculate individual scores
        scores = {
            'education': self.score_education(candidate),
            'trajectory': self.score_trajectory(candidate),
            'company': self.score_company_relevance(candidate),
            'skills': self.score_skills_match_with_ai(candidate, job_description),
            'location': self.score_location_match(candidate),
            'tenure': self.score_tenure(candidate)
        }
        
        # Calculate weighted final score
        final_score = self.calculate_weighted_score(scores)
        
        # Create detailed result
        result = {
            'candidate': candidate,
            'final_score': final_score,
            'score_breakdown': scores,
            'scoring_rationale': {
                'education': f"Education/Background: {scores['education']}/10",
                'trajectory': f"Career Trajectory: {scores['trajectory']}/10", 
                'company': f"Company Relevance: {scores['company']}/10",
                'skills': f"Skills Match: {scores['skills']}/10",
                'location': f"Location Match: {scores['location']}/10",
                'tenure': f"Tenure Stability: {scores['tenure']}/10"
            }
        }
        
        return result

    def score_multiple_candidates(self, candidates: List[Dict[str, Any]], job_description: str) -> List[Dict[str, Any]]:
        """
        Score multiple candidates and return sorted by score.
        """
        logger.info(f"Scoring {len(candidates)} candidates")
        
        scored_candidates = []
        for candidate in candidates:
            try:
                scored_candidate = self.score_candidate(candidate, job_description)
                scored_candidates.append(scored_candidate)
            except Exception as e:
                logger.error(f"Failed to score candidate {candidate.get('name', 'Unknown')}: {e}")
                continue
        
        # Sort by final score (highest first)
        scored_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        return scored_candidates


def test_scoring():
    """Test the scoring system with mock candidates."""
    
    # Mock candidates (same as Phase 2 output)
    mock_candidates = [
        {
            'name': 'Sarah Chen',
            'linkedin_url': 'https://linkedin.com/in/sarah-chen-ml',
            'headline': 'Senior ML Engineer at OpenAI',
            'company': 'OpenAI',
            'location': 'San Francisco, CA'
        },
        {
            'name': 'Alex Kumar', 
            'linkedin_url': 'https://linkedin.com/in/alex-kumar-ai',
            'headline': 'AI Research Scientist at Google DeepMind',
            'company': 'Google DeepMind',
            'location': 'Mountain View, CA'
        },
        {
            'name': 'Maria Rodriguez',
            'linkedin_url': 'https://linkedin.com/in/maria-rodriguez-dev',
            'headline': 'Full Stack Engineer at Meta',
            'company': 'Meta', 
            'location': 'Menlo Park, CA'
        },
        {
            'name': 'James Wu',
            'linkedin_url': 'https://linkedin.com/in/james-wu-engineer', 
            'headline': 'Backend Engineer at Stripe',
            'company': 'Stripe',
            'location': 'San Francisco, CA'
        },
        {
            'name': 'Priya Patel',
            'linkedin_url': 'https://linkedin.com/in/priya-patel-ml',
            'headline': 'Machine Learning Engineer at Anthropic', 
            'company': 'Anthropic',
            'location': 'San Francisco, CA'
        }
    ]
    
    # Windsurf job description
    job_description = """
    Software Engineer, ML Research
    Windsurf • Full Time • Mountain View, CA • On-site • $140,000 – $300,000 + Equity
    
    About the Company:
    Windsurf (formerly Codeium) is a Forbes AI 50 company building the future of developer productivity through AI.
    
    Roles and Responsibilities:
    • Train and fine-tune LLMs focused on developer productivity
    • Design and prioritize experiments for product impact
    • Analyze results, conduct ablation studies, and document findings
    • Convert ML discoveries into scalable product features
    
    Job Requirements:
    • 2+ years in software engineering with fast promotions
    • Strong software engineering and systems thinking skills
    • Proven experience training and iterating on large production neural networks
    • Strong GPA from a top CS undergrad program (MIT, Stanford, CMU, UIUC, etc.)
    • Familiarity with tools like Copilot, ChatGPT, or Windsurf is preferred
    """
    
    # Initialize scorer and test
    scorer = CandidateScorer()
    
    # Score all candidates
    scored_candidates = scorer.score_multiple_candidates(mock_candidates, job_description)
    
    # Display results
    print("\n🎯 Candidate Scoring Results:")
    print("=" * 60)
    
    for i, result in enumerate(scored_candidates, 1):
        candidate = result['candidate']
        score = result['final_score']
        breakdown = result['score_breakdown']
        
        print(f"\n{i}. {candidate['name']} - Score: {score}/10")
        print(f"   Company: {candidate['company']}")
        print(f"   Location: {candidate['location']}")
        print(f"   Breakdown:")
        print(f"     • Education: {breakdown['education']}/10 (20% weight)")
        print(f"     • Trajectory: {breakdown['trajectory']}/10 (20% weight)")
        print(f"     • Company: {breakdown['company']}/10 (15% weight)")
        print(f"     • Skills: {breakdown['skills']}/10 (25% weight)")
        print(f"     • Location: {breakdown['location']}/10 (10% weight)")
        print(f"     • Tenure: {breakdown['tenure']}/10 (10% weight)")
    
    print(f"\n✅ Successfully scored {len(scored_candidates)} candidates!")
    return scored_candidates


if __name__ == "__main__":
    test_scoring()