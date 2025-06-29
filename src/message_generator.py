#!/usr/bin/env python3
"""
Enhanced LinkedIn Outreach Message Generator with Recruiter Persona
Generates personalized messages with complete recruiter information
"""

import os
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OutreachMessage:
    candidate_name: str
    message: str
    message_length: int
    personalization_elements: List[str]

class OutreachGenerator:
    def __init__(self):
        """Initialize the message generator with recruiter persona."""
        try:
            from groq import Groq
            self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
            logger.info("AI client initialized successfully")
        except Exception as e:
            logger.error(f"AI client initialization failed: {e}")
            self.client = None
        
        # Recruiter persona
        self.recruiter_info = {
            "name": "Alex Chen",
            "title": "Senior Technical Recruiter",
            "company": "Windsurf",
            "linkedin": "https://linkedin.com/in/alex-chen-recruiter",
            "email": "alex.chen@windsurf.com"
        }
    
    def _clean_message(self, message: str) -> str:
        """Clean the message by removing any introductory text."""
        # List of common introductory phrases to remove
        intros = [
            "Here's a personalized LinkedIn outreach message:",
            "Here is a personalized LinkedIn outreach message:",
            "Here's a LinkedIn outreach message:",
            "Here is a LinkedIn outreach message:",
            "Here's an outreach message:",
            "Here is an outreach message:",
            "Here's a message:",
            "Here is a message:",
            "Here's the message:",
            "Here is the message:",
            "Here's a personalized message:",
            "Here is a personalized message:",
        ]
        
        # Remove any introductory text
        message = message.strip()
        for intro in intros:
            if message.lower().startswith(intro.lower()):
                message = message[len(intro):].strip()
        
        # If message still starts with "Here" or similar, try to find the first greeting
        if message.lower().startswith(("here", "this")):
            lines = message.split('\n')
            for i, line in enumerate(lines):
                if line.strip().lower().startswith(('hi ', 'hello ', 'dear ')):
                    message = '\n'.join(lines[i:]).strip()
                    break
        
        return message

    def generate_message(self, candidate: Dict[str, Any], job_description: str) -> OutreachMessage:
        """Generate a personalized outreach message for a single candidate."""
        
        # Enhanced AI prompt with specific recruiter information
        prompt = f"""
You are {self.recruiter_info['name']}, a {self.recruiter_info['title']} at {self.recruiter_info['company']}. 

Write a personalized LinkedIn outreach message for this candidate:
- Name: {candidate['name']}
- Current Role: {candidate['headline']}
- Company: {candidate['company']}
- Location: {candidate['location']}

Job Description Summary:
{job_description[:500]}...

IMPORTANT MESSAGE FORMAT REQUIREMENTS:
1. Start DIRECTLY with "Hi [Name]" or similar greeting
2. DO NOT include ANY introductory text or phrases like:
   - "Here's a message"
   - "Here is a personalized message"
   - Any other introductory text
3. Keep message under 150 words
4. Be professional but friendly
5. Reference their specific company and experience
6. Explain why they're a good fit for this ML role
7. Include clear next steps
8. End with this exact signature:

Best regards,
{self.recruiter_info['name']} | {self.recruiter_info['title']} at {self.recruiter_info['company']}
LinkedIn: {self.recruiter_info['linkedin']}
Email: {self.recruiter_info['email']}

Make it sound natural and personalized, referencing their background at {candidate['company']}.
"""

        try:
            if self.client:
                response = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama3-8b-8192",
                    max_tokens=400,
                    temperature=0.7
                )
                message = response.choices[0].message.content.strip()
                
                # Clean the message to remove any introductory text
                message = self._clean_message(message)
            else:
                # Fallback template with complete recruiter info
                message = self._generate_fallback_message(candidate, job_description)
            
            # Analyze personalization elements
            personalization = self._analyze_personalization(message, candidate)
            
            return OutreachMessage(
                candidate_name=candidate['name'],
                message=message,
                message_length=len(message),
                personalization_elements=personalization
            )
            
        except Exception as e:
            logger.error(f"Message generation failed for {candidate['name']}: {e}")
            return OutreachMessage(
                candidate_name=candidate['name'],
                message=self._generate_fallback_message(candidate, job_description),
                message_length=0,
                personalization_elements=["Fallback template used"]
            )
    
    def _generate_fallback_message(self, candidate: Dict[str, Any], job_description: str) -> str:
        """Generate a professional fallback message with complete recruiter details."""
        
        return f"""Hi {candidate['name']},

I came across your profile and was impressed by your experience as {candidate['headline']} at {candidate['company']}. Your background in machine learning and software engineering aligns perfectly with an exciting ML Research Engineer opportunity we have at Windsurf.

Windsurf is building the future of developer productivity through AI, and we're looking for talented engineers like yourself to join our team in Mountain View, CA. The role offers competitive compensation ($140K-$300K + equity) and the chance to work on cutting-edge LLM technology.

I'd love to discuss how your experience at {candidate['company']} could contribute to our mission. Would you be open to a brief conversation about this opportunity?

Best regards,
{self.recruiter_info['name']} | {self.recruiter_info['title']} at {self.recruiter_info['company']}
LinkedIn: {self.recruiter_info['linkedin']}
Email: {self.recruiter_info['email']}"""
    
    def _analyze_personalization(self, message: str, candidate: Dict[str, Any]) -> List[str]:
        """Analyze what personalization elements are present in the message."""
        elements = []
        
        if candidate['name'].split()[0] in message:
            elements.append("First name usage")
        if candidate['company'] in message:
            elements.append(f"Company mention ({candidate['company']})")
        if any(word in message.lower() for word in ['experience', 'background', 'work']):
            elements.append("Experience reference")
        if any(word in message.lower() for word in ['ml', 'machine learning', 'ai', 'engineer']):
            elements.append("Technical skills match")
        if any(word in message.lower() for word in ['windsurf', 'mountain view', 'compensation']):
            elements.append("Company-specific details")
        
        return elements
    
    def generate_batch_messages(self, candidates: List[Dict[str, Any]], job_description: str, top_n: int = 3) -> List[OutreachMessage]:
        """Generate messages for multiple candidates."""
        messages = []
        
        for candidate in candidates[:top_n]:
            logger.info(f"Generating message for: {candidate['name']}")
            message = self.generate_message(candidate, job_description)
            messages.append(message)
        
        return messages

