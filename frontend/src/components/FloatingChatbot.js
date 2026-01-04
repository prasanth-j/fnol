import React, { useState, useEffect, useRef } from 'react';
import { Card, Form, Button, Alert, Dropdown } from 'react-bootstrap';
import axios from 'axios';
import './FloatingChatbot.css';

function FloatingChatbot({ sessionId, user }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [questionType, setQuestionType] = useState('text');
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (isOpen && !hasStarted) {
      setHasStarted(true);
      sendMessage('', true);
    }
  }, [isOpen, hasStarted]);

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = async (message = '', isInitial = false) => {
    if (!isInitial && !message.trim()) return;

    setLoading(true);

    if (!isInitial) {
      setMessages(prev => [...prev, { type: 'user', text: message }]);
      setInput('');
    }

    try {
      const response = await axios.post('http://localhost:8000/chat', {
        message: message || '',
        sessionId: sessionId
      });

      const botResponse = response.data;

      setMessages(prev => {
        const lastMessage = prev[prev.length - 1];
        if (lastMessage && lastMessage.type === 'bot' && lastMessage.text === botResponse.response) {
          return prev;
        }
        return [...prev, { type: 'bot', text: botResponse.response }];
      });
      
      setQuestionType(botResponse.questionType);
      setOptions(botResponse.options || []);

      if (botResponse.completed) {
        setCompleted(true);
        setTimeout(() => {
          setMessages([]);
          setCompleted(false);
          setHasStarted(false);
          sendMessage('reset', true);
        }, 5000);
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        type: 'bot',
        text: err.response?.data?.detail || 'An error occurred. Please try again.'
      }]);
    } finally {
      setLoading(false);
      if (inputRef.current) {
        inputRef.current.focus();
      }
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!loading && !completed && input.trim()) {
      sendMessage(input);
    }
  };

  const handleYesNo = (value) => {
    if (!loading && !completed) {
      sendMessage(value);
    }
  };

  const handleOptionSelect = (option) => {
    if (!loading && !completed) {
      sendMessage(option);
    }
  };

  const handleStartNew = () => {
    setMessages([]);
    setCompleted(false);
    setHasStarted(false);
    sendMessage('reset', true);
  };

  return (
    <>
      {/* Floating Chat Button */}
      <button
        className={`floating-chat-button ${isOpen ? 'active' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Open chat"
      >
        {isOpen ? (
          <i className="bi bi-x-lg"></i>
        ) : (
          <i className="bi bi-chat-dots"></i>
        )}
      </button>

      {/* Chat Popup */}
      {isOpen && (
        <div className="chat-popup">
          <Card className="chat-card">
            <Card.Header className="chat-header">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <strong>Insurance Assistant</strong>
                  <span className="badge bg-success ms-2">Online</span>
                </div>
                {completed && (
                  <Button variant="outline-light" size="sm" onClick={handleStartNew}>
                    New Chat
                  </Button>
                )}
              </div>
            </Card.Header>
            
            <Card.Body className="chat-body p-0">
              <div className="messages-container">
                {messages.length === 0 && !loading && (
                  <div className="empty-state">
                    <i className="bi bi-chat-dots"></i>
                    <p>How can I help you today?</p>
                  </div>
                )}
                
                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`message ${msg.type}`}
                  >
                    {msg.text.split('\n').map((line, i) => (
                      <div key={i}>{line}</div>
                    ))}
                  </div>
                ))}
                
                {loading && (
                  <div className="message bot loading">
                    <span className="spinner-border spinner-border-sm me-2"></span>
                    Processing...
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {!completed && (
                <div className="chat-input-area">
                  {questionType === 'yesno' && (
                    <div className="d-flex gap-2 mb-2">
                      <Button
                        variant="success"
                        size="sm"
                        onClick={() => handleYesNo('Yes')}
                        disabled={loading}
                        className="flex-fill"
                      >
                        Yes
                      </Button>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => handleYesNo('No')}
                        disabled={loading}
                        className="flex-fill"
                      >
                        No
                      </Button>
                    </div>
                  )}

                  {questionType === 'options' && options.length > 0 && (
                    <div className="mb-2">
                      <Dropdown>
                        <Dropdown.Toggle variant="primary" size="sm" className="w-100" disabled={loading}>
                          Select an option
                        </Dropdown.Toggle>
                        <Dropdown.Menu className="w-100">
                          {options.map((option, idx) => (
                            <Dropdown.Item
                              key={idx}
                              onClick={() => handleOptionSelect(option)}
                            >
                              {option}
                            </Dropdown.Item>
                          ))}
                        </Dropdown.Menu>
                      </Dropdown>
                    </div>
                  )}

                  {(questionType === 'text' || questionType === 'yesno') && (
                    <Form onSubmit={handleSubmit}>
                      <div className="input-group">
                        <Form.Control
                          ref={inputRef}
                          type="text"
                          placeholder="Type your message..."
                          value={input}
                          onChange={(e) => setInput(e.target.value)}
                          disabled={loading || questionType === 'yesno'}
                          size="sm"
                        />
                        {questionType === 'text' && (
                          <Button type="submit" variant="primary" disabled={loading || !input.trim()} size="sm">
                            <i className="bi bi-send"></i>
                          </Button>
                        )}
                      </div>
                    </Form>
                  )}
                </div>
              )}

              {completed && (
                <div className="chat-input-area">
                  <Alert variant="success" className="mb-0 text-center py-2">
                    <small>
                      <strong>✓ Submitted!</strong> Starting new conversation...
                    </small>
                  </Alert>
                </div>
              )}
            </Card.Body>
          </Card>
        </div>
      )}
    </>
  );
}

export default FloatingChatbot;

