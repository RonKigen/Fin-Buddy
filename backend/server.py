from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import google.generativeai as genai
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("FinBuddy API starting up...")
    yield
    # Shutdown
    logger.info("FinBuddy API shutting down...")
    client.close()

# Create the main app with lifespan handler
app = FastAPI(lifespan=lifespan)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Pydantic Models
class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    message: str
    response: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_stage: Optional[str] = "general"

class ChatRequest(BaseModel):
    session_id: str
    message: str
    user_stage: Optional[str] = "general"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: datetime

class Badge(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    requirement: str
    xp_reward: int

class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_stage: str = "general"
    streak_count: int = 0
    max_streak: int = 0
    total_questions: int = 0
    total_xp: int = 0
    level: int = 1
    badges: List[str] = []
    modules_completed: List[str] = []
    quiz_scores: Dict[str, int] = {}
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LearningModule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    content: str
    category: str
    user_stage: str
    estimated_time: int  # minutes
    difficulty: str  # beginner, intermediate, advanced
    xp_reward: int
    order_index: int

class Quiz(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    category: str
    user_stage: str
    questions: List[Dict[str, Any]]
    passing_score: int
    xp_reward: int

class QuizSubmission(BaseModel):
    session_id: str
    quiz_id: str
    answers: List[int]  # indices of selected answers

class QuizResult(BaseModel):
    quiz_id: str
    score: int
    total_questions: int
    passed: bool
    xp_earned: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Financial knowledge context based on user stage
FINANCIAL_CONTEXT = {
    "student": """You are FinBuddy, a friendly AI financial literacy assistant specializing in helping students and young adults learn about money management. Focus on:
- Basic budgeting and saving tips for students
- Understanding student loans and debt management
- Building credit history responsibly
- Part-time work and income management
- Emergency funds for students (even small amounts)
- Banking basics and choosing accounts
Keep explanations simple, encouraging, and relevant to student life with limited income.""",
    
    "early_career": """You are FinBuddy, a friendly AI financial literacy assistant helping early career professionals build strong financial foundations. Focus on:
- Career-focused budgeting and salary management
- Building emergency funds (3-6 months expenses)
- Starting investment accounts (401k, IRA, index funds)
- Managing student loan payments strategically
- Credit building and responsible credit card use
- Saving for major goals (house, car, wedding)
- Insurance needs (health, auto, renters/homeowners)
Provide practical, actionable advice for people starting their careers.""",
    
    "retiree": """You are FinBuddy, a friendly AI financial literacy assistant helping retirees and those nearing retirement manage their finances. Focus on:
- Retirement income planning and withdrawal strategies
- Social Security optimization
- Healthcare and Medicare planning
- Estate planning and wills
- Tax-efficient retirement withdrawals
- Managing fixed incomes and budgeting in retirement
- Protecting assets from inflation
- Legacy planning for family
Provide thoughtful, detailed guidance for retirement financial security.""",
    
    "general": """You are FinBuddy, a friendly AI financial literacy assistant helping people learn about money management and build financial literacy. You provide clear, encouraging, and practical financial advice on topics like:
- Budgeting and saving strategies
- Debt management and credit building
- Investment basics and retirement planning
- Insurance and risk management
- Banking and financial products
- Tax planning and optimization
Always explain concepts in simple terms, use relatable examples, and encourage good financial habits."""
}

# Pre-defined badges
BADGES = [
    Badge(id="first_question", name="Curious Beginner", description="Asked your first financial question", icon="🔍", requirement="Ask 1 question", xp_reward=10),
    Badge(id="streak_3", name="Getting Started", description="Maintained a 3-day learning streak", icon="🔥", requirement="3-day streak", xp_reward=25),
    Badge(id="streak_7", name="Committed Learner", description="Maintained a 7-day learning streak", icon="🌟", requirement="7-day streak", xp_reward=50),
    Badge(id="streak_30", name="Financial Warrior", description="Maintained a 30-day learning streak", icon="⚡", requirement="30-day streak", xp_reward=100),
    Badge(id="quiz_master", name="Quiz Master", description="Completed 5 quizzes with passing grades", icon="🏆", requirement="Pass 5 quizzes", xp_reward=75),
    Badge(id="module_explorer", name="Knowledge Seeker", description="Completed 10 learning modules", icon="📚", requirement="Complete 10 modules", xp_reward=60),
    Badge(id="budget_expert", name="Budget Expert", description="Completed all budgeting modules and quizzes", icon="💰", requirement="Master budgeting", xp_reward=100),
    Badge(id="investment_guru", name="Investment Guru", description="Completed all investment modules and quizzes", icon="📈", requirement="Master investing", xp_reward=100),
]

# Pre-defined learning modules
LEARNING_MODULES = [
    # Student Stage Modules
    LearningModule(
        title="College Budgeting Basics",
        description="Learn how to create and stick to a budget as a student",
        content="""# College Budgeting Basics

## Why Budget as a Student?

Creating a budget in college helps you:
- Avoid unnecessary debt
- Build good financial habits early
- Make your money last longer
- Reduce financial stress

## The 50/30/20 Student Rule

For students, try this simplified approach:
- **50% Needs**: Tuition, textbooks, meals, rent
- **30% Wants**: Entertainment, eating out, hobbies
- **20% Savings**: Emergency fund, future goals

## Quick Budgeting Tips

1. **Track everything** for one week to see where money goes
2. **Use student discounts** whenever possible
3. **Cook more meals** instead of eating out
4. **Buy used textbooks** or rent them
5. **Set aside $25-50/month** for emergencies

## Action Steps

1. List all your income sources
2. List all your expenses
3. Find areas to cut back
4. Set up automatic savings, even if it's just $10/week

Remember: Even small amounts saved now will help build your financial future!""",
        category="budgeting",
        user_stage="student",
        estimated_time=4,
        difficulty="beginner",
        xp_reward=20,
        order_index=1
    ),
    
    LearningModule(
        title="Building Credit in College",
        description="How to start building good credit while in school",
        content="""# Building Credit in College

## Why Credit Matters

Good credit helps you:
- Get better rates on loans
- Qualify for apartments
- Sometimes get better job opportunities
- Save money in the long run

## How to Start Building Credit

### 1. Student Credit Cards
- Look for cards with no annual fee
- Start with a secured card if needed
- Keep credit utilization below 30%

### 2. Become an Authorized User
- Ask parents to add you to their card
- Their good payment history helps your credit

### 3. Credit Builder Loans
- Small loans designed to build credit
- You pay into savings while building credit

## Golden Rules of Credit

1. **Always pay on time** - Payment history is 35% of your score
2. **Keep balances low** - Use less than 30% of available credit
3. **Don't close old cards** - Length of credit history matters
4. **Check your report** - Use free services to monitor your score

## What NOT to Do

- Don't max out credit cards
- Don't apply for multiple cards at once
- Don't co-sign loans for friends
- Don't ignore your credit report

Building good credit takes time, but the earlier you start, the better off you'll be!""",
        category="credit",
        user_stage="student",
        estimated_time=5,
        difficulty="beginner",  
        xp_reward=25,
        order_index=2
    ),

    # Early Career Modules
    LearningModule(
        title="Emergency Fund Essentials",
        description="How to build and maintain an emergency fund",
        content="""# Emergency Fund Essentials

## What is an Emergency Fund?

An emergency fund is money set aside for unexpected expenses like:
- Job loss
- Medical emergencies
- Car repairs
- Home repairs
- Other unexpected costs

## How Much Do You Need?

**Goal**: 3-6 months of living expenses

**Starting out**: Even $500-1000 can help with most emergencies

## Building Your Emergency Fund

### Step 1: Calculate Your Target
- Add up monthly expenses (rent, food, utilities, etc.)
- Multiply by 3-6 months
- This is your target amount

### Step 2: Start Small
- Begin with $25-50 per paycheck
- Increase as your income grows
- Automate the savings

### Step 3: Keep It Accessible
- High-yield savings account
- Money market account
- NOT in stocks or investments

## Where to Keep Emergency Funds

✅ **Good Options:**
- High-yield savings account
- Money market account
- Certificate of deposit (short-term)

❌ **Bad Options:**
- Checking account (too accessible)
- Stock market (too risky)
- Under your mattress (no growth)

## Quick Tips

1. **Automate it** - Set up automatic transfers
2. **Start today** - Even $10 is better than $0
3. **Use windfalls** - Tax refunds, bonuses, gifts
4. **Don't touch it** - Only for real emergencies

Your emergency fund is your financial safety net - prioritize building it!""",
        category="saving",
        user_stage="early_career",
        estimated_time=4,
        difficulty="beginner",
        xp_reward=20,
        order_index=1
    ),

    # General Modules
    LearningModule(
        title="Investment Basics for Beginners",
        description="Understanding the fundamentals of investing",
        content="""# Investment Basics for Beginners

## Why Invest?

Investing helps your money grow faster than inflation and savings accounts. It's essential for:
- Retirement planning
- Building wealth
- Reaching financial goals
- Protecting against inflation

## Types of Investments

### 1. Stocks
- Own shares of companies
- Higher risk, higher potential return
- Good for long-term growth

### 2. Bonds
- Loan money to companies/government
- Lower risk, steady returns
- Good for stability

### 3. Index Funds
- Own many stocks/bonds at once
- Instant diversification
- Perfect for beginners

### 4. ETFs (Exchange-Traded Funds)
- Like index funds but trade like stocks
- Low fees
- Great for beginners

## Investment Principles

### 1. Start Early
- Time is your biggest advantage
- Compound interest works magic over time

### 2. Diversify
- Don't put all eggs in one basket
- Spread risk across many investments

### 3. Stay Consistent
- Invest regularly, regardless of market conditions
- Dollar-cost averaging reduces risk

### 4. Keep Fees Low
- High fees eat into returns
- Choose low-cost index funds

## Getting Started

1. **Pay off high-interest debt first**
2. **Build emergency fund**
3. **Start with target-date funds or index funds**
4. **Invest consistently**
5. **Don't panic during market downturns**

## Common Mistakes to Avoid

- Trying to time the market
- Putting all money in one stock
- Panic selling during downturns
- Not starting early enough
- Paying high investment fees

Remember: Investing is a marathon, not a sprint. Start small, stay consistent, and let time work in your favor!""",
        category="investing",
        user_stage="general",
        estimated_time=6,
        difficulty="intermediate",
        xp_reward=30,
        order_index=1
    )
]

# Pre-defined quizzes
QUIZZES = [
    Quiz(
        title="Budgeting Basics Quiz",
        description="Test your knowledge of budgeting fundamentals",
        category="budgeting",
        user_stage="general",
        passing_score=70,
        xp_reward=30,
        questions=[
            {
                "question": "What percentage of income should typically go to needs in a basic budget?",
                "options": ["30%", "50%", "70%", "90%"],
                "correct": 1,
                "explanation": "The 50/30/20 rule suggests 50% for needs, 30% for wants, and 20% for savings."
            },
            {
                "question": "Which is considered a 'need' rather than a 'want'?",
                "options": ["Streaming subscriptions", "Rent payment", "Dining out", "New clothes"],
                "correct": 1,
                "explanation": "Rent is a necessity for shelter, while the others are typically wants."
            },
            {
                "question": "How often should you review and adjust your budget?",
                "options": ["Never", "Once a year", "Monthly", "Daily"],
                "correct": 2,
                "explanation": "Monthly budget reviews help you stay on track and make necessary adjustments."
            },
            {
                "question": "What's the first step in creating a budget?",
                "options": ["Set spending limits", "Track your current spending", "Open a savings account", "Pay off debt"],
                "correct": 1,
                "explanation": "You need to know where your money currently goes before you can make a budget."
            },
            {
                "question": "An emergency fund should typically cover how many months of expenses?",
                "options": ["1 month", "3-6 months", "1 year", "2 years"],
                "correct": 1,
                "explanation": "3-6 months of expenses provides adequate coverage for most emergencies."
            }
        ]
    ),
    
    Quiz(
        title="Credit Score Fundamentals",
        description="Test your understanding of credit scores and credit building",
        category="credit",
        user_stage="general",
        passing_score=70,
        xp_reward=25,
        questions=[
            {
                "question": "What factor has the biggest impact on your credit score?",
                "options": ["Credit utilization", "Payment history", "Length of credit history", "Types of credit"],
                "correct": 1,
                "explanation": "Payment history makes up 35% of your credit score and is the most important factor."
            },
            {
                "question": "What's the ideal credit utilization ratio?",
                "options": ["Below 10%", "Below 30%", "Below 50%", "Below 70%"],
                "correct": 1,
                "explanation": "Keeping credit utilization below 30% helps maintain a good credit score."
            },
            {
                "question": "How long do negative items typically stay on your credit report?",
                "options": ["2 years", "5 years", "7 years", "10 years"],
                "correct": 2,
                "explanation": "Most negative items stay on your credit report for 7 years."
            },
            {
                "question": "Which action will NOT help improve your credit score?",
                "options": ["Paying bills on time", "Closing old credit cards", "Keeping balances low", "Checking credit report regularly"],
                "correct": 1,
                "explanation": "Closing old cards can hurt your credit by reducing available credit and shortening credit history."
            }
        ]
    ),

    Quiz(
        title="Investment Basics Quiz",
        description="Test your knowledge of investment fundamentals",
        category="investing",
        user_stage="general",
        passing_score=70,
        xp_reward=35,
        questions=[
            {
                "question": "What is compound interest?",
                "options": ["Interest on interest", "Simple interest", "Bank fees", "Investment losses"],
                "correct": 0,
                "explanation": "Compound interest is earning interest on both your principal and previously earned interest."
            },
            {
                "question": "Which investment typically has the highest risk and potential return?",
                "options": ["Savings account", "Government bonds", "Individual stocks", "CDs"],
                "correct": 2,
                "explanation": "Individual stocks have higher volatility but potentially higher returns than other options."
            },
            {
                "question": "What does diversification mean in investing?",
                "options": ["Buying one stock", "Spreading investments across different assets", "Only investing in bonds", "Day trading"],
                "correct": 1,
                "explanation": "Diversification reduces risk by spreading investments across different types of assets."
            },
            {
                "question": "What is an index fund?",
                "options": ["A single stock", "A fund that tracks a market index", "A government bond", "A savings account"],
                "correct": 1,
                "explanation": "Index funds track market indexes like the S&P 500 and provide instant diversification."
            },
            {
                "question": "When is the best time to start investing?",
                "options": ["When you're rich", "When you're 40", "As early as possible", "Never"],
                "correct": 2,
                "explanation": "Starting early allows compound interest to work in your favor over time."
            }
        ]
    )
]

# Utility functions
def get_system_message(user_stage: str) -> str:
    return FINANCIAL_CONTEXT.get(user_stage, FINANCIAL_CONTEXT["general"])

def calculate_level(xp: int) -> int:
    """Calculate user level based on XP"""
    if xp < 50: return 1
    elif xp < 150: return 2
    elif xp < 300: return 3
    elif xp < 500: return 4
    elif xp < 750: return 5
    elif xp < 1000: return 6
    else: return min(10, 6 + (xp - 1000) // 300)

async def check_and_award_badges(profile: UserProfile) -> List[str]:
    """Check if user qualifies for new badges and return list of new badges"""
    new_badges = []
    
    # First question badge
    if "first_question" not in profile.badges and profile.total_questions >= 1:
        new_badges.append("first_question")
    
    # Streak badges
    if "streak_3" not in profile.badges and profile.streak_count >= 3:
        new_badges.append("streak_3")
    if "streak_7" not in profile.badges and profile.streak_count >= 7:
        new_badges.append("streak_7")
    if "streak_30" not in profile.badges and profile.streak_count >= 30:
        new_badges.append("streak_30")
    
    # Quiz master badge
    passed_quizzes = sum(1 for score in profile.quiz_scores.values() if score >= 70)
    if "quiz_master" not in profile.badges and passed_quizzes >= 5:
        new_badges.append("quiz_master")
    
    # Module explorer badge
    if "module_explorer" not in profile.badges and len(profile.modules_completed) >= 10:
        new_badges.append("module_explorer")
    
    return new_badges

async def update_streak(session_id: str):
    """Update user's streak based on last activity"""
    profile = await db.user_profiles.find_one({"session_id": session_id})
    if not profile:
        return
    
    now = datetime.utcnow()
    last_activity = profile.get("last_activity")
    
    if last_activity:
        # Convert string to datetime if needed
        if isinstance(last_activity, str):
            last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
        
        days_diff = (now - last_activity).days
        
        if days_diff == 1:
            # Consecutive day - increment streak
            new_streak = profile.get("streak_count", 0) + 1
            max_streak = max(profile.get("max_streak", 0), new_streak)
            
            await db.user_profiles.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "streak_count": new_streak,
                        "max_streak": max_streak,
                        "last_activity": now
                    }
                }
            )
        elif days_diff > 1:
            # Streak broken
            await db.user_profiles.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "streak_count": 1,
                        "last_activity": now
                    }
                }
            )
    else:
        # First activity
        await db.user_profiles.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "streak_count": 1,
                    "last_activity": now
                }
            },
            upsert=True
        )