def test_message_generation():
    """Test the enhanced message generator."""
    print("🧪 Testing Enhanced Message Generator with Recruiter Details...")
    print("=" * 80)
    
    # Sample candidates with scores
    candidates = [
        {
            "name": "Sarah Chen",
            "linkedin_url": "https://linkedin.com/in/sarah-chen-ml",
            "headline": "Senior ML Engineer at OpenAI", 
            "company": "OpenAI",
            "location": "San Francisco, CA",
            "fit_score": 8.1
        },
        {
            "name": "Alex Kumar",
            "linkedin_url": "https://linkedin.com/in/alex-kumar-ai",
            "headline": "AI Research Scientist at Google DeepMind",
            "company": "Google DeepMind", 
            "location": "Mountain View, CA",
            "fit_score": 7.9
        },
        {
            "name": "Priya Patel",
            "linkedin_url": "https://linkedin.com/in/priya-patel-ml",
            "headline": "Machine Learning Engineer at Anthropic",
            "company": "Anthropic",
            "location": "San Francisco, CA", 
            "fit_score": 7.3
        }
    ]
    
    job_description = """
    Software Engineer, ML Research at Windsurf
    Mountain View, CA • $140,000 – $300,000 + Equity
    
    Requirements:
    • 2+ years in software engineering with fast promotions
    • Proven experience training and iterating on large production neural networks
    • Strong GPA from a top CS undergrad program (MIT, Stanford, CMU, UIUC, etc.)
    • Must be able to work in Mountain View, CA full-time onsite
    """
    
    generator = OutreachGenerator()
    messages = generator.generate_batch_messages(candidates, job_description, top_n=3)
    
    print("💬 Enhanced Personalized Outreach Messages:")
    print("=" * 80)
    
    total_length = 0
    for i, message in enumerate(messages, 1):
        print(f"\n{i}. {message.candidate_name} ({candidates[i-1]['fit_score']}/10)")
        print(f"   Company: {candidates[i-1]['company']}")
        print(f"   LinkedIn: {candidates[i-1]['linkedin_url']}")
        print(f"   Message Length: {message.message_length} characters")
        print(f"   Personalization: {', '.join(message.personalization_elements)}")
        print(f"\n   MESSAGE:")
        print(f"   {message.message}")
        print("-" * 80)
        total_length += message.message_length
    
    avg_length = total_length / len(messages) if messages else 0
    print(f"\n✅ Generated {len(messages)} personalized messages!")
    print(f"📊 Average message length: {int(avg_length)} characters")
    print("🎯 All messages include complete recruiter contact information!")

if __name__ == "__main__":
    test_message_generation()