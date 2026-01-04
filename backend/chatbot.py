"""
Chatbot Manager - Controls conversation flow and state
Backend controls all question logic, not the LLM
Manages insurance claim filing process
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from agent import StrandsAgent


class ChatbotManager:
    """Manages chatbot conversation state and flow"""
    
    # Claim keywords to detect when user wants to file a claim
    CLAIM_KEYWORDS = ['claim', 'accident', 'incident', 'crash', 'collision', 'file a claim', 'report', 'damage', 'loss']
    
    # Question flow definition
    QUESTIONS = [
        {
            "step": 1,
            "key": "policyNumber",
            "question": "Please provide your policy number.",
            "type": "text"
        },
        {
            "step": 2,
            "key": "contactNumber",
            "question": "What is your contact number?",
            "type": "text"
        },
        {
            "step": 3,
            "key": "incidentDateTime",
            "question": "When did the incident occur? (Please provide date and time)",
            "type": "text"
        },
        {
            "step": 4,
            "key": "incidentType",
            "question": "What type of incident occurred?",
            "type": "options",
            "options": ["Collision", "Single Vehicle Accident", "Hit and Run", "Theft", "Vandalism", "Other"]
        },
        {
            "step": 5,
            "key": "location",
            "question": "Where did the incident occur? (Please provide the location)",
            "type": "text"
        },
        {
            "step": 6,
            "key": "weather",
            "question": "What was the weather condition at the time of incident?",
            "type": "options",
            "options": ["Clear", "Rainy", "Snowy", "Foggy", "Windy", "Other"]
        },
        {
            "step": 7,
            "key": "policeReport",
            "question": "Was a police report filed?",
            "type": "yesno"
        },
        {
            "step": 8,
            "key": "policeReportNumber",
            "question": "Please provide the police report number.",
            "type": "text",
            "conditional": {"key": "policeReport", "value": "Yes"}
        },
        {
            "step": 9,
            "key": "vehicleDamage",
            "question": "Please describe the vehicle damage.",
            "type": "text"
        },
        {
            "step": 10,
            "key": "driveable",
            "question": "Is the vehicle driveable?",
            "type": "yesno"
        },
        {
            "step": 11,
            "key": "towingRequired",
            "question": "Is towing required?",
            "type": "yesno"
        },
        {
            "step": 12,
            "key": "photosTaken",
            "question": "Were photos taken of the incident?",
            "type": "yesno"
        },
        {
            "step": 13,
            "key": "injuries",
            "question": "Were there any injuries?",
            "type": "options",
            "options": ["No injuries", "Minor injuries", "Major injuries", "Fatalities"]
        },
        {
            "step": 14,
            "key": "driverName",
            "question": "What is the driver's name?",
            "type": "text"
        },
        {
            "step": 15,
            "key": "driverRelation",
            "question": "What is the driver's relation to the policyholder?",
            "type": "options",
            "options": ["Self", "Spouse", "Family Member", "Friend", "Other"]
        },
        {
            "step": 16,
            "key": "driverLicenseNumber",
            "question": "What is the driver's license number?",
            "type": "text"
        },
        {
            "step": 17,
            "key": "drivingExperience",
            "question": "What is the driver's driving experience?",
            "type": "options",
            "options": ["Less than 1 year", "1-3 years", "3-5 years", "5-10 years", "More than 10 years"]
        },
        {
            "step": 18,
            "key": "driverCondition",
            "question": "Was the driver in good physical and mental condition at the time of the incident?",
            "type": "yesno"
        },
        {
            "step": 19,
            "key": "consent",
            "question": "Do you consent to the processing of this claim and authorize us to investigate?",
            "type": "yesno"
        }
    ]
    
    def __init__(self):
        self.current_step = 0
        self.answers: Dict[str, Any] = {}
        self.agent = StrandsAgent()
        self.conversational_mode = True  # Start in conversational mode
        self.conversation_history: List[str] = []
    
    def get_state(self) -> Dict[str, Any]:
        """Get current chatbot state for session storage"""
        return {
            "current_step": self.current_step,
            "answers": self.answers,
            "conversational_mode": self.conversational_mode,
            "conversation_history": self.conversation_history
        }
    
    def set_state(self, state: Dict[str, Any]):
        """Restore chatbot state from session"""
        self.current_step = state.get("current_step", 0)
        self.answers = state.get("answers", {})
        self.conversational_mode = state.get("conversational_mode", True)
        self.conversation_history = state.get("conversation_history", [])
    
    def get_current_question(self) -> Optional[Dict[str, Any]]:
        """Get the current question based on step and conditions"""
        if self.current_step >= len(self.QUESTIONS):
            return None
        
        question = self.QUESTIONS[self.current_step]
        
        # Check if question has conditional logic
        if "conditional" in question:
            cond = question["conditional"]
            cond_key = cond["key"]
            cond_value = cond["value"]
            
            # If condition not met, skip this question
            if self.answers.get(cond_key) != cond_value:
                self.current_step += 1
                return self.get_current_question()
        
        return question
    
    def _check_claim_intent(self, user_input: str) -> bool:
        """Check if user wants to file a claim"""
        user_lower = user_input.lower()
        return any(keyword in user_lower for keyword in self.CLAIM_KEYWORDS)
    
    async def _get_conversational_response(self, user_input: str) -> str:
        """Generate conversational response when not in claim mode"""
        user_lower = user_input.lower()
        
        # Greetings
        if any(word in user_lower for word in ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']):
            return "Hello! I'm here to help you with your insurance needs. How can I assist you today?"
        
        # Help questions
        if any(word in user_lower for word in ['help', 'what can you do', 'what do you do']):
            return "I can help you with various insurance services including filing claims, checking policy information, and answering questions about coverage. What would you like to know?"
        
        # Insurance definition questions
        if any(word in user_lower for word in ['what is insurance', 'what is insuracne', 'explain insurance', 'insurance meaning']):
            return "Insurance is a financial product that provides protection against financial loss. It helps cover costs for unexpected events like accidents, theft, or damage. Would you like to know more about your policies, or do you need to file a claim?"
        
        # Policy questions
        if any(word in user_lower for word in ['policy', 'policies', 'my policy', 'my policies']):
            return "You can view all your policies on the dashboard. I can help you file a claim for any of your policies. Would you like to file a claim?"
        
        # Coverage questions
        if any(word in user_lower for word in ['coverage', 'what does my policy cover', 'what is covered']):
            return "Coverage details vary by policy type. You can see your coverage information in the policy details on the dashboard. For specific coverage questions, please contact our customer service team. Would you like to file a claim instead?"
        
        # Premium/payment questions
        if any(word in user_lower for word in ['premium', 'payment', 'pay', 'bill', 'cost']):
            return "You can see your premium information for each policy on the dashboard. For payment-related questions, please contact our customer service team. Is there anything else I can help with, or would you like to file a claim?"
        
        # Question about questions
        if any(word in user_lower for word in ['question', 'ask', 'inquire', 'want to know']):
            return "I'm here to help! I can assist you with filing a claim, or you can ask me general questions about insurance. What would you like to know?"
        
        # Use agent for better understanding if available
        try:
            if self.agent and self.agent.agent:
                prompt = f"""The user asked: "{user_input}"
                
