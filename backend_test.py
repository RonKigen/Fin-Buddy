#!/usr/bin/env python3
import requests
import uuid
import time
import json
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://b97b0891-cb09-4adc-894a-620139441176.preview.emergentagent.com/api"

class FinBuddyTester:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.session_id = str(uuid.uuid4())
        self.test_results = {
            "gemini_ai_integration": {"success": False, "details": []},
            "chat_api_endpoints": {"success": False, "details": []},
            "financial_context_system": {"success": False, "details": []},
            "user_profile_management": {"success": False, "details": []},
            "mongodb_data_models": {"success": False, "details": []},
            "gamification_system": {"success": False, "details": []},
            "learning_modules_api": {"success": False, "details": []},
            "interactive_quiz_system": {"success": False, "details": []}
        }
    
    def run_all_tests(self):
        """Run all test cases and collect results"""
        try:
            # Test root endpoint
            self.test_root_endpoint()
            
            # Test Gemini AI Integration with different financial questions
            self.test_gemini_ai_integration()
            
            # Test chat history endpoint
            self.test_chat_history()
            
            # Test financial context system with different user stages
            self.test_financial_context_system()
            
            # Test user profile management
            self.test_user_profile_management()
            
            # Test gamification system
            self.test_gamification_system()
            
            # Test learning modules API
            self.test_learning_modules_api()
            
            # Test interactive quiz system
            self.test_interactive_quiz_system()
            
            # Print summary
            self.print_summary()
            
            return self.test_results
        except Exception as e:
            logger.error(f"Test suite error: {str(e)}")
            return {"error": str(e)}
    
    def test_root_endpoint(self):
        """Test the root API endpoint"""
        try:
            response = requests.get(f"{self.backend_url}/")
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "FinBuddy API" in data["message"]
            self.test_results["chat_api_endpoints"]["details"].append({
                "test": "Root endpoint",
                "success": True,
                "response": data
            })
            logger.info("✅ Root endpoint test passed")
        except Exception as e:
            self.test_results["chat_api_endpoints"]["details"].append({
                "test": "Root endpoint",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ Root endpoint test failed: {str(e)}")
    
    def test_gemini_ai_integration(self):
        """Test Gemini AI integration with various financial questions"""
        financial_questions = [
            "What is compound interest and why is it important?",
            "How should I start building an emergency fund?",
            "What's the difference between a Roth IRA and a traditional IRA?",
            "How can I improve my credit score?",
            "What are index funds and why are they recommended for beginners?"
        ]
        
        success_count = 0
        for question in financial_questions:
            try:
                response = self.send_chat_message(question, "general")
                
                # Check if response contains relevant financial information
                financial_terms = ["finance", "money", "budget", "invest", "save", "fund", 
                                  "credit", "debt", "interest", "income", "expense"]
                
                response_text = response.get("response", "").lower()
                relevant_terms_found = any(term in response_text for term in financial_terms)
                
                # Check response length - should be substantial
                is_substantial = len(response_text) > 100
                
                if relevant_terms_found and is_substantial:
                    success_count += 1
                    self.test_results["gemini_ai_integration"]["details"].append({
                        "test": f"Financial question: {question[:30]}...",
                        "success": True,
                        "response_length": len(response_text),
                        "relevant": relevant_terms_found
                    })
                    logger.info(f"✅ Gemini AI response test passed for: {question[:30]}...")
                else:
                    self.test_results["gemini_ai_integration"]["details"].append({
                        "test": f"Financial question: {question[:30]}...",
                        "success": False,
                        "response_length": len(response_text),
                        "relevant": relevant_terms_found,
                        "response_excerpt": response_text[:100] + "..."
                    })
                    logger.error(f"❌ Gemini AI response test failed for: {question[:30]}...")
            except Exception as e:
                self.test_results["gemini_ai_integration"]["details"].append({
                    "test": f"Financial question: {question[:30]}...",
                    "success": False,
                    "error": str(e)
                })
                logger.error(f"❌ Gemini AI test error for question '{question[:30]}...': {str(e)}")
        
        # Mark overall test as successful if majority of questions got good responses
        self.test_results["gemini_ai_integration"]["success"] = success_count >= 3
        logger.info(f"Gemini AI Integration tests: {success_count}/{len(financial_questions)} passed")
    
    def test_chat_history(self):
        """Test chat history retrieval"""
        try:
            # First send a few messages to create history
            messages = [
                "What are some basic budgeting tips?",
                "How can I start investing with little money?",
                "What's a good way to track my expenses?"
            ]
            
            for msg in messages:
                self.send_chat_message(msg, "general")
                time.sleep(1)  # Small delay to ensure messages are stored
            
            # Now retrieve chat history
            response = requests.get(f"{self.backend_url}/chat/history/{self.session_id}")
            assert response.status_code == 200
            
            history = response.json()
            assert isinstance(history, list)
            assert len(history) >= len(messages)
            
            # Verify history structure
            for entry in history:
                assert "id" in entry
                assert "session_id" in entry
                assert "message" in entry
                assert "response" in entry
                assert "timestamp" in entry
                assert entry["session_id"] == self.session_id
            
            self.test_results["chat_api_endpoints"]["details"].append({
                "test": "Chat history retrieval",
                "success": True,
                "history_count": len(history)
            })
            logger.info(f"✅ Chat history test passed with {len(history)} entries")
            
            # Mark chat API endpoints test as successful
            self.test_results["chat_api_endpoints"]["success"] = True
            
        except Exception as e:
            self.test_results["chat_api_endpoints"]["details"].append({
                "test": "Chat history retrieval",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ Chat history test failed: {str(e)}")
    
    def test_financial_context_system(self):
        """Test that different user stages provide appropriate financial advice context"""
        stages = ["student", "early_career", "retiree", "general"]
        stage_specific_questions = {
            "student": "How should I manage my student loans?",
            "early_career": "How should I start saving for retirement in my 20s?",
            "retiree": "What's the best withdrawal strategy for retirement accounts?",
            "general": "What are some basic financial literacy concepts everyone should know?"
        }
        
        # Keywords that should appear in responses for each stage
        stage_keywords = {
            "student": ["student", "loan", "budget", "college", "university", "education", "class"],
            "early_career": ["career", "salary", "401k", "professional", "job", "income"],
            "retiree": ["retirement", "medicare", "social security", "withdraw", "estate"],
            "general": ["budget", "save", "invest", "plan", "finance", "money"]
        }
        
        success_count = 0
        for stage in stages:
            try:
                question = stage_specific_questions[stage]
                response = self.send_chat_message(question, stage)
                
                response_text = response.get("response", "").lower()
                keywords = stage_keywords[stage]
                
                # Check if response contains stage-specific keywords
                relevant_keywords_found = [keyword for keyword in keywords if keyword in response_text]
                is_relevant = len(relevant_keywords_found) >= 2  # At least 2 relevant keywords
                
                if is_relevant:
                    success_count += 1
                    self.test_results["financial_context_system"]["details"].append({
                        "test": f"{stage} stage context",
                        "success": True,
                        "relevant_keywords": relevant_keywords_found
                    })
                    logger.info(f"✅ Financial context test passed for {stage} stage")
                else:
                    self.test_results["financial_context_system"]["details"].append({
                        "test": f"{stage} stage context",
                        "success": False,
                        "relevant_keywords": relevant_keywords_found,
                        "response_excerpt": response_text[:100] + "..."
                    })
                    logger.error(f"❌ Financial context test failed for {stage} stage")
            except Exception as e:
                self.test_results["financial_context_system"]["details"].append({
                    "test": f"{stage} stage context",
                    "success": False,
                    "error": str(e)
                })
                logger.error(f"❌ Financial context test error for {stage} stage: {str(e)}")
        
        # Mark overall test as successful if all stages passed
        self.test_results["financial_context_system"]["success"] = success_count == len(stages)
        logger.info(f"Financial Context System tests: {success_count}/{len(stages)} passed")
    
    def test_user_profile_management(self):
        """Test user profile management functionality"""
        try:
            # 1. Get initial profile (should be created during chat tests)
            response = requests.get(f"{self.backend_url}/profile/{self.session_id}")
            assert response.status_code == 200
            
            initial_profile = response.json()
            assert initial_profile is not None
            assert "session_id" in initial_profile
            assert initial_profile["session_id"] == self.session_id
            assert "user_stage" in initial_profile
            assert "total_questions" in initial_profile
            
            initial_stage = initial_profile["user_stage"]
            initial_questions = initial_profile["total_questions"]
            
            self.test_results["user_profile_management"]["details"].append({
                "test": "Get user profile",
                "success": True,
                "initial_stage": initial_stage,
                "question_count": initial_questions
            })
            logger.info(f"✅ Get user profile test passed")
            
            # 2. Update user stage
            new_stage = "retiree" if initial_stage != "retiree" else "student"
            response = requests.post(
                f"{self.backend_url}/profile/update-stage?session_id={self.session_id}&user_stage={new_stage}"
            )
            assert response.status_code == 200
            
            self.test_results["user_profile_management"]["details"].append({
                "test": "Update user stage",
                "success": True,
                "old_stage": initial_stage,
                "new_stage": new_stage
            })
            logger.info(f"✅ Update user stage test passed")
            
            # 3. Verify stage was updated
            response = requests.get(f"{self.backend_url}/profile/{self.session_id}")
            assert response.status_code == 200
            
            updated_profile = response.json()
            assert updated_profile["user_stage"] == new_stage
            
            self.test_results["user_profile_management"]["details"].append({
                "test": "Verify stage update",
                "success": True,
                "verified_stage": updated_profile["user_stage"]
            })
            logger.info(f"✅ Verify stage update test passed")
            
            # 4. Send a message and verify question count increases
            self.send_chat_message("Does changing my life stage affect the advice I get?", new_stage)
            
            response = requests.get(f"{self.backend_url}/profile/{self.session_id}")
            assert response.status_code == 200
            
            final_profile = response.json()
            assert final_profile["total_questions"] > initial_questions
            
            self.test_results["user_profile_management"]["details"].append({
                "test": "Question count increment",
                "success": True,
                "initial_count": initial_questions,
                "final_count": final_profile["total_questions"]
            })
            logger.info(f"✅ Question count increment test passed")
            
            # Mark overall test as successful
            self.test_results["user_profile_management"]["success"] = True
            self.test_results["mongodb_data_models"]["success"] = True  # MongoDB models are working if profile tests pass
            
        except Exception as e:
            self.test_results["user_profile_management"]["details"].append({
                "test": "User profile management",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ User profile management test failed: {str(e)}")
    
    def test_gamification_system(self):
        """Test the gamification system including badges, XP, and streaks"""
        try:
            # 1. Test badges endpoint
            response = requests.get(f"{self.backend_url}/badges")
            assert response.status_code == 200
            
            badges = response.json()
            assert isinstance(badges, list)
            assert len(badges) > 0
            
            # Verify badge structure
            for badge in badges:
                assert "id" in badge
                assert "name" in badge
                assert "description" in badge
                assert "icon" in badge
                assert "requirement" in badge
                assert "xp_reward" in badge
            
            self.test_results["gamification_system"]["details"].append({
                "test": "Get badges",
                "success": True,
                "badge_count": len(badges)
            })
            logger.info(f"✅ Get badges test passed with {len(badges)} badges")
            
            # 2. Test first question badge awarding
            # Send a message if we haven't already to trigger first_question badge
            self.send_chat_message("What's a good financial goal to start with?", "general")
            
            # Get profile to check for badge
            response = requests.get(f"{self.backend_url}/profile/{self.session_id}")
            assert response.status_code == 200
            
            profile = response.json()
            assert "badges" in profile
            assert isinstance(profile["badges"], list)
            
            # Check if first_question badge was awarded
            first_question_badge_awarded = "first_question" in profile["badges"]
            
            self.test_results["gamification_system"]["details"].append({
                "test": "First question badge",
                "success": first_question_badge_awarded,
                "badges": profile["badges"]
            })
            
            if first_question_badge_awarded:
                logger.info("✅ First question badge test passed")
            else:
                logger.warning("⚠️ First question badge not awarded yet")
            
            # 3. Test XP and level calculation
            assert "total_xp" in profile
            assert "level" in profile
            assert isinstance(profile["total_xp"], int)
            assert isinstance(profile["level"], int)
            
            # Verify level calculation based on XP
            expected_level = 1
            if profile["total_xp"] >= 50: expected_level = 2
            if profile["total_xp"] >= 150: expected_level = 3
            if profile["total_xp"] >= 300: expected_level = 4
            if profile["total_xp"] >= 500: expected_level = 5
            
            level_calculation_correct = profile["level"] == expected_level
            
            self.test_results["gamification_system"]["details"].append({
                "test": "XP and level calculation",
                "success": level_calculation_correct,
                "xp": profile["total_xp"],
                "actual_level": profile["level"],
                "expected_level": expected_level
            })
            
            if level_calculation_correct:
                logger.info("✅ XP and level calculation test passed")
            else:
                logger.error(f"❌ Level calculation incorrect. XP: {profile['total_xp']}, Expected level: {expected_level}, Actual: {profile['level']}")
            
            # 4. Test streak tracking
            assert "streak_count" in profile
            assert "max_streak" in profile
            assert isinstance(profile["streak_count"], int)
            assert isinstance(profile["max_streak"], int)
            
            # Streak should be at least 1 after our interactions
            streak_tracking_working = profile["streak_count"] >= 1
            
            self.test_results["gamification_system"]["details"].append({
                "test": "Streak tracking",
                "success": streak_tracking_working,
                "current_streak": profile["streak_count"],
                "max_streak": profile["max_streak"]
            })
            
            if streak_tracking_working:
                logger.info("✅ Streak tracking test passed")
            else:
                logger.error("❌ Streak tracking test failed")
            
            # Mark overall test as successful if most subtests passed
            success_count = sum(1 for detail in self.test_results["gamification_system"]["details"] if detail.get("success", False))
            self.test_results["gamification_system"]["success"] = success_count >= 3  # At least 3 of 4 tests passed
            
        except Exception as e:
            self.test_results["gamification_system"]["details"].append({
                "test": "Gamification system",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ Gamification system test failed: {str(e)}")
    
    def test_learning_modules_api(self):
        """Test the learning modules API functionality"""
        try:
            # 1. Test getting all modules
            response = requests.get(f"{self.backend_url}/modules")
            assert response.status_code == 200
            
            modules = response.json()
            assert isinstance(modules, list)
            assert len(modules) > 0
            
            # Verify module structure
            for module in modules:
                assert "id" in module
                assert "title" in module
                assert "description" in module
                assert "content" in module
                assert "category" in module
                assert "user_stage" in module
                assert "estimated_time" in module
                assert "difficulty" in module
                assert "xp_reward" in module
            
            self.test_results["learning_modules_api"]["details"].append({
                "test": "Get all modules",
                "success": True,
                "module_count": len(modules)
            })
            logger.info(f"✅ Get all modules test passed with {len(modules)} modules")
            
            # 2. Test filtering modules by user stage
            stages = ["student", "early_career", "general"]
            for stage in stages:
                response = requests.get(f"{self.backend_url}/modules?user_stage={stage}")
                assert response.status_code == 200
                
                filtered_modules = response.json()
                assert isinstance(filtered_modules, list)
                
                # Verify that all returned modules are for this stage or general
                stage_appropriate = all(m["user_stage"] == stage or m["user_stage"] == "general" for m in filtered_modules)
                
                self.test_results["learning_modules_api"]["details"].append({
                    "test": f"Filter modules by {stage} stage",
                    "success": stage_appropriate,
                    "module_count": len(filtered_modules)
                })
                
                if stage_appropriate:
                    logger.info(f"✅ Filter modules by {stage} stage test passed")
                else:
                    logger.error(f"❌ Filter modules by {stage} stage test failed")
            
            # 3. Test completing a module
            if modules:
                module_id = modules[0]["id"]
                response = requests.post(f"{self.backend_url}/modules/{module_id}/complete?session_id={self.session_id}")
                assert response.status_code == 200
                
                completion_result = response.json()
                assert "message" in completion_result
                assert "xp_earned" in completion_result
                
                # Verify profile was updated with completed module
                profile_response = requests.get(f"{self.backend_url}/profile/{self.session_id}")
                assert profile_response.status_code == 200
                
                profile = profile_response.json()
                assert "modules_completed" in profile
                assert module_id in profile["modules_completed"]
                
                self.test_results["learning_modules_api"]["details"].append({
                    "test": "Complete module",
                    "success": True,
                    "module_id": module_id,
                    "xp_earned": completion_result["xp_earned"]
                })
                logger.info(f"✅ Complete module test passed")
                
                # 4. Test completing the same module again (should indicate already completed)
                response = requests.post(f"{self.backend_url}/modules/{module_id}/complete?session_id={self.session_id}")
                assert response.status_code == 200
                
                repeat_completion = response.json()
                assert "message" in repeat_completion
                assert "already completed" in repeat_completion["message"].lower()
                
                self.test_results["learning_modules_api"]["details"].append({
                    "test": "Complete module again",
                    "success": True,
                    "message": repeat_completion["message"]
                })
                logger.info(f"✅ Complete module again test passed")
            
            # Mark overall test as successful
            success_count = sum(1 for detail in self.test_results["learning_modules_api"]["details"] if detail.get("success", False))
            self.test_results["learning_modules_api"]["success"] = success_count >= 3  # At least 3 tests passed
            
        except Exception as e:
            self.test_results["learning_modules_api"]["details"].append({
                "test": "Learning modules API",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ Learning modules API test failed: {str(e)}")
    
    def test_interactive_quiz_system(self):
        """Test the interactive quiz system functionality"""
        try:
            # 1. Test getting all quizzes
            response = requests.get(f"{self.backend_url}/quizzes")
            assert response.status_code == 200
            
            quizzes = response.json()
            assert isinstance(quizzes, list)
            assert len(quizzes) > 0
            
            # Verify quiz structure
            for quiz in quizzes:
                assert "id" in quiz
                assert "title" in quiz
                assert "description" in quiz
                assert "category" in quiz
                assert "user_stage" in quiz
                assert "questions" in quiz
                assert "passing_score" in quiz
                assert "xp_reward" in quiz
                
                # Verify questions structure
                for question in quiz["questions"]:
                    assert "question" in question
                    assert "options" in question
                    # Correct answer and explanation should be removed for security
                    assert "correct" not in question
                    assert "explanation" not in question
            
            self.test_results["interactive_quiz_system"]["details"].append({
                "test": "Get all quizzes",
                "success": True,
                "quiz_count": len(quizzes)
            })
            logger.info(f"✅ Get all quizzes test passed with {len(quizzes)} quizzes")
            
            # 2. Test filtering quizzes by user stage
            stages = ["student", "early_career", "general"]
            for stage in stages:
                response = requests.get(f"{self.backend_url}/quizzes?user_stage={stage}")
                assert response.status_code == 200
                
                filtered_quizzes = response.json()
                assert isinstance(filtered_quizzes, list)
                
                # Verify that all returned quizzes are for this stage or general
                stage_appropriate = all(q["user_stage"] == stage or q["user_stage"] == "general" for q in filtered_quizzes)
                
                self.test_results["interactive_quiz_system"]["details"].append({
                    "test": f"Filter quizzes by {stage} stage",
                    "success": stage_appropriate,
                    "quiz_count": len(filtered_quizzes)
                })
                
                if stage_appropriate:
                    logger.info(f"✅ Filter quizzes by {stage} stage test passed")
                else:
                    logger.error(f"❌ Filter quizzes by {stage} stage test failed")
            
            # 3. Test submitting a quiz with correct answers
            if quizzes:
                quiz = quizzes[0]
                quiz_id = quiz["id"]
                
                # Create answers array (all zeros for simplicity)
                # In a real test, we'd need to know the correct answers
                # For testing, we'll submit all zeros and check the response structure
                answers = [0] * len(quiz["questions"])
                
                submission = {
                    "session_id": self.session_id,
                    "quiz_id": quiz_id,
                    "answers": answers
                }
                
                response = requests.post(f"{self.backend_url}/quizzes/{quiz_id}/submit", json=submission)
                assert response.status_code == 200
                
                result = response.json()
                assert "score" in result
                assert "total_questions" in result
                assert "correct_answers" in result
                assert "passed" in result
                assert "xp_earned" in result
                assert "results" in result
                
                # Verify detailed results structure
                for question_result in result["results"]:
                    assert "question" in question_result
                    assert "your_answer" in question_result
                    assert "correct_answer" in question_result
                    assert "is_correct" in question_result
                    assert "explanation" in question_result
                
                self.test_results["interactive_quiz_system"]["details"].append({
                    "test": "Submit quiz",
                    "success": True,
                    "quiz_id": quiz_id,
                    "score": result["score"],
                    "xp_earned": result["xp_earned"],
                    "passed": result["passed"]
                })
                logger.info(f"✅ Submit quiz test passed with score {result['score']}")
                
                # 4. Verify profile was updated with quiz score
                profile_response = requests.get(f"{self.backend_url}/profile/{self.session_id}")
                assert profile_response.status_code == 200
                
                profile = profile_response.json()
                assert "quiz_scores" in profile
                assert quiz_id in profile["quiz_scores"]
                assert profile["quiz_scores"][quiz_id] == result["score"]
                
                self.test_results["interactive_quiz_system"]["details"].append({
                    "test": "Quiz score in profile",
                    "success": True,
                    "profile_score": profile["quiz_scores"][quiz_id],
                    "result_score": result["score"]
                })
                logger.info(f"✅ Quiz score in profile test passed")
            
            # Mark overall test as successful
            success_count = sum(1 for detail in self.test_results["interactive_quiz_system"]["details"] if detail.get("success", False))
            self.test_results["interactive_quiz_system"]["success"] = success_count >= 3  # At least 3 tests passed
            
        except Exception as e:
            self.test_results["interactive_quiz_system"]["details"].append({
                "test": "Interactive quiz system",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ Interactive quiz system test failed: {str(e)}")
    
    def send_chat_message(self, message: str, user_stage: str = "general") -> Dict[str, Any]:
        """Helper method to send a chat message and return the response"""
        payload = {
            "session_id": self.session_id,
            "message": message,
            "user_stage": user_stage
        }
        
        response = requests.post(f"{self.backend_url}/chat", json=payload)
        if response.status_code != 200:
            raise Exception(f"Chat API error: {response.status_code} - {response.text}")
        
        return response.json()
    
    def print_summary(self):
        """Print a summary of all test results"""
        print("\n" + "="*80)
        print("FINBUDDY BACKEND TEST RESULTS")
        print("="*80)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            print(f"{test_name.replace('_', ' ').upper()}: {status}")
            
            for detail in result.get("details", []):
                sub_status = "✅" if detail.get("success", False) else "❌"
                print(f"  {sub_status} {detail.get('test', 'Unknown test')}")
                
                if not detail.get("success", False) and "error" in detail:
                    print(f"     Error: {detail['error']}")
            
            print("")
        
        print("="*80)

if __name__ == "__main__":
    tester = FinBuddyTester()
    results = tester.run_all_tests()