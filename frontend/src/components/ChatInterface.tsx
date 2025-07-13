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

const ChatInterface: React.FC = () => {
	const [messages, setMessages] = useState<Message[]>([
		{
			id: '1',
			text: "Hi there! I'm Travel Bot, your AI travel assistant. How can I help you plan your next adventure?",
			isUser: false,
			timestamp: new Date(),
			type: 'text',
		},
	]);
	const [inputValue, setInputValue] = useState('');
	const [isTyping, setIsTyping] = useState(false);
	const messagesEndRef = useRef<HTMLDivElement>(null);

	const scrollToBottom = () => {
		messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
	};

	useEffect(() => {
		scrollToBottom();
	}, [messages]);

	const parisItinerary: ItineraryData = {
		title: 'Paris: 3-Day Itinerary',
		days: [
			{
				title: 'Day 1: Iconic Paris',
				activities: [
					'Morning: Visit the Eiffel Tower (book tickets in advance)',
					'Lunch: Café near Champ de Mars',
					'Afternoon: Louvre Museum (focus on key exhibits)',
					'Evening: Seine River cruise at sunset',
					'Dinner: Le Marais district',
				],
			},
			{
				title: 'Day 2: Cultural Immersion',
				activities: [
					'Morning: Notre-Dame Cathedral (exterior) & Sainte-Chapelle',
					'Lunch: Latin Quarter',
					"Afternoon: Musée d'Orsay",
					'Evening: Montmartre & Sacré-Cœur',
					'Dinner: Traditional bistro in Montmartre',
				],
			},
			{
				title: 'Day 3: Parisian Lifestyle',
				activities: [
					'Morning: Luxembourg Gardens & Saint-Germain-des-Prés',
					'Lunch: Café de Flore or Les Deux Magots',
					'Afternoon: Shopping on Champs-Élysées',
					'Evening: Arc de Triomphe (climb to the top)',
					'Dinner: Farewell dinner at a Michelin-starred restaurant',
				],
			},
		],
	};

	const handleSendMessage = () => {
		if (inputValue.trim()) {
			const newMessage: Message = {
				id: Date.now().toString(),
				text: inputValue,
				isUser: true,
				timestamp: new Date(),
				type: 'text',
			};

			setMessages((prev) => [...prev, newMessage]);
			const userInput = inputValue.toLowerCase();
			setInputValue('');
			setIsTyping(true);

			// Check if user is asking for Paris itinerary
			setTimeout(() => {
				if (
					userInput.includes('paris') &&
					(userInput.includes('plan') ||
						userInput.includes('trip') ||
						userInput.includes('itinerary') ||
						userInput.includes('3-day') ||
						userInput.includes('3 day'))
				) {
					const botResponse: Message = {
						id: (Date.now() + 1).toString(),
						text: "Here's a suggested itinerary for your 3 days in Paris! Would you like me to adjust anything or provide more details about specific attractions?",
						isUser: false,
						timestamp: new Date(),
						type: 'itinerary',
						itineraryData: parisItinerary,
					};
					setMessages((prev) => [...prev, botResponse]);
				} else {
					const botResponse: Message = {
						id: (Date.now() + 1).toString(),
						text: "Thanks for your message! I'd be happy to help you plan your trip. Could you tell me more about your destination preferences? For example, try asking me about planning a 3-day trip to Paris!",
						isUser: false,
						timestamp: new Date(),
						type: 'text',
					};
					setMessages((prev) => [...prev, botResponse]);
				}
				setIsTyping(false);
			}, 1500);
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
					<p>{message.text}</p>
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
							<span className='status-indicator online'></span>
							Online
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
						placeholder='Type your message here...'
						className='message-input'
						rows={1}
					/>
					<button
						onClick={handleSendMessage}
						className='send-button'
						disabled={!inputValue.trim()}
					>
						<span className='send-icon'>➤</span>
					</button>
				</div>
			</div>
		</div>
	);
};

export default ChatInterface;
