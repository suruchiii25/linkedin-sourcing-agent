#!/usr/bin/env python3
"""
Enhanced AI-Powered Candidate Scoring System
Improved algorithm with better accuracy and more sophisticated analysis
"""

import os
import json
import logging
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from groq import Groq
from dotenv import load_dotenv
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ScoringWeights:
    """Synapse's official scoring weights"""
    education: float = 0.20
    trajectory: float = 0.20
    company: float = 0.15
    skills: float = 0.25  # Most important factor
    location: float = 0.10
    tenure: float = 0.10

@dataclass
class CandidateProfile:
    """Enhanced candidate profile with more detailed information"""
    name: str
    linkedin_url: str
    headline: str
    company: str
    location: str
    # Enhanced fields for better scoring
    experience_years: Optional[int] = None
    education_level: Optional[str] = None
    previous_companies: Optional[List[str]] = None
    skills_mentioned: Optional[List[str]] = None
    job_titles: Optional[List[str]] = None

class EnhancedCandidateScorer:
    """Enhanced AI-powered candidate scoring with improved accuracy"""
    
    def __init__(self):
        """Initialize the enhanced scoring system"""
        try:
            load_dotenv()
        except Exception as e:
            logger.warning(f"Failed to load .env file: {e}")
        
        self.client = None
        self.weights = ScoringWeights()
        
        # Enhanced company tiers with more comprehensive mapping
        self.company_tiers = {
            'tier_1': {
                'companies': ['google', 'meta', 'amazon', 'apple', 'microsoft', 'netflix', 'tesla', 
                            'openai', 'anthropic', 'deepmind', 'nvidia', 'spacex', 'stripe', 'uber',
                            'airbnb', 'salesforce', 'oracle', 'adobe', 'intel', 'qualcomm'],
                'score': 9.5
            },
            'tier_2': {
                'companies': ['spotify', 'snapchat', 'twitter', 'linkedin', 'pinterest', 'reddit',
                            'dropbox', 'slack', 'zoom', 'shopify', 'square', 'coinbase', 'robinhood',
                            'databricks', 'snowflake', 'palantir', 'atlassian', 'figma'],
                'score': 8.5
            },
            'tier_3': {
                'companies': ['startup', 'series a', 'series b', 'unicorn', 'ycombinator', 'techstars'],
                'score': 7.0
            },
            'default': {'score': 6.0}
        }
        
        # Enhanced education institution mapping
        self.education_tiers = {
            'elite': {
                'schools': ['mit', 'stanford', 'harvard', 'cmu', 'berkeley', 'caltech', 'princeton',
                          'yale', 'columbia', 'cornell', 'upenn', 'chicago', 'northwestern',
                          'duke', 'johns hopkins', 'rice', 'vanderbilt', 'washington university',
                          'georgia tech', 'uiuc', 'university of illinois', 'carnegie mellon'],
                'score': 9.5
            },
            'strong': {
                'schools': ['ucla', 'usc', 'nyu', 'boston university', 'northeastern', 'purdue',
                          'texas', 'virginia tech', 'north carolina', 'florida', 'ohio state',
                          'penn state', 'michigan', 'wisconsin', 'minnesota', 'colorado'],
                'score': 8.0
            },
            'standard': {
                'schools': ['state university', 'university', 'college', 'institute', 'school'],
                'score': 6.0
            }
        }
        
        # Job seniority levels for trajectory scoring
        self.seniority_levels = {
            'senior': ['senior', 'principal', 'staff', 'lead', 'director', 'head', 'vp', 'chief'],
            'mid': ['engineer', 'developer', 'scientist', 'analyst', 'specialist'],
            'junior': ['junior', 'intern', 'entry', 'associate', 'graduate']
        }
        
        # Try to initialize AI client, but don't fail if it doesn't work
        self._initialize_ai_client()
    
    def _initialize_ai_client(self):
        """Initialize AI client with better error handling"""
        try:
            api_key = os.getenv('GROQ_API_KEY')
            if not api_key:
                logger.warning("GROQ_API_KEY not found in environment")
                return
            
            self.client = Groq(api_key=api_key)
            
            # Test the client with a simple request
            test_response = self.client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10
            )
            if test_response:
                logger.info("Enhanced AI client initialized and tested successfully")
            
        except Exception as e:
            logger.warning(f"AI client initialization failed (will use fallback scoring): {e}")
            self.client = None
    
    def _extract_skills_with_ai(self, profile: CandidateProfile, job_description: str) -> Dict[str, Any]:
        """Enhanced AI-powered skills analysis"""
        if not self.client:
            return self._fallback_skills_analysis(profile, job_description)
        
        try:
            # More sophisticated prompt for better analysis
            prompt = f"""
            Analyze this candidate profile against the job requirements and provide a detailed skills assessment:

            CANDIDATE PROFILE:
            Name: {profile.name}
            Headline: {profile.headline}
            Company: {profile.company}
            Location: {profile.location}
            
            JOB REQUIREMENTS:
            {job_description}
            
            Please analyze and return ONLY a JSON object with this exact structure:
            {{
                "technical_skills_match": <score 1-10>,
                "experience_relevance": <score 1-10>,
                "domain_expertise": <score 1-10>,
                "overall_skills_score": <score 1-10>,
                "key_strengths": ["strength1", "strength2", "strength3"],
                "missing_skills": ["skill1", "skill2"],
                "confidence_level": <score 1-10>,
                "reasoning": "Brief explanation of the scoring"
            }}
            
            Be precise and analytical. Focus on technical skills, domain knowledge, and experience relevance.
            """
            
            response = self.client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3  # Lower temperature for more consistent scoring
            )
            
            # Parse AI response
            result = json.loads(response.choices[0].message.content.strip())
            
            # Validate and clean the response
            required_fields = ['technical_skills_match', 'experience_relevance', 'domain_expertise', 
                             'overall_skills_score', 'confidence_level']
            
            for field in required_fields:
                if field not in result:
                    result[field] = 7.0  # Default score
                else:
                    # Ensure scores are in valid range
                    result[field] = max(1.0, min(10.0, float(result[field])))
            
            logger.info(f"AI skills analysis completed for {profile.name}")
            return result
            
        except Exception as e:
            logger.warning(f"AI skills analysis failed for {profile.name}: {e}")
            return self._fallback_skills_analysis(profile, job_description)
    
    def _fallback_skills_analysis(self, profile: CandidateProfile, job_description: str) -> Dict[str, Any]:
        """Enhanced fallback skills analysis using keyword matching"""
        # Extract key terms from job description
        job_keywords = re.findall(r'\b(?:python|javascript|react|node|sql|aws|docker|kubernetes|'
                                 r'machine learning|ai|tensorflow|pytorch|data science|backend|'
                                 r'frontend|full stack|devops|cloud|microservices|api|database)\b', 
                                 job_description.lower())
        
        # Extract skills from profile
        profile_text = f"{profile.headline} {profile.company}".lower()
        profile_keywords = re.findall(r'\b(?:python|javascript|react|node|sql|aws|docker|kubernetes|'
                                    r'machine learning|ai|tensorflow|pytorch|data science|backend|'
                                    r'frontend|full stack|devops|cloud|microservices|api|database)\b', 
                                    profile_text)
        
        # Calculate match percentage
        if job_keywords:
            matching_skills = set(job_keywords) & set(profile_keywords)
            match_percentage = len(matching_skills) / len(set(job_keywords))
            skills_score = min(10.0, 4.0 + (match_percentage * 6.0))  # Scale to 4-10 range
        else:
            skills_score = 7.0  # Default when no clear keywords found
        
        return {
            'technical_skills_match': skills_score,
            'experience_relevance': skills_score,
            'domain_expertise': skills_score * 0.9,
            'overall_skills_score': skills_score,
            'key_strengths': list(set(profile_keywords))[:3],
            'missing_skills': list(set(job_keywords) - set(profile_keywords))[:2],
            'confidence_level': 6.0,
            'reasoning': f"Keyword-based analysis found {len(set(job_keywords) & set(profile_keywords))} matching skills"
        }
    
    def _score_education(self, profile: CandidateProfile) -> float:
        """Enhanced education scoring with better detection"""
        profile_text = f"{profile.headline} {profile.company}".lower()
        
        # Check for elite institutions
        for school in self.education_tiers['elite']['schools']:
            if school in profile_text:
                return self.education_tiers['elite']['score']
        
        # Check for strong institutions
        for school in self.education_tiers['strong']['schools']:
            if school in profile_text:
                return self.education_tiers['strong']['score']
        
        # Check for PhD/Masters indicators
        if any(degree in profile_text for degree in ['phd', 'ph.d', 'doctorate', 'masters', 'mba']):
            return 8.5
        
        # Default for standard education
        return self.education_tiers['standard']['score']
    
    def _score_trajectory(self, profile: CandidateProfile) -> float:
        """Enhanced career trajectory scoring"""
        headline = profile.headline.lower()
        
        # Check seniority level
        senior_score = 0
        for level, keywords in self.seniority_levels.items():
            for keyword in keywords:
                if keyword in headline:
                    if level == 'senior':
                        senior_score = 9.0
                    elif level == 'mid':
                        senior_score = 7.0
                    else:  # junior
                        senior_score = 5.0
                    break
            if senior_score > 0:
                break
        
        # Boost for leadership indicators
        leadership_keywords = ['lead', 'manager', 'director', 'head', 'principal', 'staff']
        if any(keyword in headline for keyword in leadership_keywords):
            senior_score = min(10.0, senior_score + 1.5)
        
        return senior_score if senior_score > 0 else 6.5
    
    def _score_company_relevance(self, profile: CandidateProfile) -> float:
        """Enhanced company relevance scoring"""
        company_name = profile.company.lower()
        
        # Check company tiers
        for tier_name, tier_data in self.company_tiers.items():
            if tier_name == 'default':
                continue
            
            for company in tier_data['companies']:
                if company in company_name:
                    return tier_data['score']
        
        # Industry relevance boost
        tech_indicators = ['tech', 'software', 'ai', 'data', 'cloud', 'startup', 'labs']
        if any(indicator in company_name for indicator in tech_indicators):
            return 7.5
        
        return self.company_tiers['default']['score']
    
    def _score_location_match(self, profile: CandidateProfile, job_location: str = "Mountain View, CA") -> float:
        """Enhanced location matching"""
        candidate_location = profile.location.lower()
        job_location = job_location.lower()
        
        # Exact city match
        if "mountain view" in candidate_location or "mv" in candidate_location:
            return 10.0
        
        # Bay Area locations
        bay_area_cities = ["san francisco", "palo alto", "menlo park", "cupertino", "sunnyvale", 
                          "santa clara", "redwood city", "fremont", "oakland", "berkeley"]
        
        if any(city in candidate_location for city in bay_area_cities):
            return 8.5
        
        # California
        if "california" in candidate_location or "ca" in candidate_location:
            return 7.0
        
        # Remote-friendly indicators
        if "remote" in candidate_location or "worldwide" in candidate_location:
            return 6.0
        
        # Default for other locations
        return 4.0
    
    def _score_tenure(self, profile: CandidateProfile) -> float:
        """Enhanced tenure scoring with better pattern detection"""
        headline = profile.headline.lower()
        
        # Look for experience indicators
        experience_patterns = re.findall(r'(\d+)\+?\s*(?:years?|yrs?)', headline)
        
        if experience_patterns:
            years = int(experience_patterns[0])
            if 2 <= years <= 4:
                return 9.5  # Sweet spot
            elif 5 <= years <= 7:
                return 8.5  # Very good
            elif 1 <= years <= 1:
                return 6.0  # Junior but acceptable
            elif years >= 8:
                return 7.5  # Senior but might be overqualified
            else:
                return 5.0
        
        # Seniority-based tenure estimation
        if any(word in headline for word in ['senior', 'lead', 'principal']):
            return 8.0  # Likely 3-5 years
        elif any(word in headline for word in ['junior', 'entry', 'associate']):
            return 6.0  # Likely 1-2 years
        else:
            return 7.0  # Mid-level, likely 2-3 years
    
    def score_candidate(self, profile: CandidateProfile, job_description: str) -> Dict[str, Any]:
        """Enhanced comprehensive candidate scoring"""
        logger.info(f"Scoring candidate with enhanced algorithm: {profile.name}")
        
        # Get AI-powered skills analysis
        skills_analysis = self._extract_skills_with_ai(profile, job_description)
        
        # Calculate individual scores
        education_score = self._score_education(profile)
        trajectory_score = self._score_trajectory(profile)
        company_score = self._score_company_relevance(profile)
        skills_score = skills_analysis['overall_skills_score']
        location_score = self._score_location_match(profile)
        tenure_score = self._score_tenure(profile)
        
        # Calculate weighted total
        total_score = (
            education_score * self.weights.education +
            trajectory_score * self.weights.trajectory +
            company_score * self.weights.company +
            skills_score * self.weights.skills +
            location_score * self.weights.location +
            tenure_score * self.weights.tenure
        )
        
        # Enhanced scoring result with more details
        result = {
            'name': profile.name,
            'company': profile.company,
            'location': profile.location,
            'linkedin_url': profile.linkedin_url,
            'total_score': round(total_score, 1),
            'confidence_level': skills_analysis.get('confidence_level', 7.0),
            'score_breakdown': {
                'education': round(education_score, 1),
                'trajectory': round(trajectory_score, 1),
                'company': round(company_score, 1),
                'skills': round(skills_score, 1),
                'location': round(location_score, 1),
                'tenure': round(tenure_score, 1)
            },
            'weights_used': {
                'education': f"{self.weights.education*100}%",
                'trajectory': f"{self.weights.trajectory*100}%",
                'company': f"{self.weights.company*100}%",
                'skills': f"{self.weights.skills*100}%",
                'location': f"{self.weights.location*100}%",
                'tenure': f"{self.weights.tenure*100}%"
            },
            'skills_analysis': {
                'key_strengths': skills_analysis.get('key_strengths', []),
                'missing_skills': skills_analysis.get('missing_skills', []),
                'technical_match': round(skills_analysis.get('technical_skills_match', 7.0), 1),
                'experience_relevance': round(skills_analysis.get('experience_relevance', 7.0), 1),
                'reasoning': skills_analysis.get('reasoning', 'Standard scoring applied')
            }
        }
        
        return result
    
    def score_candidates_batch(self, candidates: List[CandidateProfile], job_description: str) -> List[Dict[str, Any]]:
        """Score multiple candidates with better error handling"""
        results = []
        for candidate in candidates:
            try:
                result = self.score_candidate(candidate, job_description)
                if result:
                    results.append(result)
                else:
                    logger.warning(f"No score generated for candidate {candidate.name}")
            except Exception as e:
                logger.error(f"Failed to score candidate {candidate.name}: {e}")
                # Add a basic score for failed candidates
                results.append({
                    'name': candidate.name,
                    'linkedin_url': candidate.linkedin_url,
                    'headline': candidate.headline,
                    'company': candidate.company,
                    'location': candidate.location,
                    'total_score': 5.0,  # Default score
                    'score_breakdown': {
                        'education': 5.0,
                        'trajectory': 5.0,
                        'company': 5.0,
                        'skills': 5.0,
                        'location': 5.0,
                        'tenure': 5.0
                    },
                    'skills_analysis': self._fallback_skills_analysis(candidate, job_description)
                })
        
        return results if results else None

