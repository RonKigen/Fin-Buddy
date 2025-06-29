import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Generate session ID
const generateSessionId = () => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

// Components
const ChatInterface = ({ sessionId, userStage, onShowLearning, onShowQuiz, onShowProfile }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadChatHistory();
  }, [sessionId]);

  const loadChatHistory = async () => {
    try {
      const response = await axios.get(`${API}/chat/history/${sessionId}`);
      if (response.data && response.data.length > 0) {
        const formattedHistory = response.data.map(chat => [
          { type: 'user', content: chat.message },
          { type: 'assistant', content: chat.response }
        ]).flat();
        setMessages(formattedHistory);
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage("");
    setMessages(prev => [...prev, { type: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await axios.post(`${API}/chat`, {
        session_id: sessionId,
        message: userMessage,
        user_stage: userStage
      });

      setMessages(prev => [...prev, { 
        type: 'assistant', 
        content: response.data.response 
      }]);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, { 
        type: 'assistant', 
        content: "I'm sorry, I encountered an error. Please try again." 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Navigation */}
      <div className="bg-white shadow-sm border-b p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <span className="text-xl">💬</span>
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-800">Chat with FinBuddy</h2>
              <p className="text-sm text-gray-500">Ask me anything about finance!</p>
            </div>
          </div>
          <div className="flex space-x-2">
            <button onClick={onShowLearning} className="px-3 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors text-sm font-medium">
              📚 Learn
            </button>
            <button onClick={onShowQuiz} className="px-3 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-colors text-sm font-medium">
              🏆 Quiz
            </button>
            <button onClick={onShowProfile} className="px-3 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors text-sm font-medium">
              👤 Profile
            </button>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🤖</div>
            <h3 className="text-xl font-semibold text-gray-700 mb-2">Ready to learn about finance?</h3>
            <p className="text-gray-500">Ask me anything about budgeting, saving, investing, or any financial topic!</p>
          </div>
        )}
        
        {messages.map((message, index) => (
          <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-3xl px-6 py-4 rounded-2xl ${
              message.type === 'user' 
                ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white' 
                : 'bg-white shadow-md text-gray-800 border'
            }`}>
              <div className="whitespace-pre-wrap">{message.content}</div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white shadow-md rounded-2xl px-6 py-4 border">
              <div className="flex items-center space-x-2">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                </div>
                <span className="text-gray-500 text-sm">FinBuddy is thinking...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t p-4">
        <div className="flex space-x-4">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about financial literacy..."
            className="flex-1 resize-none border-2 border-gray-200 rounded-xl p-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-800 placeholder-gray-500"
            rows="2"
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !inputMessage.trim()}
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-medium"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

const LearningModules = ({ sessionId, userStage, onBack }) => {
  const [modules, setModules] = useState([]);
  const [selectedModule, setSelectedModule] = useState(null);
  const [completedModules, setCompletedModules] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadModules();
    loadUserProfile();
  }, [userStage]);

  const loadModules = async () => {
    try {
      const response = await axios.get(`${API}/modules?user_stage=${userStage}`);
      setModules(response.data);
    } catch (error) {
      console.error('Error loading modules:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUserProfile = async () => {
    try {
      const response = await axios.get(`${API}/profile/${sessionId}`);
      if (response.data) {
        setCompletedModules(response.data.modules_completed || []);
      }
    } catch (error) {
      console.error('Error loading profile:', error);
    }
  };

  const completeModule = async (moduleId) => {
    try {
      const response = await axios.post(`${API}/modules/${moduleId}/complete?session_id=${sessionId}`);
      setCompletedModules(prev => [...prev, moduleId]);
      
      // Show success message with XP earned
      alert(`🎉 Module completed! You earned ${response.data.xp_earned} XP!`);
      
      if (response.data.new_badges && response.data.new_badges.length > 0) {
        alert(`🏆 New badge${response.data.new_badges.length > 1 ? 's' : ''} earned: ${response.data.new_badges.join(', ')}!`);
      }
    } catch (error) {
      console.error('Error completing module:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading learning modules...</p>
        </div>
      </div>
    );
  }

  if (selectedModule) {
    const module = modules.find(m => m.id === selectedModule);
    const isCompleted = completedModules.includes(selectedModule);
    
    return (
      <div className="h-full flex flex-col">
        <div className="bg-white shadow-sm border-b p-4">
          <div className="flex items-center justify-between">
            <button onClick={() => setSelectedModule(null)} className="flex items-center space-x-2 text-gray-600 hover:text-gray-800">
              <span>←</span>
              <span>Back to Modules</span>
            </button>
            <button onClick={onBack} className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
              Back to Chat
            </button>
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-2xl shadow-lg p-8">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h1 className="text-3xl font-bold text-gray-800 mb-2">{module.title}</h1>
                  <p className="text-gray-600 mb-4">{module.description}</p>
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <span>⏱️ {module.estimated_time} min read</span>
                    <span>📊 {module.difficulty}</span>
                    <span>🎯 {module.xp_reward} XP</span>
                  </div>
                </div>
                {isCompleted && (
                  <div className="bg-green-100 text-green-800 px-4 py-2 rounded-full text-sm font-medium flex items-center">
                    ✅ Completed
                  </div>
                )}
              </div>
              
              <div className="prose prose-lg max-w-none">
                {module.content.split('\n').map((line, index) => {
                  if (line.startsWith('# ')) {
                    return <h1 key={index} className="text-2xl font-bold mt-8 mb-4 text-gray-800">{line.replace('# ', '')}</h1>;
                  } else if (line.startsWith('## ')) {
                    return <h2 key={index} className="text-xl font-semibold mt-6 mb-3 text-gray-700">{line.replace('## ', '')}</h2>;
                  } else if (line.startsWith('### ')) {
                    return <h3 key={index} className="text-lg font-medium mt-4 mb-2 text-gray-600">{line.replace('### ', '')}</h3>;
                  } else if (line.startsWith('- ')) {
                    return <li key={index} className="ml-4 text-gray-700">{line.replace('- ', '')}</li>;
                  } else if (line.trim() === '') {
                    return <br key={index} />;
                  } else {
                    return <p key={index} className="mb-4 text-gray-700 leading-relaxed">{line}</p>;
                  }
                })}
              </div>
              
              {!isCompleted && (
                <div className="mt-8 pt-6 border-t">
                  <button
                    onClick={() => completeModule(selectedModule)}
                    className="w-full py-4 bg-gradient-to-r from-green-500 to-blue-600 text-white rounded-xl font-semibold text-lg hover:shadow-lg transform hover:scale-105 transition-all duration-200"
                  >
                    🎉 Complete Module & Earn {module.xp_reward} XP
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="bg-white shadow-sm border-b p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-blue-600 rounded-full flex items-center justify-center">
              <span className="text-xl">📚</span>
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-800">Learning Modules</h2>
              <p className="text-sm text-gray-500">Bite-sized financial lessons</p>
            </div>
          </div>
          <button onClick={onBack} className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
            Back to Chat
          </button>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-6xl mx-auto">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {modules.map((module) => {
              const isCompleted = completedModules.includes(module.id);
              return (
                <div
                  key={module.id}
                  className={`bg-white rounded-2xl shadow-lg p-6 cursor-pointer transform hover:scale-105 transition-all duration-200 border-2 ${
                    isCompleted ? 'border-green-200 bg-green-50' : 'border-transparent hover:shadow-xl'
                  }`}
                  onClick={() => setSelectedModule(module.id)}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                      module.difficulty === 'beginner' ? 'bg-green-100 text-green-800' :
                      module.difficulty === 'intermediate' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {module.difficulty}
                    </div>
                    {isCompleted && <span className="text-2xl">✅</span>}
                  </div>
                  
                  <h3 className="text-xl font-bold text-gray-800 mb-2">{module.title}</h3>
                  <p className="text-gray-600 mb-4 line-clamp-3">{module.description}</p>
                  
                  <div className="flex items-center justify-between text-sm text-gray-500">
                    <span>⏱️ {module.estimated_time} min</span>
                    <span>🎯 {module.xp_reward} XP</span>
                  </div>
                  
                  <div className="mt-4 pt-4 border-t">
                    <div className={`px-3 py-1 rounded-full text-xs font-medium inline-block ${
                      module.category === 'budgeting' ? 'bg-blue-100 text-blue-800' :
                      module.category === 'credit' ? 'bg-purple-100 text-purple-800' :
                      module.category === 'saving' ? 'bg-green-100 text-green-800' :
                      module.category === 'investing' ? 'bg-orange-100 text-orange-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {module.category}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

const Quiz = ({ sessionId, userStage, onBack }) => {
  const [quizzes, setQuizzes] = useState([]);
  const [selectedQuiz, setSelectedQuiz] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [quizResults, setQuizResults] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadQuizzes();
  }, [userStage]);

  const loadQuizzes = async () => {
    try {
      const response = await axios.get(`${API}/quizzes?user_stage=${userStage}`);
      setQuizzes(response.data);
    } catch (error) {
      console.error('Error loading quizzes:', error);
    } finally {
      setLoading(false);
    }
  };

  const startQuiz = (quiz) => {
    setSelectedQuiz(quiz);
    setCurrentQuestion(0);
    setAnswers(new Array(quiz.questions.length).fill(-1));
    setShowResults(false);
    setQuizResults(null);
  };

  const selectAnswer = (answerIndex) => {
    const newAnswers = [...answers];
    newAnswers[currentQuestion] = answerIndex;
    setAnswers(newAnswers);
  };

  const nextQuestion = () => {
    if (currentQuestion < selectedQuiz.questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      submitQuiz();
    }
  };

  const prevQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const submitQuiz = async () => {
    try {
      const response = await axios.post(`${API}/quizzes/${selectedQuiz.id}/submit`, {
        session_id: sessionId,
        quiz_id: selectedQuiz.id,
        answers: answers
      });
      
      setQuizResults(response.data);
      setShowResults(true);
      
      if (response.data.new_badges && response.data.new_badges.length > 0) {
        setTimeout(() => {
          alert(`🏆 New badge${response.data.new_badges.length > 1 ? 's' : ''} earned: ${response.data.new_badges.join(', ')}!`);
        }, 1000);
      }
    } catch (error) {
      console.error('Error submitting quiz:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading quizzes...</p>
        </div>
      </div>
    );
  }

  if (showResults && quizResults) {
    return (
      <div className="h-full flex flex-col">
        <div className="bg-white shadow-sm border-b p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-800">Quiz Results</h2>
            <button onClick={() => {setSelectedQuiz(null); setShowResults(false);}} className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
              Back to Quizzes
            </button>
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-2xl shadow-lg p-8 mb-6">
              <div className="text-center mb-8">
                <div className={`text-6xl mb-4 ${quizResults.passed ? '🎉' : '😅'}`}>
                  {quizResults.passed ? '🎉' : '😅'}
                </div>
                <h1 className={`text-3xl font-bold mb-2 ${quizResults.passed ? 'text-green-600' : 'text-orange-600'}`}>
                  {quizResults.passed ? 'Congratulations!' : 'Good Effort!'}
                </h1>
                <p className="text-xl text-gray-600 mb-4">
                  You scored {quizResults.score}% ({quizResults.correct_answers}/{quizResults.total_questions})
                </p>
                <div className="flex items-center justify-center space-x-6 text-sm">
                  <div className="bg-blue-100 text-blue-800 px-4 py-2 rounded-full">
                    +{quizResults.xp_earned} XP Earned
                  </div>
                  {quizResults.passed && (
                    <div className="bg-green-100 text-green-800 px-4 py-2 rounded-full">
                      ✅ Passed!
                    </div>
                  )}
                </div>
              </div>
              
              <div className="space-y-6">
                {quizResults.results.map((result, index) => (
                  <div key={index} className={`p-4 rounded-lg border-2 ${result.is_correct ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="font-semibold text-gray-800">{index + 1}. {result.question}</h3>
                      <span className={`text-2xl ${result.is_correct ? '✅' : '❌'}`}>
                        {result.is_correct ? '✅' : '❌'}
                      </span>
                    </div>
                    <div className="space-y-2 text-sm">
                      <p><strong>Your answer:</strong> {result.your_answer}</p>
                      {!result.is_correct && (
                        <p><strong>Correct answer:</strong> {result.correct_answer}</p>
                      )}
                      {result.explanation && (
                        <p className="text-gray-600"><strong>Explanation:</strong> {result.explanation}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (selectedQuiz) {
    const question = selectedQuiz.questions[currentQuestion];
    const progress = ((currentQuestion + 1) / selectedQuiz.questions.length) * 100;
    
    return (
      <div className="h-full flex flex-col">
        <div className="bg-white shadow-sm border-b p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-gray-800">{selectedQuiz.title}</h2>
            <button onClick={() => setSelectedQuiz(null)} className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
              Exit Quiz
            </button>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all duration-300" style={{width: `${progress}%`}}></div>
          </div>
          <p className="text-sm text-gray-600 mt-2">Question {currentQuestion + 1} of {selectedQuiz.questions.length}</p>
        </div>
        
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="max-w-3xl w-full">
            <div className="bg-white rounded-2xl shadow-lg p-8">
              <h3 className="text-2xl font-bold text-gray-800 mb-8">{question.question}</h3>
              
              <div className="space-y-4 mb-8">
                {question.options.map((option, index) => (
                  <button
                    key={index}
                    onClick={() => selectAnswer(index)}
                    className={`w-full p-4 text-left rounded-xl border-2 transition-all duration-200 ${
                      answers[currentQuestion] === index 
                        ? 'border-purple-500 bg-purple-50 text-purple-800' 
                        : 'border-gray-200 hover:border-purple-300 hover:bg-purple-50'
                    }`}
                  >
                    <div className="flex items-center">
                      <div className={`w-6 h-6 rounded-full border-2 mr-4 flex items-center justify-center ${
                        answers[currentQuestion] === index ? 'border-purple-500 bg-purple-500' : 'border-gray-300'
                      }`}>
                        {answers[currentQuestion] === index && <div className="w-2 h-2 bg-white rounded-full"></div>}
                      </div>
                      <span className="font-medium">{option}</span>
                    </div>
                  </button>
                ))}
              </div>
              
              <div className="flex justify-between">
                <button
                  onClick={prevQuestion}
                  disabled={currentQuestion === 0}
                  className="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Previous
                </button>
                <button
                  onClick={nextQuestion}
                  disabled={answers[currentQuestion] === -1}
                  className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl font-medium hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                >
                  {currentQuestion === selectedQuiz.questions.length - 1 ? 'Submit Quiz' : 'Next'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="bg-white shadow-sm border-b p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
              <span className="text-xl">🏆</span>
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-800">Financial Quizzes</h2>
              <p className="text-sm text-gray-500">Test your knowledge and earn XP</p>
            </div>
          </div>
          <button onClick={onBack} className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
            Back to Chat
          </button>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-6xl mx-auto">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {quizzes.map((quiz) => (
              <div
                key={quiz.id}
                className="bg-white rounded-2xl shadow-lg p-6 cursor-pointer transform hover:scale-105 transition-all duration-200 hover:shadow-xl"
                onClick={() => startQuiz(quiz)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                    quiz.category === 'budgeting' ? 'bg-blue-100 text-blue-800' :
                    quiz.category === 'credit' ? 'bg-purple-100 text-purple-800' :
                    quiz.category === 'investing' ? 'bg-orange-100 text-orange-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {quiz.category}
                  </div>
                  <span className="text-2xl">🏆</span>
                </div>
                
                <h3 className="text-xl font-bold text-gray-800 mb-2">{quiz.title}</h3>
                <p className="text-gray-600 mb-4">{quiz.description}</p>
                
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>📝 {quiz.questions.length} questions</span>
                  <span>🎯 {quiz.xp_reward} XP</span>
                </div>
                
                <div className="mt-4 pt-4 border-t">
                  <div className="text-sm text-gray-500">
                    Pass with {quiz.passing_score}% or higher
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const UserProfile = ({ sessionId, onBack }) => {
  const [profile, setProfile] = useState(null);
  const [badges, setBadges] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProfile();
    loadBadges();
  }, [sessionId]);

  const loadProfile = async () => {
    try {
      const response = await axios.get(`${API}/profile/${sessionId}`);
      setProfile(response.data);
    } catch (error) {
      console.error('Error loading profile:', error);
    }
  };

  const loadBadges = async () => {
    try {
      const response = await axios.get(`${API}/badges`);
      setBadges(response.data);
    } catch (error) {
      console.error('Error loading badges:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading profile...</p>
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-gray-600">No profile found</p>
        </div>
      </div>
    );
  }

  const earnedBadges = badges.filter(badge => profile.badges.includes(badge.id));
  const availableBadges = badges.filter(badge => !profile.badges.includes(badge.id));

  return (
    <div className="h-full flex flex-col">
      <div className="bg-white shadow-sm border-b p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <span className="text-xl">👤</span>
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-800">Your Profile</h2>
              <p className="text-sm text-gray-500">Track your progress</p>
            </div>
          </div>
          <button onClick={onBack} className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
            Back to Chat
          </button>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Stats Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-blue-500 to-purple-600 text-white p-6 rounded-2xl">
              <div className="text-3xl font-bold">{profile.level}</div>
              <div className="text-sm opacity-90">Level</div>
            </div>
            <div className="bg-gradient-to-br from-green-500 to-blue-500 text-white p-6 rounded-2xl">
              <div className="text-3xl font-bold">{profile.total_xp}</div>
              <div className="text-sm opacity-90">Total XP</div>
            </div>
            <div className="bg-gradient-to-br from-orange-500 to-red-500 text-white p-6 rounded-2xl">
              <div className="text-3xl font-bold">{profile.streak_count}</div>
              <div className="text-sm opacity-90">Current Streak</div>
            </div>
            <div className="bg-gradient-to-br from-purple-500 to-pink-500 text-white p-6 rounded-2xl">
              <div className="text-3xl font-bold">{profile.total_questions}</div>
              <div className="text-sm opacity-90">Questions Asked</div>
            </div>
          </div>

          {/* Progress Overview */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">Learning Progress</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{profile.modules_completed.length}</div>
                <div className="text-sm text-gray-600">Modules Completed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{Object.keys(profile.quiz_scores).length}</div>
                <div className="text-sm text-gray-600">Quizzes Taken</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{profile.max_streak}</div>
                <div className="text-sm text-gray-600">Best Streak</div>
              </div>
            </div>
          </div>

          {/* Earned Badges */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">🏆 Earned Badges ({earnedBadges.length})</h3>
            {earnedBadges.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {earnedBadges.map((badge) => (
                  <div key={badge.id} className="flex items-center space-x-4 p-4 bg-yellow-50 border-2 border-yellow-200 rounded-xl">
                    <div className="text-3xl">{badge.icon}</div>
                    <div>
                      <h4 className="font-bold text-gray-800">{badge.name}</h4>
                      <p className="text-sm text-gray-600">{badge.description}</p>
                      <p className="text-xs text-yellow-600">+{badge.xp_reward} XP</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No badges earned yet. Keep learning to unlock achievements!</p>
            )}
          </div>

          {/* Available Badges */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4">🎯 Available Badges</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {availableBadges.map((badge) => (
                <div key={badge.id} className="flex items-center space-x-4 p-4 bg-gray-50 border-2 border-gray-200 rounded-xl opacity-75">
                  <div className="text-3xl grayscale">{badge.icon}</div>
                  <div>
                    <h4 className="font-bold text-gray-600">{badge.name}</h4>
                    <p className="text-sm text-gray-500">{badge.description}</p>
                    <p className="text-xs text-blue-600">{badge.requirement} • +{badge.xp_reward} XP</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main App Component
const FinBuddy = () => {
  const [currentView, setCurrentView] = useState('stage-select'); // stage-select, chat, learning, quiz, profile
  const [sessionId] = useState(() => generateSessionId());
  const [userStage, setUserStage] = useState("general");

  const handleStageSelection = (stage) => {
    setUserStage(stage);
    setCurrentView('chat');
  };

  const renderCurrentView = () => {
    switch (currentView) {
      case 'stage-select':
        return <StageSelector onStageSelect={handleStageSelection} />;
      case 'chat':
        return (
          <ChatInterface 
            sessionId={sessionId}
            userStage={userStage}
            onShowLearning={() => setCurrentView('learning')}
            onShowQuiz={() => setCurrentView('quiz')}
            onShowProfile={() => setCurrentView('profile')}
          />
        );
      case 'learning':
        return (
          <LearningModules 
            sessionId={sessionId}
            userStage={userStage}
            onBack={() => setCurrentView('chat')}
          />
        );
      case 'quiz':
        return (
          <Quiz 
            sessionId={sessionId}
            userStage={userStage}
            onBack={() => setCurrentView('chat')}
          />
        );
      case 'profile':
        return (
          <UserProfile 
            sessionId={sessionId}
            onBack={() => setCurrentView('chat')}
          />
        );
      default:
        return <StageSelector onStageSelect={handleStageSelection} />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Header */}
      {currentView !== 'stage-select' && (
        <div className="bg-white shadow-sm border-b">
          <div className="container mx-auto px-4 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                  <span className="text-sm">🤖</span>
                </div>
                <div>
                  <h1 className="text-lg font-bold text-gray-800">FinBuddy</h1>
                  <p className="text-xs text-gray-500">AI Financial Literacy Assistant</p>
                </div>
              </div>
              <button 
                onClick={() => setCurrentView('stage-select')}
                className="px-3 py-1 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors text-sm font-medium"
              >
                Change Stage
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className={`${currentView !== 'stage-select' ? 'h-[calc(100vh-80px)]' : 'h-screen'}`}>
        {renderCurrentView()}
      </div>
    </div>
  );
};

// Stage Selector Component
const StageSelector = ({ onStageSelect }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto text-center">
          <div className="mb-8">
            <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <span className="text-3xl">🤖</span>
            </div>
            <h1 className="text-4xl font-bold text-gray-800 mb-2">Welcome to FinBuddy</h1>
            <p className="text-xl text-gray-600 mb-2">Your AI-powered financial literacy assistant</p>
            <p className="text-sm text-gray-500">🎮 Gamified Learning • 📚 Bite-sized Modules • 🏆 Interactive Quizzes</p>
          </div>
          
          <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
            <h2 className="text-2xl font-semibold text-gray-800 mb-6">Tell me about your life stage</h2>
            <p className="text-gray-600 mb-8">I'll personalize my advice and learning content to help you with the most relevant financial topics</p>
            
            <div className="grid gap-4">
              <button 
                onClick={() => onStageSelect('student')}
                className="p-6 bg-gradient-to-r from-green-400 to-blue-500 text-white rounded-xl hover:shadow-lg transform hover:scale-105 transition-all duration-200"
              >
                <div className="text-2xl mb-2">🎓</div>
                <div className="font-semibold text-lg">Student</div>
                <div className="text-sm opacity-90">Learning to manage money during studies</div>
              </button>
              
              <button 
                onClick={() => onStageSelect('early_career')}
                className="p-6 bg-gradient-to-r from-purple-400 to-pink-500 text-white rounded-xl hover:shadow-lg transform hover:scale-105 transition-all duration-200"
              >
                <div className="text-2xl mb-2">💼</div>
                <div className="font-semibold text-lg">Early Career</div>
                <div className="text-sm opacity-90">Building financial foundations for the future</div>
              </button>
              
              <button 
                onClick={() => onStageSelect('retiree')}
                className="p-6 bg-gradient-to-r from-orange-400 to-red-500 text-white rounded-xl hover:shadow-lg transform hover:scale-105 transition-all duration-200"
              >
                <div className="text-2xl mb-2">🏖️</div>
                <div className="font-semibold text-lg">Retiree</div>
                <div className="text-sm opacity-90">Managing finances in retirement</div>
              </button>
              
              <button 
                onClick={() => onStageSelect('general')}
                className="p-6 bg-gradient-to-r from-gray-400 to-gray-600 text-white rounded-xl hover:shadow-lg transform hover:scale-105 transition-all duration-200"
              >
                <div className="text-2xl mb-2">💡</div>
                <div className="font-semibold text-lg">General</div>
                <div className="text-sm opacity-90">General financial literacy questions</div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FinBuddy;