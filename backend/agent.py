"""
Strands Agent - Uses Gemini 2.5 Flash for input understanding and normalization
Agent only understands input, does NOT control conversation flow

This implementation uses the Strands framework to leverage Gemini for input
normalization while maintaining backend control over conversation flow.
"""

import os
from typing import Optional, List
from datetime import datetime, timedelta
from dotenv import load_dotenv
from strands import Agent
from strands.models.gemini import GeminiModel

# Load environment variables from .env file
load_dotenv()


class StrandsAgent:
    """
    Agent that uses Strands framework with Gemini to understand and normalize user input.
    The agent is constrained to only process input - it does NOT control conversation flow.
    """
    
    def __init__(self):
        # Get API key from .env file or environment variable
        # Supports both GEMINI_API_KEY and GOOGLE_API_KEY (GOOGLE_API_KEY takes precedence)
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY or GOOGLE_API_KEY not set. "
                "Please set it in .env file or environment variable."
            )
        
        # Initialize Strands Gemini Model
        # Using gemini-2.5-flash as shown in the sample code
        model = GeminiModel(
            client_args={
                "api_key": api_key,
            },
            model_id="gemini-2.5-flash",
            params={
                "temperature": 0.3,  # Lower temperature for more consistent normalization
                "top_p": 0.95,
            }
        )
        
        # Create Strands Agent with a system prompt that constrains it to input normalization only
        system_prompt = """
        You are an input normalization assistant for an insurance claim system.
        
        Your ONLY responsibility is to understand and normalize user input. You do NOT:
        - Decide what question to ask next
        - Control conversation flow
        - Make decisions about the process
        
        You ONLY:
        - Understand user intent from free-text input
        - Normalize yes/no answers
        - Match user input to provided options
        - Extract and normalize dates, times, and other structured data
        
        Be precise and return only the normalized value requested.
        """
        
        # Initialize Strands Agent (no tools needed - we only use it for normalization)
        # Note: Using run_async=False to avoid async issues, agent will handle sync calls
        try:
            self.agent = Agent(
                model=model,
                system_prompt=system_prompt,
                tools=[]  # No tools - agent only normalizes input
            )
        except Exception as e:
            # Agent initialization failed, will use fallback normalization
            self.agent = None
    
    def process_input(
        self,
        user_input: str,
        question_type: str,
        question_text: str,
        options: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Process user input and return normalized value
        
        Args:
            user_input: Raw user input
            question_type: "text", "yesno", or "options"
            question_text: The question being asked
            options: List of options if question_type is "options"
        
        Returns:
            Normalized value or None if invalid
        """
        
        if question_type == "yesno":
            return self._normalize_yesno(user_input)
        
        elif question_type == "options":
            if not options:
                return None
            return self._normalize_option(user_input, options)
        
        elif question_type == "text":
            return self._normalize_text(user_input, question_text)
        
        return None
    
    def _normalize_yesno(self, user_input: str) -> Optional[str]:
        """Normalize yes/no input using Strands Agent"""
        user_lower = user_input.lower().strip()
        
        # Quick check for common yes/no words
        yes_words = ["yes", "y", "true", "1", "yeah", "yep", "sure", "ok", "okay"]
        no_words = ["no", "n", "false", "0", "nope", "nah"]
        
        if any(word in user_lower for word in yes_words):
            return "Yes"
        elif any(word in user_lower for word in no_words):
            return "No"
        
        # Use Strands Agent for ambiguous cases
        prompt = f"""Given the user input: "{user_input}"
Is this a Yes or No answer? Respond with only "Yes" or "No"."""
        
        if not self.agent:
            return None
            
        try:
            result = self.agent(prompt)
            # Strands Agent returns AgentResult object, extract text content
            # Handle both string and AgentResult types
            if hasattr(result, 'content'):
                result_text = str(result.content).strip().upper()
            elif hasattr(result, 'text'):
                result_text = str(result.text).strip().upper()
            else:
                result_text = str(result).strip().upper()
            
            if "YES" in result_text:
                return "Yes"
            elif "NO" in result_text:
                return "No"
        except Exception:
            return None
        
        return None
    
    def _normalize_option(self, user_input: str, options: List[str]) -> Optional[str]:
        """Normalize option selection using Strands Agent"""
        user_lower = user_input.lower().strip()
        
        # Direct match
        for option in options:
            if user_lower == option.lower():
                return option
        
        # Partial match
        for option in options:
            if option.lower() in user_lower or user_lower in option.lower():
                return option
        
        # Use Strands Agent to match intent
        prompt = f"""Given the user input: "{user_input}"
And these available options: {', '.join(options)}

Which option best matches the user's intent? Respond with only the exact option text from the list, or "NONE" if no match."""
        
        if not self.agent:
            return None
            
        try:
            result = self.agent(prompt)
            # Strands Agent returns AgentResult object, extract text content
            # Handle both string and AgentResult types
            if hasattr(result, 'content'):
                result_text = str(result.content).strip()
            elif hasattr(result, 'text'):
                result_text = str(result.text).strip()
            else:
                result_text = str(result).strip()
            
            # Check if result matches any option
            for option in options:
                if option.lower() in result_text.lower() or result_text.lower() in option.lower():
                    return option
        except Exception:
            return None
        
        return None
    
    def _normalize_text(self, user_input: str, question_text: str) -> Optional[str]:
        """Normalize text input using Strands Agent"""
        # Basic validation - ensure it's not empty
        if not user_input or not user_input.strip():
            return None
        
        # For date/time questions, use better date parsing
        if "date" in question_text.lower() or "time" in question_text.lower():
            # First try to parse relative dates
            normalized_date = self._parse_relative_date(user_input)
            if normalized_date:
                return normalized_date
            
            # Then try Strands Agent for complex dates
            prompt = f"""Given the user input: "{user_input}"
Extract and normalize the date and time. If the user says "yesterday", "today", "tomorrow", convert it to the actual date.
Format: "YYYY-MM-DD HH:MM" or "Month DD, YYYY at HH:MM AM/PM"
Today's date is {datetime.now().strftime('%Y-%m-%d')}.
Respond with only the normalized date and time."""
            
            if not self.agent:
                return user_input.strip()
                
            try:
                result = self.agent(prompt)
                # Strands Agent returns AgentResult object, extract text content
                # Handle both string and AgentResult types
                if hasattr(result, 'content'):
                    return str(result.content).strip()
                elif hasattr(result, 'text'):
                    return str(result.text).strip()
                else:
                    return str(result).strip()
            except Exception:
                return user_input.strip()
        
        # For other text, use Strands to clean/extract if needed
        # For now, return cleaned input, but can enhance with Strands for better extraction
        return user_input.strip()
    
    def _parse_relative_date(self, user_input: str) -> Optional[str]:
        """Parse relative dates like yesterday, today, tomorrow"""
        user_lower = user_input.lower().strip()
        now = datetime.now()
        
        if 'yesterday' in user_lower:
            date = now - timedelta(days=1)
            # Try to extract time if mentioned
            time_str = self._extract_time(user_input)
            return f"{date.strftime('%Y-%m-%d')} {time_str}" if time_str else date.strftime('%Y-%m-%d %H:%M')
        elif 'today' in user_lower:
            date = now
            time_str = self._extract_time(user_input)
            return f"{date.strftime('%Y-%m-%d')} {time_str}" if time_str else date.strftime('%Y-%m-%d %H:%M')
        elif 'tomorrow' in user_lower:
            date = now + timedelta(days=1)
            time_str = self._extract_time(user_input)
            return f"{date.strftime('%Y-%m-%d')} {time_str}" if time_str else date.strftime('%Y-%m-%d %H:%M')
        
        return None
    
    def _extract_time(self, user_input: str) -> Optional[str]:
        """Extract time from user input if present"""
        import re
        # Look for time patterns like "2:30 PM", "14:30", "2pm", etc.
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)',
            r'(\d{1,2}):(\d{2})',
            r'(\d{1,2})\s*(AM|PM|am|pm)',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None

