import React from 'react';
import LeftSection from './components/LeftSection';
import './App.css';

function App() {
	return (
		<div className='app'>
			<LeftSection />
			<div className='right-section'>
				<div className='chat-container'>
					<div className='chat-placeholder'>
						<h2>Chat interface will be implemented here</h2>
						<p>This is where the travel bot conversation will take place.</p>
					</div>
				</div>
			</div>
		</div>
	);
}

export default App;