# Test function
def test_enhanced_scoring():
    """Test the enhanced scoring system"""
    # Enhanced mock candidates with more realistic data
    candidates = [
        CandidateProfile(
            name="Sarah Chen",
            linkedin_url="https://linkedin.com/in/sarah-chen-ml",
            headline="Senior ML Engineer at OpenAI with 5+ years experience in LLMs and PyTorch",
            company="OpenAI",
            location="San Francisco, CA"
        ),
        CandidateProfile(
            name="Alex Kumar",
            linkedin_url="https://linkedin.com/in/alex-kumar-ai",
            headline="AI Research Scientist at Google DeepMind, PhD from Stanford",
            company="Google DeepMind",
            location="Mountain View, CA"
        ),
        CandidateProfile(
            name="Maria Rodriguez",
            linkedin_url="https://linkedin.com/in/maria-rodriguez-dev",
            headline="Full Stack Engineer at Meta, 3 years experience with React and Node.js",
            company="Meta",
            location="Menlo Park, CA"
        ),
        CandidateProfile(
            name="James Wu",
            linkedin_url="https://linkedin.com/in/james-wu-engineer",
            headline="Principal Backend Engineer at Stripe, 7+ years building scalable systems",
            company="Stripe",
            location="San Francisco, CA"
        ),
        CandidateProfile(
            name="Priya Patel",
            linkedin_url="https://linkedin.com/in/priya-patel-ml",
            headline="Machine Learning Engineer at Anthropic, MIT graduate specializing in NLP",
            company="Anthropic",
            location="San Francisco, CA"
        )
    ]
    
    # Windsurf job description
    job_desc = """
    Software Engineer, ML Research at Windsurf (formerly Codeium)
    Mountain View, CA • $140,000 – $300,000 + Equity
    
    Requirements:
    - 2+ years software engineering with fast promotions
    - Strong software engineering and systems thinking
    - Experience training and iterating on large production neural networks
    - Strong GPA from top CS program (MIT, Stanford, CMU, UIUC, etc.)
    - Familiarity with tools like Copilot, ChatGPT, or Windsurf
    - Deep curiosity for code generation space
    - Prior experience with applied research
    """
    
    # Initialize enhanced scorer
    scorer = EnhancedCandidateScorer()
    
    # Score candidates
    results = scorer.score_candidates_batch(candidates, job_desc)
    
    # Display enhanced results
    print("\n🎯 Enhanced Candidate Scoring Results:")
    print("=" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['name']} - Score: {result['total_score']}/10 (Confidence: {result['confidence_level']}/10)")
        print(f"   Company: {result['company']}")
        print(f"   Location: {result['location']}")
        print(f"   Enhanced Breakdown:")
        
        breakdown = result['score_breakdown']
        weights = result['weights_used']
        
        for factor, score in breakdown.items():
            if factor != 'error':
                weight = weights.get(factor, 'N/A')
                print(f"   • {factor.title()}: {score}/10 ({weight} weight)")
        
        # Show skills analysis
        skills = result['skills_analysis']
        if 'key_strengths' in skills and skills['key_strengths']:
            print(f"   Key Strengths: {', '.join(skills['key_strengths'][:3])}")
        
        if 'missing_skills' in skills and skills['missing_skills']:
            print(f"   Areas for Growth: {', '.join(skills['missing_skills'][:2])}")
        
        if 'reasoning' in skills:
            print(f"   Analysis: {skills['reasoning'][:100]}...")
    
    print(f"\n✅ Enhanced scoring completed for {len(results)} candidates!")
    print(f"📊 Score range: {results[-1]['total_score']:.1f} - {results[0]['total_score']:.1f}")
    print(f"🎯 Average confidence: {sum(r['confidence_level'] for r in results)/len(results):.1f}/10")

if __name__ == "__main__":
    test_enhanced_scoring()