# API Routes
@api_router.get("/")
async def root():
    return {"message": "FinBuddy API - Your AI Financial Literacy Assistant"}

@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_finbuddy(request: ChatRequest):
    try:
        # Update streak
        await update_streak(request.session_id)
        
        # Get or create user profile
        user_profile = await db.user_profiles.find_one({"session_id": request.session_id})
        if not user_profile:
            new_profile = UserProfile(
                session_id=request.session_id,
                user_stage=request.user_stage,
                total_questions=1
            )
            await db.user_profiles.insert_one(new_profile.dict())
            current_profile = new_profile
        else:
            # Update question count and check for badges
            current_profile = UserProfile(**user_profile)
            current_profile.total_questions += 1
            
            # Check for new badges
            new_badges = await check_and_award_badges(current_profile)
            if new_badges:
                current_profile.badges.extend(new_badges)
                # Award XP for new badges
                for badge_id in new_badges:
                    badge = next((b for b in BADGES if b.id == badge_id), None)
                    if badge:
                        current_profile.total_xp += badge.xp_reward
            
            # Update level
            current_profile.level = calculate_level(current_profile.total_xp)
            
            await db.user_profiles.update_one(
                {"session_id": request.session_id},
                {"$set": current_profile.dict()}
            )

        # Initialize Gemini model with the new model ID
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-2.5-pro")
        
        # Create system message content
        system_content = get_system_message(request.user_stage)
        
        # Generate response with system context
        response = model.generate_content([
            system_content,
            request.message
        ])
        
        # Save chat history
        chat_record = ChatMessage(
            session_id=request.session_id,
            message=request.message,
            response=response.text,
            user_stage=request.user_stage
        )
        await db.chat_history.insert_one(chat_record.dict())
        
        return ChatResponse(
            response=response.text,
            session_id=request.session_id,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process chat message")

# Learning Modules Endpoints
@api_router.get("/modules")
async def get_learning_modules(user_stage: Optional[str] = None):
    """Get all learning modules, optionally filtered by user stage"""
    try:
        # Initialize modules in database if not present
        existing_count = await db.learning_modules.count_documents({})
        if existing_count == 0:
            modules_data = [module.dict() for module in LEARNING_MODULES]
            await db.learning_modules.insert_many(modules_data)
        
        query = {}
        if user_stage:
            query = {"$or": [{"user_stage": user_stage}, {"user_stage": "general"}]}
        
        modules = await db.learning_modules.find(query).sort("order_index", 1).to_list(100)
        
        # Convert MongoDB ObjectId to string for JSON serialization
        for module in modules:
            if "_id" in module:
                module["_id"] = str(module["_id"])
                
        return modules
    except Exception as e:
        logging.error(f"Modules error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve learning modules")

@api_router.post("/modules/{module_id}/complete")
async def complete_module(module_id: str, session_id: str):
    """Mark a module as completed for user"""
    try:
        # Get user profile
        profile = await db.user_profiles.find_one({"session_id": session_id})
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Get module for XP reward
        module = await db.learning_modules.find_one({"id": module_id})
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")
        
        # Update profile
        current_profile = UserProfile(**profile)
        if module_id not in current_profile.modules_completed:
            current_profile.modules_completed.append(module_id)
            current_profile.total_xp += module.get("xp_reward", 20)
            current_profile.level = calculate_level(current_profile.total_xp)
            
            # Check for new badges
            new_badges = await check_and_award_badges(current_profile)
            if new_badges:
                current_profile.badges.extend(new_badges)
                for badge_id in new_badges:
                    badge = next((b for b in BADGES if b.id == badge_id), None)
                    if badge:
                        current_profile.total_xp += badge.xp_reward
                current_profile.level = calculate_level(current_profile.total_xp)
            
            await db.user_profiles.update_one(
                {"session_id": session_id},
                {"$set": current_profile.dict()}
            )
            
            return {
                "message": "Module completed successfully",
                "xp_earned": module.get("xp_reward", 20),
                "new_badges": new_badges,
                "new_level": current_profile.level
            }
        else:
            return {"message": "Module already completed"}
            
    except Exception as e:
        logging.error(f"Complete module error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to complete module")

# Quiz Endpoints
@api_router.get("/quizzes")
async def get_quizzes(user_stage: Optional[str] = None):
    """Get all quizzes, optionally filtered by user stage"""
    try:
        # Initialize quizzes in database if not present
        existing_count = await db.quizzes.count_documents({})
        if existing_count == 0:
            quizzes_data = [quiz.dict() for quiz in QUIZZES]
            await db.quizzes.insert_many(quizzes_data)
        
        query = {}
        if user_stage:
            query = {"$or": [{"user_stage": user_stage}, {"user_stage": "general"}]}
        
        # Return quizzes without correct answers
        quizzes = await db.quizzes.find(query).to_list(100)
        
        # Convert MongoDB ObjectId to string for JSON serialization
        for quiz in quizzes:
            if "_id" in quiz:
                quiz["_id"] = str(quiz["_id"])
        
        # Remove correct answers from questions for security
        for quiz in quizzes:
            for question in quiz.get("questions", []):
                if "correct" in question:
                    del question["correct"]
                if "explanation" in question:
                    del question["explanation"]
        
        return quizzes
    except Exception as e:
        logging.error(f"Quizzes error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve quizzes")

@api_router.post("/quizzes/{quiz_id}/submit")
async def submit_quiz(quiz_id: str, submission: QuizSubmission):
    """Submit quiz answers and get results"""
    try:
        # Get quiz
        quiz = await db.quizzes.find_one({"id": quiz_id})
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        quiz_obj = Quiz(**quiz)
        
        # Calculate score
        correct_answers = 0
        total_questions = len(quiz_obj.questions)
        results = []
        
        for i, answer_index in enumerate(submission.answers):
            if i < len(quiz_obj.questions):
                question = quiz_obj.questions[i]
                is_correct = answer_index == question["correct"]
                if is_correct:
                    correct_answers += 1
                
                results.append({
                    "question": question["question"],
                    "your_answer": question["options"][answer_index] if answer_index < len(question["options"]) else "No answer",
                    "correct_answer": question["options"][question["correct"]],
                    "is_correct": is_correct,
                    "explanation": question.get("explanation", "")
                })
        
        score = int((correct_answers / total_questions) * 100)
        passed = score >= quiz_obj.passing_score
        xp_earned = quiz_obj.xp_reward if passed else quiz_obj.xp_reward // 2
        
        # Update user profile
        profile = await db.user_profiles.find_one({"session_id": submission.session_id})
        if profile:
            current_profile = UserProfile(**profile)
            current_profile.quiz_scores[quiz_id] = score
            current_profile.total_xp += xp_earned
            current_profile.level = calculate_level(current_profile.total_xp)
            
            # Check for new badges
            new_badges = await check_and_award_badges(current_profile)
            if new_badges:
                current_profile.badges.extend(new_badges)
                for badge_id in new_badges:
                    badge = next((b for b in BADGES if b.id == badge_id), None)
                    if badge:
                        current_profile.total_xp += badge.xp_reward
                current_profile.level = calculate_level(current_profile.total_xp)
            
            await db.user_profiles.update_one(
                {"session_id": submission.session_id},
                {"$set": current_profile.dict()}
            )
        
        return {
            "score": score,
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "passed": passed,
            "xp_earned": xp_earned,
            "results": results,
            "new_badges": new_badges if profile else []
        }
        
    except Exception as e:
        logging.error(f"Submit quiz error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit quiz")

# Gamification Endpoints
@api_router.get("/badges")
async def get_all_badges():
    """Get all available badges"""
    return [badge.dict() for badge in BADGES]

@api_router.get("/profile/{session_id}")
async def get_user_profile(session_id: str):
    try:
        profile = await db.user_profiles.find_one({"session_id": session_id})
        if profile:
            return UserProfile(**profile)
        return None
    except Exception as e:
        logging.error(f"Profile error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user profile")

@api_router.post("/profile/update-stage")
async def update_user_stage(session_id: str, user_stage: str):
    try:
        await db.user_profiles.update_one(
            {"session_id": session_id},
            {"$set": {"user_stage": user_stage}},
            upsert=True
        )
        return {"message": "User stage updated successfully"}
    except Exception as e:
        logging.error(f"Profile update error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update user stage")

@api_router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    try:
        history = await db.chat_history.find(
            {"session_id": session_id}
        ).sort("timestamp", 1).to_list(100)
        return [ChatMessage(**chat) for chat in history]
    except Exception as e:
        logging.error(f"History error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Note: The old @app.on_event("shutdown") has been replaced with the lifespan handler above