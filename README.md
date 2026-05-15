# 🎤 AI Mock Interview Platform

An intelligent mock interview platform built with Streamlit that uses facial expression analysis, AI-powered question generation, and real-time feedback to help candidates prepare for job interviews.

## 🌟 Features

- **User Authentication**: Secure registration and login system
- **Resume Parsing**: Automatic extraction of skills, experience, and education
- **Intelligent Question Generation**: AI-powered questions based on job description and resume
- **Live Interview**: Real-time interview with video capture and facial expression analysis
- **Facial Expression Analysis**: Engagement and emotion detection during interview
- **Performance Analytics**: Detailed feedback and scoring for each answer
- **Dashboard**: Interview history and performance tracking
- **Export Reports**: Download interview results and recommendations

## 📋 Project Structure

```
AI_Mock_Int_Streamlit/
├── core/
│   ├── __init__.py
│   ├── auth.py                # User registration and login
│   ├── database.py            # SQLAlchemy models and database
│   ├── face_analyzer.py       # Facial expression analysis
│   ├── interview.py           # Q&A generation and evaluation
│   └── resume.py              # Resume parsing
├── pages/
│   ├── 1_Setup_Interview.py   # Interview setup page
│   ├── 2_Live_Interview.py    # Live interview interface
│   ├── 3_Interview_Complete.py # Results and feedback
│   └── 4_Dashboard.py         # User dashboard
├── app.py                     # Main entry point
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose setup
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)
- PostgreSQL (optional, SQLite used by default)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ai-mock-interview.git
   cd ai-mock-interview
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

The application will be available at `http://localhost:8501`

### Using Docker

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Access the services**
   - Streamlit App: http://localhost:8501
   - PgAdmin: http://localhost:5050
   - Database: localhost:5432

## 🎯 How It Works

### 1. Setup Interview
- Create an account or login
- Upload your resume (PDF/TXT)
- Paste the job description
- System automatically extracts key information

### 2. Live Interview
- Answer AI-generated questions
- Real-time facial expression analysis
- Video/audio recording capability
- Get live engagement feedback

### 3. Interview Complete
- Detailed scoring and feedback
- Areas of strength and improvement
- Question-by-question analysis
- Export results as PDF report

### 4. Dashboard
- View interview history
- Track performance trends
- Analyze skill development
- Access previous reports

## 🔧 Configuration

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/dbname

# OpenAI API (optional, for enhanced feedback)
OPENAI_API_KEY=your-api-key

# AWS S3 (optional, for storing videos)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
```

## 📦 Dependencies

- **Streamlit**: Web framework
- **SQLAlchemy**: ORM and database
- **OpenCV**: Computer vision for facial analysis
- **DeepFace**: Facial expression analysis
- **LangChain**: LLM integration
- **PDFPlumber**: Resume parsing

## 🔐 Security

- Passwords are hashed using bcrypt
- SQL injection protection via SQLAlchemy ORM
- Environment variables for sensitive data
- Optional JWT authentication ready for implementation

## 📈 Performance

- Optimized facial detection with caching
- Database indexes on frequently queried fields
- Async processing for video analysis
- CDN-ready architecture

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Change Streamlit port
streamlit run app.py --server.port 8502
```

### Database Connection Issues
```bash
# Verify PostgreSQL is running
psql -U postgres -h localhost
```

### Missing Dependencies
```bash
# Update pip and reinstall
pip install --upgrade pip
pip install -r requirements.txt
```

## 📝 Development

### Running Tests
```bash
pytest
```

### Code Quality
```bash
black .
flake8 .
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Streamlit team for the amazing framework
- OpenCV and DeepFace communities
- All contributors and users

## 📧 Contact

For questions or support, please contact:
- Email: support@mockinteview.com
- Issues: GitHub Issues

---

**Happy Interviewing! 🚀**
