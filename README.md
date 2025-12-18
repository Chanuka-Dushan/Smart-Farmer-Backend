# Smart Farmer - Full Stack Application

A modern full-stack application with a **FastAPI** backend and a **Next.js** admin dashboard built with **shadcn/ui**.

## 📁 Project Structure

```
smart_farmer_backend/
│
├── backend/                    # Python/FastAPI Backend
│   ├── main.py                # FastAPI application entry point
│   ├── models/                # Database models
│   │   └── __init__.py
│   ├── venv/                  # Python virtual environment (gitignored)
│   └── requirements.txt       # Python dependencies
│
├── dashboard/                  # Next.js/shadcn Admin Dashboard
│   ├── app/                   # Next.js app directory
│   │   ├── page.tsx          # Dashboard homepage
│   │   ├── layout.tsx        # Root layout
│   │   └── globals.css       # Global styles
│   ├── components/            # React components
│   │   └── ui/               # shadcn/ui components
│   ├── lib/                   # Utility functions
│   ├── public/                # Static assets
│   ├── node_modules/          # Node dependencies (gitignored)
│   ├── package.json           # Node dependencies
│   ├── next.config.ts         # Next.js configuration
│   └── tsconfig.json          # TypeScript configuration
│
├── .gitignore                 # Git ignore rules (Python + Node)
└── README.md                  # This file
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+** installed
- **Node.js 18+** and npm installed
- Git (optional, for version control)

### Backend Setup (FastAPI)

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment:**
   
   **Windows:**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
   
   **macOS/Linux:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the FastAPI server:**
   ```bash
   uvicorn main:app --reload
   ```
   
   The backend will be available at: `http://localhost:8000`
   
   API documentation: `http://localhost:8000/docs`

### Dashboard Setup (Next.js)

1. **Navigate to the dashboard directory:**
   ```bash
   cd dashboard
   ```

2. **Install Node dependencies:**
   ```bash
   npm install
   ```

3. **Run the development server:**
   ```bash
   npm run dev
   ```
   
   The dashboard will be available at: `http://localhost:3000`

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **Uvicorn** - ASGI server for running FastAPI
- **SQLAlchemy** - SQL toolkit and ORM
- **Pydantic** - Data validation using Python type annotations
- **Python-Jose** - JWT token handling
- **Passlib** - Password hashing

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Beautiful, accessible component library
- **Lucide React** - Icon library

## 📦 Available Scripts

### Backend
```bash
# Activate virtual environment
.\venv\Scripts\activate  # Windows
source venv/bin/activate # macOS/Linux

# Run development server
uvicorn main:app --reload

# Run production server
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Dashboard
```bash
# Development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

## 🎨 Dashboard Features

The admin dashboard includes:

- **📊 Statistics Cards** - Real-time metrics with beautiful gradients
- **📈 Analytics Overview** - Placeholder for chart integrations
- **🔔 Recent Activity Feed** - Latest user actions and events
- **⚡ Quick Actions** - Common tasks and shortcuts
- **🎨 Modern UI** - Built with shadcn/ui components
- **🌓 Dark Mode Support** - Automatic theme switching
- **📱 Responsive Design** - Works on all screen sizes

## 🔧 Customization

### Adding shadcn/ui Components

```bash
cd dashboard
npx shadcn@latest add [component-name]
```

Available components: button, card, input, table, dialog, dropdown-menu, and many more!

### Backend API Endpoints

Edit `backend/main.py` to add new API endpoints:

```python
@app.get("/api/your-endpoint")
async def your_endpoint():
    return {"message": "Hello World"}
```

### Dashboard Pages

Create new pages in `dashboard/app/`:

```bash
dashboard/app/
├── page.tsx           # Home page (/)
├── users/
│   └── page.tsx      # Users page (/users)
└── settings/
    └── page.tsx      # Settings page (/settings)
```

## 🔐 Environment Variables

Create `.env` files for environment-specific configuration:

**Backend (.env):**
```env
DATABASE_URL=sqlite:///./users.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Dashboard (.env.local):**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📝 Development Workflow

1. **Start the backend server** (Terminal 1)
2. **Start the dashboard** (Terminal 2)
3. Make changes to your code
4. Both servers will auto-reload on file changes

## 🚢 Deployment

### Backend (FastAPI)
- Deploy to: Railway, Render, AWS, Google Cloud, Azure
- Use `gunicorn` for production: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app`

### Dashboard (Next.js)
- Deploy to: Vercel, Netlify, AWS Amplify, Cloudflare Pages
- Vercel is recommended for Next.js applications

## 📚 Learn More

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [shadcn/ui Documentation](https://ui.shadcn.com/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

---

**Built with ❤️ using FastAPI and Next.js**
