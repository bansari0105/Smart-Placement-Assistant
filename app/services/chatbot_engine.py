"""
Advanced AI Chatbot Engine with NLP, Intent Classification, and Dynamic Reasoning
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from firebase_admin import firestore

logger = logging.getLogger(__name__)


class ChatbotEngine:
    """Advanced chatbot engine with NLP-based intent classification and reasoning."""
    
    def __init__(self, db: firestore.Client):
        self.db = db
        
        # Intent keywords mapping - Enhanced for better detection
        self.intent_keywords = {
            'greeting': ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon'],
            'company_info': ['company', 'about', 'information', 'details', 'what is', 'tell me about'],
            'skills': ['skill', 'technology', 'tech stack', 'programming', 'language', 'framework', 
                      'what skills', 'required skills', 'what skill', 'skills needed', 'skills required',
                      'need to prepare', 'prepare for', 'what to learn', 'technologies', 'tech'],
            'eligibility': ['eligibility', 'qualification', 'requirement', 'cgpa', 'percentage', 
                          'degree', 'education', 'criteria', 'requirements'],
            'package': ['salary', 'package', 'ctc', 'lpa', 'compensation', 'pay', 'stipend', 'earnings'],
            'interview': ['interview', 'round', 'process', 'hiring', 'selection', 'technical', 'hr',
                         'interview process', 'hiring process', 'selection process', 'interview round',
                         'interview stages', 'how to prepare for interview'],
            'experience': ['experience', 'review', 'feedback', 'interview experience', 'placement experience'],
            'resume': ['resume', 'cv', 'curriculum vitae', 'resume tips', 'resume format'],
            'roadmap': ['roadmap', 'path', 'how to prepare', 'preparation', 'study plan', 'learning path'],
            'internship': ['internship', 'intern', 'summer intern', 'winter intern', 'internship opportunity'],
            'placement_drive': ['drive', 'placement drive', 'campus drive', 'recruitment', 'hiring drive', 'upcoming'],
            'tech_stack': ['tech stack', 'technologies', 'tools', 'stack', 'framework', 'library'],
            'location': ['location', 'located', 'where', 'address', 'headquarters', 'office', 'city', 'place'],
        }
        
        # Company name extraction patterns
        self.company_patterns = [
            r'\b(TCS|Tata Consultancy Services)\b',
            r'\b(Infosys)\b',
            r'\b(Wipro)\b',
            r'\b(Accenture)\b',
            r'\b(Cognizant)\b',
            r'\b(Google|Alphabet)\b',
            r'\b(Microsoft|MSFT)\b',
            r'\b(Amazon)\b',
            r'\b(Apple)\b',
            r'\b(Facebook|Meta)\b',
            r'\b(IBM)\b',
            r'\b(Oracle)\b',
            r'\b(Capgemini)\b',
            r'\b(HCL)\b',
            r'\b(Tech Mahindra)\b',
        ]
    
    def classify_intent(self, message: str) -> Tuple[str, float]:
        """
        Classify user intent using keyword matching and pattern recognition.
        Returns: (intent, confidence)
        """
        message_lower = message.lower()
        scores = {}
        
        for intent, keywords in self.intent_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in message_lower:
                    score += 1
            if score > 0:
                scores[intent] = score
        
        if scores:
            best_intent = max(scores, key=scores.get)
            confidence = min(scores[best_intent] / len(self.intent_keywords[best_intent]), 1.0)
            return best_intent, confidence
        
        return 'general', 0.3
    
    def extract_company_name(self, message: str) -> Optional[str]:
        """
        Extract company name from message using advanced NLP techniques.
        Handles ANY company name, not just hardcoded patterns.
        """
        # Clean message: lowercase, remove punctuation
        message_clean = re.sub(r'[^\w\s]', ' ', message.lower())
        words = message_clean.split()
        
        # Remove common stop words
        stop_words = {
            'what', 'is', 'the', 'a', 'an', 'about', 'tell', 'me', 'give', 'me',
            'show', 'me', 'how', 'does', 'do', 'can', 'you', 'i', 'want', 'to',
            'know', 'need', 'required', 'skills', 'eligibility', 'process', 'interview',
            'salary', 'package', 'company', 'info', 'information', 'details'
        }
        filtered_words = [w for w in words if w not in stop_words and len(w) > 2]
        
        if not filtered_words:
            return None
        
        # Strategy 1: Check against known companies in Firestore (with exact matching)
        # IMPROVED: Better matching to avoid false positives like "Meril" vs "Merrill"
        try:
            companies = self.db.collection('companies').limit(100).get()
            best_match = None
            best_score = 0.0
            
            for company_doc in companies:
                company_data = company_doc.to_dict()
                db_company_name = company_data.get('company_name', '').lower()
                if not db_company_name:
                    continue
                
                # Exact match first (highest priority)
                    if db_company_name == message_clean.strip():
                        return company_data.get('company_name')
                
                # For short names (5 chars or less), require very high similarity
                if len(db_company_name) <= 5 or len(message_clean.strip()) <= 5:
                    # Require exact match or very high similarity for short names
                    similarity = self._similarity_score(db_company_name, message_clean.strip())
                    if similarity > 0.9:  # Very high threshold for short names
                        if similarity > best_score:
                            best_match = company_data.get('company_name')
                            best_score = similarity
                    continue
                
                    # Check if all words match with similarity check
                    company_words = db_company_name.split()
                    message_words_set = set(message_clean.split())
                    matched_words = sum(1 for word in company_words if word in message_words_set and len(word) > 2)
                
                    if len(company_words) > 0 and matched_words / len(company_words) >= 0.8:
                        # Additional similarity check to avoid false matches
                        similarity = self._similarity_score(db_company_name, message_clean.strip())
                        if similarity > 0.7:
                            if similarity > best_score:
                                best_match = company_data.get('company_name')
                                best_score = similarity
            
            # Return best match only if score is high enough
            if best_match and best_score > 0.7:
                return best_match
        except Exception as e:
            logger.debug(f"Error checking Firestore companies: {e}")
        
        # Strategy 2: Check knowledge base (with exact matching)
        # IMPROVED: Better matching to avoid false positives
        try:
            kb_companies = self.db.collection('company_knowledge_base').limit(100).get()
            best_match = None
            best_score = 0.0
            
            for kb_doc in kb_companies:
                kb_data = kb_doc.to_dict()
                kb_company_name = kb_data.get('companyName', '').lower()
                if not kb_company_name:
                    continue
                
                    # Exact match first (most reliable)
                    if kb_company_name == message_clean.strip():
                        return kb_data.get('companyName')
                
                # For short names (5 chars or less), require very high similarity
                if len(kb_company_name) <= 5 or len(message_clean.strip()) <= 5:
                    similarity = self._similarity_score(kb_company_name, message_clean.strip())
                    if similarity > 0.9:  # Very high threshold for short names
                        if similarity > best_score:
                            best_match = kb_data.get('companyName')
                            best_score = similarity
                    continue
                
                    # Check if all words match (but require high similarity)
                    company_words = kb_company_name.split()
                    message_words_set = set(message_clean.split())
                    matched_words = sum(1 for word in company_words if word in message_words_set and len(word) > 2)
                    # Require at least 80% word match to avoid false positives
                    if len(company_words) > 0 and matched_words / len(company_words) >= 0.8:
                        # Additional check: company name should be very similar
                        similarity = self._similarity_score(kb_company_name, message_clean.strip())
                        if similarity > 0.7:
                            if similarity > best_score:
                                best_match = kb_data.get('companyName')
                                best_score = similarity
            
            # Return best match only if score is high enough
            if best_match and best_score > 0.7:
                return best_match
        except Exception as e:
            logger.debug(f"Error checking knowledge base: {e}")
        
        # Strategy 3: Extract potential company name from message
        # Look for capitalized words or common company name patterns
        message_original = message
        # Find capitalized words (likely company names)
        capitalized_words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', message_original)
        if capitalized_words:
            # Take the first capitalized phrase (likely the company)
            potential_name = capitalized_words[0]
            # Filter out common words
            if potential_name.lower() not in stop_words and len(potential_name) > 2:
                return potential_name
        
        # Strategy 4: Extract noun phrases (simple heuristic)
        # Look for patterns like "what is X", "tell me about X", "X company"
        patterns = [
            r'what\s+is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'tell\s+me\s+about\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'about\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+company',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+skills',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+eligibility',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message_original, re.IGNORECASE)
            if match:
                potential_name = match.group(1).strip()
                if potential_name.lower() not in stop_words and len(potential_name) > 2:
                    return potential_name
        
        # Strategy 5: If message is short and contains few words, assume first meaningful word is company
        if len(filtered_words) <= 3 and filtered_words:
            # Check if it looks like a company name (not a question word)
            potential = ' '.join(filtered_words[:2]).title()
            if len(potential) > 2:
                return potential
        
        return None
    
    def _similarity_score(self, str1: str, str2: str) -> float:
        """Calculate similarity score between two strings (0-1)."""
        str1 = str1.lower().strip()
        str2 = str2.lower().strip()
        
        # Exact match
        if str1 == str2:
            return 1.0
        
        # For short names (5 chars or less), require exact match to avoid false positives
        if len(str1) <= 5 or len(str2) <= 5:
            # Allow only if one is a substring of the other (e.g., "tcs" in "tcs ltd")
            if str1 in str2 or str2 in str1:
                return 0.9
            # Otherwise, require very high similarity
            if abs(len(str1) - len(str2)) > 1:
                return 0.0  # Different lengths for short names = different companies
        
        # Check if one contains the other (for longer names)
        if len(str1) > 5 and len(str2) > 5:
            if str1 in str2 or str2 in str1:
                return 0.9
        
        # Calculate character overlap (Jaccard similarity)
        set1 = set(str1.replace(' ', ''))
        set2 = set(str2.replace(' ', ''))
        if len(set1) == 0 or len(set2) == 0:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        jaccard = intersection / union if union > 0 else 0.0
        
        # For short names, require higher threshold
        if len(str1) <= 5 or len(str2) <= 5:
            return jaccard if jaccard > 0.85 else 0.0
        
        return jaccard
    
    def search_knowledge_base(self, query: str, company_name: Optional[str] = None) -> Optional[Dict]:
        """
        Search company_knowledge_base collection for relevant information.
        """
        try:
            if company_name:
                # Search by company name
                docs = self.db.collection('company_knowledge_base').where(
                    'companyName', '==', company_name
                ).limit(1).get()
                
                if docs:
                    data = docs[0].to_dict()
                    data['id'] = docs[0].id
                    return data
            
            # Search in all knowledge base entries
            docs = self.db.collection('company_knowledge_base').limit(20).get()
            for doc in docs:
                data = doc.to_dict()
                # Simple keyword matching
                query_lower = query.lower()
                description = (data.get('description', '') or '').lower()
                skills = ' '.join(data.get('skills', [])).lower()
                
                if query_lower in description or query_lower in skills:
                    data['id'] = doc.id
                    return data
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
        
        return None
    
    def search_chat_logs(self, query: str, userId: str) -> Optional[str]:
        """
        Search previous chat logs for similar questions and answers.
        """
        try:
            logs = self.db.collection('chat_logs').where(
                'userId', '==', userId
            ).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10).get()
            
            query_lower = query.lower()
            for log in logs:
                log_data = log.to_dict()
                message = (log_data.get('message', '') or '').lower()
                if query_lower in message or any(word in message for word in query_lower.split()[:3]):
                    return log_data.get('response')
        except Exception as e:
            logger.error(f"Error searching chat logs: {e}")
        
        return None
    
    def generate_response_from_knowledge(self, intent: str, knowledge: Dict, query: str = "") -> str:
        """Generate response from knowledge base data. ChatGPT-like: always provides helpful answer."""
        company_name = knowledge.get('companyName', 'Company')
        query_lower = query.lower()
        
        # Check if query is asking about skills (even if intent is different)
        is_skills_query = (intent == 'skills' or 
                           'skill' in query_lower or 
                           'what skill' in query_lower or
                           'need to prepare' in query_lower or
                           'prepare for' in query_lower)
        
        # Check if query is asking about interview process
        is_interview_query = (intent == 'interview' or
                             'interview process' in query_lower or
                             'interview' in query_lower and 'process' in query_lower or
                             'hiring process' in query_lower or
                             'selection process' in query_lower)
        
        if intent == 'location' or 'where' in query_lower or 'located' in query_lower:
            location = knowledge.get('location', '')
            if location:
                return (f"**{company_name} Location:**\n\n"
                       f"📍 {company_name} is located in **{location}**\n\n"
                       f"🌐 For more details, visit their official website.")
            else:
                return (f"I don't have the location information for {company_name} yet. "
                       f"Let me search for it...\n\n"
                       f"🔍 Searching for {company_name} location information...")
        
        elif is_skills_query:
            skills = knowledge.get('skills', [])
            if skills and len(skills) > 0:
                skills_list = ', '.join(skills[:15])
                # Fix: Extract replace operation to avoid backslash in f-string
                newline_bullet = '\n• '
                formatted_skills = skills_list.replace(', ', newline_bullet)
                return (f"**Skills Required for {company_name}:**\n\n"
                       f"🔧 **Technical Skills:**\n"
                       f"• {formatted_skills}\n\n"
                       f"💡 **Preparation Tips:**\n"
                       f"• Focus on mastering these technologies through hands-on projects\n"
                       f"• Practice coding problems related to these skills on platforms like LeetCode, HackerRank\n"
                       f"• Build real-world projects showcasing these technologies\n"
                       f"• Stay updated with latest trends in these areas\n\n"
                       f"📚 **Recommended Learning Path:**\n"
                       f"• Start with fundamentals, then move to advanced concepts\n"
                       f"• Join online communities and forums for these technologies\n"
                       f"• Contribute to open-source projects using these skills")
            else:
                # ChatGPT-like: Provide helpful answer even without specific data
                return (f"**Skills to Prepare for {company_name}:**\n\n"
                       f"While I'm gathering specific skill requirements for {company_name}, here are the **essential skills** typically needed for tech companies:\n\n"
                       f"🔧 **Core Technical Skills:**\n"
                       f"• **Programming Languages:** Java, Python, C++, JavaScript (depending on role)\n"
                       f"• **Data Structures & Algorithms:** Arrays, Linked Lists, Trees, Graphs, Dynamic Programming\n"
                       f"• **Database:** SQL, NoSQL databases (MongoDB, PostgreSQL)\n"
                       f"• **System Design:** Basic understanding of distributed systems\n"
                       f"• **Version Control:** Git, GitHub\n\n"
                       f"💼 **Additional Skills (Role-Dependent):**\n"
                       f"• **Web Development:** React, Angular, Node.js (for frontend/backend roles)\n"
                       f"• **Cloud Platforms:** AWS, Azure, GCP (for cloud roles)\n"
                       f"• **DevOps:** Docker, Kubernetes, CI/CD (for DevOps roles)\n"
                       f"• **Machine Learning:** Python, TensorFlow, PyTorch (for ML roles)\n\n"
                       f"🔍 **I'm currently searching for {company_name}'s specific requirements. For the most accurate information, I recommend:**\n"
                       f"• Check {company_name}'s official careers page\n"
                       f"• Review recent job postings from {company_name}\n"
                       f"• Connect with {company_name} employees on LinkedIn\n\n"
                       f"Would you like me to search for more specific information about {company_name}?")
        
        elif is_interview_query:
            process = knowledge.get('process', '')
            if process and len(process) > 50:
                return (f"**{company_name} Interview Process:**\n\n"
                       f"{process}\n\n"
                       f"📋 **Preparation Tips:**\n"
                       f"• Research each round thoroughly - understand what's expected\n"
                       f"• Practice common questions for each stage\n"
                       f"• Prepare your questions to ask the interviewer\n"
                       f"• Review company values and recent news\n"
                       f"• Practice mock interviews with friends or mentors\n\n"
                       f"💡 **General Interview Best Practices:**\n"
                       f"• Arrive 10-15 minutes early (or log in early for virtual interviews)\n"
                       f"• Dress professionally\n"
                       f"• Prepare STAR method examples (Situation, Task, Action, Result)\n"
                       f"• Ask thoughtful questions about the role and company")
            else:
                # ChatGPT-like: Provide helpful answer even without specific data
                return (f"**Interview Process for {company_name}:**\n\n"
                       f"While I'm gathering specific interview details for {company_name}, here's what you can expect from **typical tech company interview processes**:\n\n"
                       f"📋 **Common Interview Rounds:**\n\n"
                       f"**1. Online Assessment / Coding Round**\n"
                       f"• Usually 1-2 coding problems (easy to medium difficulty)\n"
                       f"• Focus on Data Structures & Algorithms\n"
                       f"• Time limit: 60-90 minutes\n"
                       f"• Platforms: HackerRank, CodeSignal, or company's own platform\n\n"
                       f"**2. Technical Interview (1-2 rounds)**\n"
                       f"• Deep dive into technical skills\n"
                       f"• Problem-solving and coding on whiteboard/virtual board\n"
                       f"• System design questions (for experienced roles)\n"
                       f"• Questions about your projects and experience\n\n"
                       f"**3. HR / Behavioral Round**\n"
                       f"• Questions about your background, motivation, and fit\n"
                       f"• Salary discussion\n"
                       f"• Company culture and values alignment\n\n"
                       f"**4. Manager Round (Sometimes)**\n"
                       f"• Discussion with hiring manager\n"
                       f"• Role-specific questions\n"
                       f"• Team fit assessment\n\n"
                       f"🔍 **I'm currently searching for {company_name}'s specific interview process. For the most accurate information:**\n"
                       f"• Check {company_name}'s careers page for interview details\n"
                       f"• Read interview experiences on Glassdoor, GeeksforGeeks\n"
                       f"• Connect with recent hires from {company_name} on LinkedIn\n\n"
                       f"Would you like me to search for more specific information about {company_name}'s interview process?")
        
        elif intent == 'eligibility':
            eligibility = knowledge.get('eligibility', '')
            if eligibility and len(eligibility) > 20:
                return (f"**{company_name} Eligibility Requirements:**\n\n{eligibility}\n\n"
                       f"✅ **Important Notes:**\n"
                       f"• Make sure you meet all these requirements before applying\n"
                       f"• Some requirements may be flexible based on exceptional skills or experience\n"
                       f"• Always check the latest job postings for updated requirements")
            else:
                return (f"**Eligibility Requirements for {company_name}:**\n\n"
                       f"While I'm gathering specific eligibility criteria for {company_name}, here are **typical requirements** for tech companies:\n\n"
                       f"📋 **Common Eligibility Criteria:**\n"
                       f"• **Education:** Bachelor's degree in Computer Science, IT, or related field\n"
                       f"• **CGPA:** Usually 7.0+ (varies by company)\n"
                       f"• **Backlogs:** No active backlogs (some companies allow cleared backlogs)\n"
                       f"• **Year:** Final year students or recent graduates\n"
                       f"• **Skills:** Strong programming and problem-solving skills\n\n"
                       f"🔍 **I'm currently searching for {company_name}'s specific eligibility criteria. For the most accurate information, check their official careers page.**")
        
        elif intent == 'package':
            salary = knowledge.get('salary', '')
            if salary and len(salary) > 10:
                return (f"**{company_name} Salary Information:**\n\n{salary}\n\n"
                       f"💼 **Important Notes:**\n"
                       f"• Salary may vary based on role, experience, and location\n"
                       f"• Additional benefits (health insurance, stock options) may apply\n"
                       f"• Negotiate based on your skills and market research")
            else:
                return (f"**Salary Information for {company_name}:**\n\n"
                       f"While I'm gathering specific salary information for {company_name}, here's what you should know:\n\n"
                       f"💰 **Salary Factors:**\n"
                       f"• **Role:** Software Engineer, Data Scientist, Product Manager, etc.\n"
                       f"• **Experience:** Entry-level, Mid-level, Senior positions\n"
                       f"• **Location:** Metro cities typically offer higher packages\n"
                       f"• **Skills:** In-demand skills can command premium salaries\n\n"
                       f"📊 **Typical Ranges (India):**\n"
                       f"• **Entry-level:** 3-8 LPA\n"
                       f"• **Mid-level:** 8-20 LPA\n"
                       f"• **Senior-level:** 20+ LPA\n\n"
                       f"🔍 **For accurate salary information:**\n"
                       f"• Check {company_name}'s job postings\n"
                       f"• Research on Glassdoor, AmbitionBox, PayScale\n"
                       f"• Connect with current employees on LinkedIn\n\n"
                       f"Would you like me to search for more specific information?")
        
        elif intent == 'company_info':
            description = knowledge.get('description', '')
            location = knowledge.get('location', '')
            skills = knowledge.get('skills', [])
            response = f"**About {company_name}:**\n\n"
            if description:
                response += f"{description}\n\n"
            if location:
                response += f"📍 **Location:** {location}\n\n"
            if skills and len(skills) > 0:
                response += f"🔧 **Key Skills:** {', '.join(skills[:8])}\n\n"
            response += f"🌐 For more information, visit their official website."
            return response
        
        # Default response with available data - ChatGPT-like comprehensive answer
        response = f"**{company_name} Information:**\n\n"
        if knowledge.get('description'):
            response += f"{knowledge['description']}\n\n"
        if knowledge.get('location'):
            response += f"📍 **Location:** {knowledge['location']}\n\n"
        if knowledge.get('skills') and len(knowledge['skills']) > 0:
            response += f"🔧 **Skills:** {', '.join(knowledge['skills'][:10])}\n\n"
        if knowledge.get('eligibility'):
            response += f"📋 **Eligibility:** {knowledge['eligibility'][:200]}...\n\n"
        if knowledge.get('process'):
            response += f"📝 **Interview Process:** {knowledge['process'][:200]}...\n\n"
        if knowledge.get('salary'):
            response += f"💰 **Salary:** {knowledge['salary']}\n\n"
        
        if not response.strip() or response == f"**{company_name} Information:**\n\n":
            response += f"I have basic information about {company_name}. Would you like to know about:\n"
            response += f"• Skills required\n"
            response += f"• Interview process\n"
            response += f"• Eligibility criteria\n"
            response += f"• Salary information\n"
            response += f"• Location details\n\n"
            response += f"Just ask me any specific question about {company_name}!"
        
        return response
    
    def generate_general_response(self, intent: str, query: str) -> str:
        """Generate general response when knowledge base doesn't have answer."""
        if intent == 'greeting':
            return ("Hello! 👋 I'm your Placement Assistant. I can help you with:\n\n"
                   "• Company information and requirements\n"
                   "• Skills needed for placements\n"
                   "• Interview preparation tips\n"
                   "• Eligibility criteria\n"
                   "• Salary packages\n"
                   "• Placement drive details\n\n"
                   "What would you like to know?")
        
        elif intent == 'resume':
            return ("**Resume Tips for Placements:**\n\n"
                   "📄 **Format:**\n"
                   "• Keep it 1-2 pages\n"
                   "• Use clear, professional fonts\n"
                   "• Organize sections logically\n\n"
                   "📝 **Content:**\n"
                   "• Highlight technical skills\n"
                   "• Include relevant projects\n"
                   "• Quantify achievements\n"
                   "• Add GitHub/LinkedIn links\n\n"
                   "✅ **Tips:**\n"
                   "• Tailor resume for each company\n"
                   "• Use action verbs\n"
                   "• Proofread carefully")
        
        elif intent == 'roadmap':
            return ("**Placement Preparation Roadmap:**\n\n"
                   "📚 **Phase 1: Fundamentals (Months 1-2)**\n"
                   "• Master Data Structures & Algorithms\n"
                   "• Learn a programming language deeply\n"
                   "• Practice basic coding problems\n\n"
                   "💻 **Phase 2: Advanced Topics (Months 3-4)**\n"
                   "• System Design basics\n"
                   "• Database concepts\n"
                   "• Framework-specific skills\n\n"
                   "🎯 **Phase 3: Interview Prep (Months 5-6)**\n"
                   "• Mock interviews\n"
                   "• Behavioral questions\n"
                   "• Company-specific research")
        
        elif intent == 'internship':
            return ("**Internship Opportunities:**\n\n"
                   "🔍 **Where to Find:**\n"
                   "• Company career pages\n"
                   "• LinkedIn job postings\n"
                   "• Internshala, Naukri, Indeed\n"
                   "• Campus placement cell\n\n"
                   "💡 **Tips:**\n"
                   "• Apply early\n"
                   "• Tailor your resume\n"
                   "• Prepare for technical interviews\n"
                   "• Show enthusiasm and willingness to learn")
        
        # Try to extract company name even from general queries
        company_name = self.extract_company_name(query)
        if company_name:
            return {
                'response': f"🔍 Searching for information about {company_name}...",
                'source': 'scraped',
                'intent': intent,
                'company_name': company_name,
                'needs_scraping': True,
            }
        
        # Only show generic response if no company detected
        return (f"I understand you're asking: \"{query}\"\n\n"
               f"To help you better, please mention a company name. For example:\n"
               f"• \"What is Meril?\"\n"
               f"• \"Tell me about Deloitte\"\n"
               f"• \"Deloitte skills\"\n"
               f"• \"Meril eligibility\"\n\n"
               f"I'll automatically search and provide detailed information!")
    
    def process_query(self, userId: str, message: str) -> Dict:
        """
        Main processing function: classify intent, search knowledge base, generate response.
        Returns: {
            'response': str,
            'source': 'firestore' | 'scraped' | 'ai' | 'general',
            'intent': str,
            'company_name': str or None
        }
        """
        try:
            # Classify intent
            intent, confidence = self.classify_intent(message)
            logger.info(f"Intent: {intent}, Confidence: {confidence}")
            
            # Extract company name if present
            company_name = self.extract_company_name(message)
            
            # Search chat logs first (for similar previous questions)
            previous_response = self.search_chat_logs(message, userId)
            if previous_response and confidence > 0.5:
                return {
                    'response': previous_response,
                    'source': 'firestore',
                    'intent': intent,
                    'company_name': company_name,
                }
            
            # Search knowledge base
            knowledge = self.search_knowledge_base(message, company_name)
            
            if knowledge:
                # Check if specific data is missing for the requested intent
                needs_scraping = False
                message_lower = message.lower()
                
                # If asking for skills but skills data is missing/empty
                if (intent == 'skills' or 'skill' in message_lower) and \
                   (not knowledge.get('skills') or len(knowledge.get('skills', [])) == 0):
                    needs_scraping = True
                    logger.info(f"Skills requested but missing for {company_name}, triggering scrape")
                
                # If asking for interview process but process data is missing/empty
                if (intent == 'interview' or 'interview process' in message_lower or 
                    ('interview' in message_lower and 'process' in message_lower)) and \
                   (not knowledge.get('process') or len(knowledge.get('process', '')) < 50):
                    needs_scraping = True
                    logger.info(f"Interview process requested but missing for {company_name}, triggering scrape")
                
                # If asking for location but location data is missing
                if (intent == 'location' or 'where' in message_lower or 'located' in message_lower) and \
                   (not knowledge.get('location') or len(knowledge.get('location', '')) < 3):
                    needs_scraping = True
                    logger.info(f"Location requested but missing for {company_name}, triggering scrape")
                
                if needs_scraping:
                    return {
                        'response': f"🔍 I found some information about {company_name}, but I'm searching for more specific details...",
                        'source': 'scraped',
                        'intent': intent,
                        'company_name': company_name or knowledge.get('companyName'),
                        'needs_scraping': True,
                    }
                
                # Generate response from available knowledge
                response = self.generate_response_from_knowledge(intent, knowledge, message)
                return {
                    'response': response,
                    'source': 'firestore',
                    'intent': intent,
                    'company_name': company_name or knowledge.get('companyName'),
                }
            
            # If no knowledge found and company name exists, mark for scraping
            if company_name:
                return {
                    'response': f"🔍 Searching for information about {company_name}...",
                    'source': 'scraped',
                    'intent': intent,
                    'company_name': company_name,
                    'needs_scraping': True,
                }
            
            # Generate general response (but check for company name first)
            response = self.generate_general_response(intent, message)
            
            # If response is a dict (needs scraping), return it
            if isinstance(response, dict):
                return response
            
            return {
                'response': response,
                'source': 'ai',
                'intent': intent,
                'company_name': company_name,
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'response': "I apologize, but I encountered an error. Please try rephrasing your question or ask about a specific company.",
                'source': 'ai',
                'intent': 'error',
                'company_name': None,
            }
    
    def save_to_knowledge_base(self, company_name: str, data: Dict) -> bool:
        """Save scraped/processed data to company_knowledge_base."""
        try:
            doc_id = re.sub(r'[^a-zA-Z0-9_-]', '_', company_name.lower())[:50]
            doc_ref = self.db.collection('company_knowledge_base').document(doc_id)
            
            data['companyName'] = company_name
            data['last_updated'] = firestore.SERVER_TIMESTAMP
            data['collectedFrom'] = data.get('collectedFrom', 'scraped')
            
            doc_ref.set(data, merge=True)
            logger.info(f"Saved to knowledge base: {company_name}")
            return True
        except Exception as e:
            logger.error(f"Error saving to knowledge base: {e}")
            return False
    
    def save_chat_log(self, userId: str, message: str, response: str, metadata: Dict) -> bool:
        """Save chat interaction to chat_logs collection."""
        try:
            self.db.collection('chat_logs').add({
                'userId': userId,
                'message': message,
                'response': response,
                'intent': metadata.get('intent'),
                'company_name': metadata.get('company_name'),
                'source': metadata.get('source'),
                'timestamp': firestore.SERVER_TIMESTAMP,
            })
            return True
        except Exception as e:
            logger.error(f"Error saving chat log: {e}")
            return False

