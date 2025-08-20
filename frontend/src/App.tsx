
import LeftSection from './components/LeftSection';
import ChatInterface from './components/ChatInterface';
import './App.css';

function App() {
	return (
		<div className='app'>
			<LeftSection />
			<div className='right-section'>
				<ChatInterface />
			</div>
		</div>
	);
}

export default App;
