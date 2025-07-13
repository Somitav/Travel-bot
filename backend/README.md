# Travel Bot Backend

A FastAPI-based backend for the Travel Bot application that provides AI-powered travel planning with real-time conversation support.

## Features

- **Real-time Communication**: Server-Side Events (SSE) for real-time chat
- **AI-Powered Planning**: Uses Groq API for intelligent travel planning
- **Persistent Storage**: MongoDB for conversation state management
- **Modular Architecture**: Clean separation of concerns with organized modules

## Architecture

```
backend/
├── main.py          # FastAPI application and routes
├── models.py        # Data models and schemas
├── database.py      # MongoDB operations
├── services.py      # Business logic and AI services
├── utils.py         # Utility functions
├── requirements.txt # Python dependencies
├── .env            # Environment variables (not in git)
└── .gitignore      # Git ignore rules
```

## Setup

### Prerequisites

- Python 3.8+
- MongoDB Atlas account (or local MongoDB)
- Groq API key

### Installation

1. **Clone the repository** (if not already done):

   ```bash
   git clone <repository-url>
   cd travel-bot/backend
   ```

2. **Create virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file in the backend directory with:

   ```env
   # MongoDB Configuration
   MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority

   # Groq API Configuration
   GROQ_API_KEY=your_groq_api_key_here

   # Application Configuration
   ENV=development
   DEBUG=true
   ```

5. **Run the application**:

   ```bash
   python main.py
   ```

   Or with uvicorn:

   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Endpoints

### Main Endpoints

- **POST** `/chat/{session_id}` - Start or continue a conversation
- **GET** `/session/{session_id}` - Get conversation state
- **DELETE** `/session/{session_id}` - Delete conversation session
- **GET** `/health` - Health check endpoint

### Chat Endpoint Usage

```javascript
// Example frontend usage
const response = await fetch('/chat/user123', {
	method: 'POST',
	headers: {
		'Content-Type': 'application/json',
	},
	body: JSON.stringify({
		message: 'I want to plan a 3-day trip to Paris',
	}),
});

// Handle Server-Side Events
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
	const { done, value } = await reader.read();
	if (done) break;

	const chunk = decoder.decode(value);
	const lines = chunk.split('\n');

	for (const line of lines) {
		if (line.startsWith('data: ')) {
			const data = JSON.parse(line.substring(6));
			console.log('Received:', data);
		}
	}
}
```

## Environment Variables

| Variable       | Description                          | Required |
| -------------- | ------------------------------------ | -------- |
| `MONGODB_URL`  | MongoDB connection string            | Yes      |
| `GROQ_API_KEY` | Groq API key for AI services         | Yes      |
| `ENV`          | Environment (development/production) | No       |
| `DEBUG`        | Enable debug logging                 | No       |

## Development

### Running Tests

```bash
# Run tests (when implemented)
pytest tests/
```

### Code Style

The project follows PEP 8 standards. Use `black` for formatting:

```bash
pip install black
black .
```

### Project Structure

- **models.py**: Contains data models like `ConversationState`
- **database.py**: MongoDB connection and CRUD operations
- **services.py**: Business logic, AI integration, and conversation flow
- **utils.py**: Utility functions for date parsing, greetings, etc.
- **main.py**: FastAPI application with route definitions

## Security Notes

- Never commit `.env` files to version control
- Use environment variables for all sensitive configuration
- The `.env` file is already in `.gitignore`
- Use strong passwords and secure connection strings

## Deployment

For production deployment:

1. Set production environment variables
2. Use a production WSGI server like Gunicorn
3. Configure proper CORS settings
4. Use SSL/TLS certificates
5. Set up monitoring and logging

```bash
# Production example
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here]
