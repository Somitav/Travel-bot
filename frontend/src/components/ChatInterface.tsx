import React, { useState, useRef, useEffect } from 'react';
import './ChatInterface.css';

interface Message {
	id: string;
	text: string;
	isUser: boolean;
	timestamp: Date;
	type?: 'text' | 'itinerary';
	itineraryData?: ItineraryData;
}

interface ItineraryData {
	title: string;
	days: ItineraryDay[];
}

interface ItineraryDay {
	title: string;
	activities: string[];
}

const API_BASE_URL = 'http://localhost:8000';

const ChatInterface: React.FC = () => {
	const [messages, setMessages] = useState<Message[]>([]);
	const [inputValue, setInputValue] = useState('');
	const [isTyping, setIsTyping] = useState(false);
	const [isConnected, setIsConnected] = useState(false);
	const [sessionId, setSessionId] = useState<string>('');
	const [isHealthChecking, setIsHealthChecking] = useState(true);
	const messagesEndRef = useRef<HTMLDivElement>(null);

	// Generate unique session ID
	const generateSessionId = () => {
		return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
	};

	// Health check function
	const checkHealth = async (): Promise<boolean> => {
		try {
			const response = await fetch(`${API_BASE_URL}/health`, {
				method: 'GET',
				headers: {
					'Content-Type': 'application/json',
				},
			});
			return response.ok;
		} catch (error) {
			console.error('Health check failed:', error);
			return false;
		}
	};

	// Initialize session and check health
	useEffect(() => {
		const initializeSession = async () => {
			setIsHealthChecking(true);
			const isServerHealthy = await checkHealth();

			if (!isServerHealthy) {
				alert(
					'⚠️ Travel Bot server is not available. Please make sure the backend server is running on port 8000.'
				);
				setIsConnected(false);
				setIsHealthChecking(false);
				return;
			}

			setIsConnected(true);
			const newSessionId = generateSessionId();
			setSessionId(newSessionId);

			// Add initial greeting message
			const initialMessage: Message = {
				id: '1',
				text: "Hi there! I'm Travel Bot, your AI travel assistant. How can I help you plan your next adventure?",
				isUser: false,
				timestamp: new Date(),
				type: 'text',
			};
			setMessages([initialMessage]);
			setIsHealthChecking(false);
		};

		initializeSession();
	}, []);

	const scrollToBottom = () => {
		messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
	};

	useEffect(() => {
		scrollToBottom();
	}, [messages]);

	// Parse itinerary from backend response
	const parseItineraryFromText = (text: string): ItineraryData | null => {
		try {
			// Simple parsing - look for day-by-day structure
			const lines = text.split('\n');
			const days: ItineraryDay[] = [];
			let currentDay: ItineraryDay | null = null;
			let title = 'Travel Itinerary';

			// Extract title if present
			const titleMatch = text.match(/itinerary for (.+?):/i);
			if (titleMatch) {
				title = titleMatch[1];
			}

			for (const line of lines) {
				const trimmedLine = line.trim();
				if (!trimmedLine) continue;

				// Check if it's a day header
				const dayMatch = trimmedLine.match(/^(Day \d+:?|Day \d+ -)(.*)/i);
				if (dayMatch) {
					if (currentDay) {
						days.push(currentDay);
					}
					currentDay = {
						title: trimmedLine,
						activities: [],
					};
				} else if (
					currentDay &&
					(trimmedLine.startsWith('•') ||
						trimmedLine.startsWith('-') ||
						trimmedLine.match(/^\d+\./))
				) {
					// This is an activity
					currentDay.activities.push(trimmedLine);
				} else if (
					currentDay &&
					trimmedLine.includes(':') &&
					!trimmedLine.includes('Day')
				) {
					// This might be a time-based activity
					currentDay.activities.push(trimmedLine);
				}
			}

			if (currentDay) {
				days.push(currentDay);
			}

			return days.length > 0 ? { title, days } : null;
		} catch (error) {
			console.error('Error parsing itinerary:', error);
			return null;
		}
	};

	const handleSendMessage = async () => {
		if (!inputValue.trim() || !isConnected || !sessionId) return;

		const newMessage: Message = {
			id: Date.now().toString(),
			text: inputValue,
			isUser: true,
			timestamp: new Date(),
			type: 'text',
		};

		setMessages((prev) => [...prev, newMessage]);
		const userInput = inputValue;
		setInputValue('');
		setIsTyping(true);

		try {
			// Send message to backend using Server-Side Events
			const response = await fetch(`${API_BASE_URL}/chat/${sessionId}`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify({ message: userInput }),
			});

			if (!response.ok) {
				throw new Error(`HTTP error! status: ${response.status}`);
			}

			const reader = response.body?.getReader();
			const decoder = new TextDecoder();

			if (!reader) {
				throw new Error('No response body reader available');
			}

			let buffer = '';
			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				buffer += decoder.decode(value, { stream: true });
				const lines = buffer.split('\n');
				buffer = lines.pop() || '';

				for (const line of lines) {
					if (line.startsWith('data: ')) {
						try {
							const data = JSON.parse(line.slice(6));

							if (data.type === 'message') {
								const botMessage: Message = {
									id: (Date.now() + Math.random()).toString(),
									text: data.content,
									isUser: false,
									timestamp: new Date(),
									type: 'text',
								};
								setMessages((prev) => [...prev, botMessage]);
							} else if (data.type === 'itinerary') {
								const itineraryData = parseItineraryFromText(data.content);
								const botMessage: Message = {
									id: (Date.now() + Math.random()).toString(),
									text: data.content,
									isUser: false,
									timestamp: new Date(),
									type: itineraryData ? 'itinerary' : 'text',
									itineraryData: itineraryData || undefined,
								};
								setMessages((prev) => [...prev, botMessage]);
							} else if (data.type === 'done') {
								setIsTyping(false);
								break;
							}
						} catch (parseError) {
							console.error('Error parsing SSE data:', parseError);
						}
					}
				}
			}
		} catch (error) {
			console.error('Error sending message:', error);
			const errorMessage: Message = {
				id: (Date.now() + 1).toString(),
				text: "I'm sorry, I encountered an error while processing your message. Please try again.",
				isUser: false,
				timestamp: new Date(),
				type: 'text',
			};
			setMessages((prev) => [...prev, errorMessage]);
		} finally {
			setIsTyping(false);
		}
	};

	const handleKeyPress = (e: React.KeyboardEvent) => {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSendMessage();
		}
	};

	const renderMessage = (message: Message) => {
		if (message.type === 'itinerary' && message.itineraryData) {
			return (
				<div key={message.id} className='message bot'>
					<div className='itinerary-message'>
						<h3 className='itinerary-header'>{message.itineraryData.title}</h3>
						<div className='itinerary-content'>
							{message.itineraryData.days.map((day, index) => (
								<div key={index} className='itinerary-day'>
									<h4 className='day-title'>{day.title}</h4>
									<ul className='day-activities'>
										{day.activities.map((activity, activityIndex) => (
											<li key={activityIndex}>{activity}</li>
										))}
									</ul>
								</div>
							))}
						</div>
					</div>
				</div>
			);
		}

		return (
			<div
				key={message.id}
				className={`message ${message.isUser ? 'user' : 'bot'}`}
			>
				<div className='message-content'>
					<p style={{ whiteSpace: 'pre-wrap' }}>{message.text}</p>
					<span className='message-time'>
						{message.timestamp.toLocaleTimeString([], {
							hour: '2-digit',
							minute: '2-digit',
						})}
					</span>
				</div>
			</div>
		);
	};

	// Show loading state during health check
	if (isHealthChecking) {
		return (
			<div className='chat-interface'>
				<div className='chat-header'>
					<div className='bot-info'>
						<div className='bot-avatar'>
							<span className='bot-avatar-icon'>🤖</span>
						</div>
						<div className='bot-details'>
							<h3 className='bot-name'>Travel Bot</h3>
							<span className='bot-status'>
								<span className='status-indicator connecting'></span>
								Connecting...
							</span>
						</div>
					</div>
				</div>
				<div className='chat-messages'>
					<div className='message bot'>
						<div className='message-content'>
							<p>Connecting to Travel Bot server...</p>
						</div>
					</div>
				</div>
			</div>
		);
	}

	return (
		<div className='chat-interface'>
			<div className='chat-header'>
				<div className='bot-info'>
					<div className='bot-avatar'>
						<span className='bot-avatar-icon'>🤖</span>
					</div>
					<div className='bot-details'>
						<h3 className='bot-name'>Travel Bot</h3>
						<span className='bot-status'>
							<span
								className={`status-indicator ${
									isConnected ? 'online' : 'offline'
								}`}
							></span>
							{isConnected ? 'Online' : 'Offline'}
						</span>
					</div>
				</div>
			</div>

			<div className='chat-messages'>
				{messages.map(renderMessage)}

				{isTyping && (
					<div className='message bot'>
						<div className='message-content'>
							<div className='typing-indicator'>
								<span></span>
								<span></span>
								<span></span>
							</div>
						</div>
					</div>
				)}

				<div ref={messagesEndRef} />
			</div>

			<div className='chat-input'>
				<div className='input-container'>
					<textarea
						value={inputValue}
						onChange={(e) => setInputValue(e.target.value)}
						onKeyPress={handleKeyPress}
						placeholder={
							isConnected
								? 'Type your message here...'
								: 'Server offline - please try again later'
						}
						className='message-input'
						rows={1}
						disabled={!isConnected}
					/>
					<button
						onClick={handleSendMessage}
						className='send-button'
						disabled={!inputValue.trim() || !isConnected}
					>
						<span className='send-icon'>➤</span>
					</button>
				</div>
			</div>
		</div>
	);
};

export default ChatInterface;