Provide a helpful, friendly response about insurance. Keep it brief (1-2 sentences). If the question is about filing a claim, mention that you can help with that. Otherwise, provide a helpful answer or suggest filing a claim.
                
Respond naturally and conversationally."""
                result = self.agent.agent(prompt)
                if hasattr(result, 'content'):
                    response = str(result.content).strip()
                elif hasattr(result, 'text'):
                    response = str(result.text).strip()
                else:
                    response = str(result).strip()
                
                if response and len(response) > 10:
                    return response
        except Exception:
            pass
        
        # Default response
        return "I understand. I'm here to help with your insurance needs. Would you like to file a claim, or do you have other questions?"
    
    async def process_message(self, user_input: str, user: Dict[str, str], policy_data: Optional[Dict[str, Any]] = None, available_policies: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Process user message and return response"""
        
        # Store conversation history (skip empty messages)
        if user_input and user_input.strip():
            self.conversation_history.append(user_input)
        
        # If in conversational mode, check if user wants to file a claim
        if self.conversational_mode:
            # Handle empty/greeting messages
            if not user_input or not user_input.strip() or user_input.lower().strip() in ['start', 'hi', 'hello', 'begin', '']:
                return {
                    "response": "Hello! I'm here to help you with your insurance needs. How can I assist you today?",
                    "questionType": "text"
                }
            if self._check_claim_intent(user_input):
                # Switch to FNOL mode
                self.conversational_mode = False
                # Get first question
                question = self.get_current_question()
                if question:
                    response_data = {
                        "response": f"I'll help you file a claim. Let's get started with some information.\n\n{question['question']}",
                        "questionType": question["type"]
                    }
                    if question["type"] == "options":
                        response_data["options"] = question["options"]
                    return response_data
            else:
                # Stay in conversational mode
                response_text = await self._get_conversational_response(user_input)
                return {
                    "response": response_text,
                    "questionType": "text"
                }
        
        # FNOL mode - process questions
        # Get current question
        question = self.get_current_question()
        
        if not question:
            # All questions answered
            return {
                "response": "Thank you! Your claim has been submitted successfully. We will process your claim shortly.",
                "questionType": "text",
                "completed": True
            }
        
        # If this is the first question and user input is empty or just a greeting, return the question
        # But only if we're already in FNOL mode (not conversational)
        if not self.conversational_mode and self.current_step == 0 and (not user_input or not user_input.strip() or 
                                        user_input.lower().strip() in ['start', 'begin']):
            # Return first question without processing
            response_data = {
                "response": question["question"],
                "questionType": question["type"]
            }
            if question["type"] == "options":
                response_data["options"] = question["options"]
            return response_data
        
        # Use agent to understand and normalize user input
        try:
            normalized_value = self.agent.process_input(
                user_input=user_input,
                question_type=question["type"],
                question_text=question["question"],
                options=question.get("options")
            )
        except Exception as e:
            # Fallback: try basic matching without agent
            normalized_value = self._fallback_normalize(user_input, question)
        
        # If policy number is entered, validate it
        if question["key"] == "policyNumber" and normalized_value:
            # Check if policy exists
            if available_policies:
                policy_data = next((p for p in available_policies if normalized_value.upper() in p["policyNumber"].upper()), None)
                
                if policy_data:
                    # Policy found - show details and continue
                    policy_info = self._format_policy_info(policy_data)
                    self.answers[question["key"]] = normalized_value
                    self.current_step += 1
                    
                    # Get next question
                    next_question = self.get_current_question()
                    if not next_question:
                        return {
                            "response": "Thank you! Your claim has been submitted successfully.",
                            "questionType": "text",
                            "completed": True
                        }
                    
                    response_data = {
                        "response": f"✓ Policy Found: {policy_data.get('policyNumber', normalized_value)}\n{policy_info}\n\n{next_question['question']}",
                        "questionType": next_question["type"]
                    }
                    if next_question["type"] == "options":
                        response_data["options"] = next_question["options"]
                    return response_data
                else:
                    # Policy not found - inform user
                    policy_numbers = [p["policyNumber"] for p in available_policies]
                    return {
                        "response": f"I couldn't find a policy matching '{normalized_value}'. Please check your policy number and try again.\n\nYour available policies are: {', '.join(policy_numbers)}\n\n{question['question']}",
                        "questionType": question["type"]
                    }
            else:
                # No policies available - accept any input for demo
                self.answers[question["key"]] = normalized_value
                self.current_step += 1
                
                next_question = self.get_current_question()
                if not next_question:
                    return {
                        "response": "Thank you! Your claim has been submitted successfully.",
                        "questionType": "text",
                        "completed": True
                    }
                
                response_data = {
                    "response": next_question["question"],
                    "questionType": next_question["type"]
                }
                if next_question["type"] == "options":
                    response_data["options"] = next_question["options"]
                return response_data
        
        # Validate and store answer
        if normalized_value:
            self.answers[question["key"]] = normalized_value
            self.current_step += 1
            
            # Get next question
            next_question = self.get_current_question()
            
            if not next_question:
                # Completed
                return {
                    "response": "Thank you! Your claim has been submitted successfully. We will process your claim shortly.",
                    "questionType": "text",
                    "completed": True
                }
            
            # Return next question
            response_data = {
                "response": next_question["question"],
                "questionType": next_question["type"]
            }
            
            if next_question["type"] == "options":
                response_data["options"] = next_question["options"]
            
            return response_data
        else:
            # Invalid input, ask again
            return {
                "response": f"Please provide a valid answer. {question['question']}",
                "questionType": question["type"],
                "options": question.get("options")
            }
    
    def _fallback_normalize(self, user_input: str, question: Dict[str, Any]) -> Optional[str]:
        """Fallback normalization without using Strands Agent"""
        question_type = question.get("type")
        user_lower = user_input.lower().strip()
        
        if question_type == "yesno":
            yes_words = ["yes", "y", "true", "1", "yeah", "yep", "sure", "ok", "okay"]
            no_words = ["no", "n", "false", "0", "nope", "nah"]
            if any(word in user_lower for word in yes_words):
                return "Yes"
            elif any(word in user_lower for word in no_words):
                return "No"
        
        elif question_type == "options":
            options = question.get("options", [])
            for option in options:
                if user_lower == option.lower() or option.lower() in user_lower:
                    return option
        
        elif question_type == "text":
            if user_input and user_input.strip():
                return user_input.strip()
        
        return None
    
    def _format_policy_info(self, policy: Dict[str, Any]) -> str:
        """Format policy information for display"""
        info = []
        info.append(f"Type: {policy.get('type', 'N/A')}")
        info.append(f"Status: {policy.get('status', 'N/A')}")
        info.append(f"Premium: {policy.get('premium', 'N/A')}")
        info.append(f"Coverage: {policy.get('coverage', 'N/A')}")
        if 'vehicle' in policy:
            info.append(f"Vehicle: {policy['vehicle']}")
        if 'property' in policy:
            info.append(f"Property: {policy['property']}")
        info.append(f"Expiry: {policy.get('expiryDate', 'N/A')}")
        return "\n".join(info)
    
    def get_fnol_data(self) -> Dict[str, Any]:
        """Get complete claim data"""
        return self.answers.copy()

