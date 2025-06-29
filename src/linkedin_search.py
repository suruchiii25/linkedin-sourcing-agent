#!/usr/bin/env python3
"""
LinkedIn Profile Search Module

This module searches for LinkedIn profiles using Google search and extracts
basic candidate information from search results.
"""

import time
import re
import requests
from typing import List, Dict, Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from googlesearch import search
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LinkedInSearcher:
    """
    Searches for LinkedIn profiles based on job descriptions.
    """
    
    def __init__(self, max_results: int = 25, search_delay: float = 5):
        """
        Initialize the LinkedIn searcher.
        
        Args:
            max_results: Maximum number of profiles to find
            search_delay: Delay between searches to avoid rate limiting
        """
        self.max_results = max_results
        self.search_delay = search_delay
        
    def extract_job_keywords(self, job_description: str) -> Dict[str, List[str]]:
        """
        Extract key terms from job description for better search targeting.
        
        Args:
            job_description: The job posting text
            
        Returns:
            Dictionary with categorized keywords
        """
        # Convert to lowercase for analysis
        text = job_description.lower()
        
        # Define keyword categories
        tech_skills = [
            'python', 'javascript', 'react', 'node.js', 'aws', 'docker', 
            'kubernetes', 'machine learning', 'ml', 'ai', 'tensorflow',
            'pytorch', 'llm', 'neural networks', 'backend', 'frontend',
            'fullstack', 'devops', 'cloud', 'microservices'
        ]
        
        companies = [
            'google', 'microsoft', 'amazon', 'meta', 'netflix', 'uber',
            'airbnb', 'stripe', 'openai', 'anthropic', 'startup', 'fintech'
        ]
        
        roles = [
            'engineer', 'developer', 'architect', 'lead', 'senior',
            'principal', 'staff', 'manager', 'director'
        ]
        
        # Extract relevant keywords found in job description
        found_skills = [skill for skill in tech_skills if skill in text]
        found_companies = [company for company in companies if company in text]
        found_roles = [role for role in roles if role in text]
        
        return {
            'skills': found_skills[:3],  # Top 3 most relevant
            'companies': found_companies[:3],
            'roles': found_roles[:2]
        }
    
    def build_search_queries(self, job_description: str) -> List[str]:
        """
        Build targeted Google search queries for LinkedIn profiles.
        
        Args:
            job_description: Job posting text
            
        Returns:
            List of search query strings
        """
        keywords = self.extract_job_keywords(job_description)
        
        queries = []
        
        # Base LinkedIn search
        base_query = 'site:linkedin.com/in'
        
        # Query 1: Skills-focused
        if keywords['skills']:
            skills_query = f'{base_query} "{keywords["skills"][0]}"'
            if len(keywords['skills']) > 1:
                skills_query += f' "{keywords["skills"][1]}"'
            queries.append(skills_query)
        
        # Query 2: Company + role focused
        if keywords['companies'] and keywords['roles']:
            company_query = f'{base_query} "{keywords["companies"][0]}" "{keywords["roles"][0]}"'
            queries.append(company_query)
        
        # Query 3: General role-based
        if keywords['roles']:
            role_query = f'{base_query} "{keywords["roles"][0]}"'
            if 'engineer' in keywords['roles']:
                role_query += ' "software engineer"'
            queries.append(role_query)
        
        # Fallback query if no keywords found
        if not queries:
            queries.append(f'{base_query} "software engineer"')
        
        return queries[:2]  # Limit to 2 queries to avoid rate limiting
    
    def search_linkedin_profiles(self, job_description: str) -> List[Dict]:
        """
        Search for LinkedIn profiles based on job description.
        For now, returns mock data to avoid rate limiting.
        
        Args:
            job_description: Job posting text
            
        Returns:
            List of candidate dictionaries
        """
        logger.info("Starting candidate search...")
        
        # For now, using mock data for faster development and to avoid rate limits
        mock_candidates = [
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
        
        logger.info(f"Found {len(mock_candidates)} potential candidates")
        return mock_candidates
    
    def extract_profile_info(self, profile_urls: List[str]) -> List[Dict]:
        """
        Extract basic information from LinkedIn profile URLs.
        Since we can't directly scrape LinkedIn, we'll extract what we can
        from the URL structure and search snippets.
        
        Args:
            profile_urls: List of LinkedIn profile URLs
            
        Returns:
            List of candidate dictionaries with basic info
        """
        candidates = []
        
        for url in profile_urls:
            try:
                # Extract username from URL
                username = url.split('/in/')[-1].split('/')[0]
                
                # Try to get additional info from Google search snippet
                snippet_info = self._get_profile_snippet(url)
                
                candidate = {
                    'linkedin_url': url,
                    'username': username,
                    'name': snippet_info.get('name', username.replace('-', ' ').title()),
                    'headline': snippet_info.get('headline', ''),
                    'location': snippet_info.get('location', ''),
                    'current_company': snippet_info.get('company', ''),
                    'raw_snippet': snippet_info.get('snippet', '')
                }
                
                candidates.append(candidate)
                
            except Exception as e:
                logger.warning(f"Failed to extract info from {url}: {e}")
                continue
        
        return candidates
    
    def _get_profile_snippet(self, profile_url: str) -> Dict:
        """
        Try to get additional profile information from search snippets.
        This is a best-effort approach using public search data.
        
        Args:
            profile_url: LinkedIn profile URL
            
        Returns:
            Dictionary with extracted information
        """
        try:
            # Search for this specific profile to get snippet
            search_query = f'"{profile_url}"'
            
            # Use requests to get search results page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for search result snippets
                snippets = soup.find_all('div', class_='VwiC3b')
                
                for snippet in snippets:
                    text = snippet.get_text()
                    if 'linkedin.com' in text.lower():
                        return self._parse_snippet_text(text)
            
            return {}
            
        except Exception as e:
            logger.debug(f"Could not get snippet for {profile_url}: {e}")
            return {}
    
    def _parse_snippet_text(self, snippet_text: str) -> Dict:
        """
        Parse LinkedIn profile information from search snippet text.
        
        Args:
            snippet_text: Raw snippet text from search results
            
        Returns:
            Dictionary with parsed information
        """
        info = {'snippet': snippet_text}
        
        # Try to extract name (usually at the beginning)
        lines = snippet_text.split('\n')
        if lines:
            potential_name = lines[0].strip()
            if len(potential_name.split()) <= 4 and potential_name[0].isupper():
                info['name'] = potential_name
        
        # Look for job titles and companies
        for line in lines:
            line = line.strip()
            if ' at ' in line and len(line) < 100:
                parts = line.split(' at ')
                if len(parts) == 2:
                    info['headline'] = parts[0].strip()
                    info['company'] = parts[1].strip()
                    break
        
        return info
    
    def get_mock_candidates(self) -> List[Dict]:
        """
        Return mock candidate data for development and testing.
        This helps us continue building even when search APIs are rate-limited.
        """
        return [
            {
                'linkedin_url': 'https://linkedin.com/in/sarah-chen-ml',
                'username': 'sarah-chen-ml',
                'name': 'Sarah Chen',
                'headline': 'Senior ML Engineer at OpenAI',
                'location': 'San Francisco, CA',
                'current_company': 'OpenAI',
                'raw_snippet': 'ML Engineer with 5 years experience in LLMs and neural networks'
            },
            {
                'linkedin_url': 'https://linkedin.com/in/alex-kumar-ai',
                'username': 'alex-kumar-ai',
                'name': 'Alex Kumar',
                'headline': 'AI Research Scientist at Google DeepMind',
                'location': 'Mountain View, CA',
                'current_company': 'Google DeepMind',
                'raw_snippet': 'PhD in CS from Stanford, specialized in transformer architectures'
            },
            {
                'linkedin_url': 'https://linkedin.com/in/maria-rodriguez-dev',
                'username': 'maria-rodriguez-dev',
                'name': 'Maria Rodriguez',
                'headline': 'Full Stack Engineer at Meta',
                'location': 'Menlo Park, CA',
                'current_company': 'Meta',
                'raw_snippet': 'Software engineer with ML background, 3 years at FAANG companies'
            },
            {
                'linkedin_url': 'https://linkedin.com/in/james-wu-engineer',
                'username': 'james-wu-engineer',
                'name': 'James Wu',
                'headline': 'Backend Engineer at Stripe',
                'location': 'San Francisco, CA',
                'current_company': 'Stripe',
                'raw_snippet': 'MIT graduate, expert in distributed systems and Python'
            },
            {
                'linkedin_url': 'https://linkedin.com/in/priya-patel-ml',
                'username': 'priya-patel-ml',
                'name': 'Priya Patel',
                'headline': 'Machine Learning Engineer at Anthropic',
                'location': 'San Francisco, CA',
                'current_company': 'Anthropic',
                'raw_snippet': 'Carnegie Mellon CS grad, 4 years in production ML systems'
            }
        ]
    
    def search_candidates(self, job_description: str, use_mock: bool = True) -> List[Dict]:
        """
        Main search function that coordinates the search process.
        
        Args:
            job_description: Job posting text
            use_mock: Whether to use mock data (default True)
            
        Returns:
            List of candidate dictionaries
        """
        try:
            if use_mock:
                return self.search_linkedin_profiles(job_description)
            
            # Real search implementation (disabled for now)
            queries = self.build_search_queries(job_description)
            logger.info(f"Generated {len(queries)} search queries")
            
            profile_urls = []
            for query in queries:
                try:
                    # Use Google search API
                    search_results = search(query, num_results=5)
                    profile_urls.extend([url for url in search_results if 'linkedin.com/in/' in url])
                    time.sleep(self.search_delay)  # Respect rate limits
                except Exception as e:
                    logger.warning(f"Search failed for query '{query}': {e}")
                    continue
            
            # Remove duplicates while preserving order
            profile_urls = list(dict.fromkeys(profile_urls))
            
            if not profile_urls:
                logger.warning("No LinkedIn profiles found")
                return []
            
            # Extract info from profiles
            candidates = self.extract_profile_info(profile_urls[:self.max_results])
            logger.info(f"Successfully processed {len(candidates)} candidates")
            return candidates
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

# Test function
def test_linkedin_search():
    """Test the LinkedIn search functionality."""
    
    # Sample job description (the Windsurf ML Engineer role)
    windsurf_job = """
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
    • Must be able to work in Mountain View, CA full-time onsite
    """
    
    # Initialize searcher with mock data enabled
    searcher = LinkedInSearcher(max_results=5)
    
    # Search for candidates (will use mock data if search fails)
    candidates = searcher.search_candidates(windsurf_job, use_mock=True)
    
    # Display results
    print(f"\n🔍 Found {len(candidates)} candidates:")
    print("=" * 60)
    
    for i, candidate in enumerate(candidates, 1):
        print(f"\n{i}. {candidate['name']}")
        print(f"   LinkedIn: {candidate['linkedin_url']}")
        print(f"   Headline: {candidate['headline']}")
        print(f"   Company: {candidate['current_company']}")
        if candidate['location']:
            print(f"   Location: {candidate['location']}")

if __name__ == "__main__":
    test_linkedin_search()