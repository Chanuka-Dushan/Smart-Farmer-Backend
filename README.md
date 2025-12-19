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

### DigitalOcean App Platform (Recommended)

This project includes a `.do-app.yaml` configuration file for easy deployment to DigitalOcean App Platform.

#### Quick Deploy

1. **Push your code to GitHub/GitLab**
   ```bash
   git add .
   git commit -m "Add deployment configuration"
   git push origin main
   ```

2. **Create a new app on DigitalOcean**
   - Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
   - Click "Create App"
   - Connect your repository
   - DigitalOcean will automatically detect the `.do-app.yaml` configuration

3. **Deploy**
   - Review the detected configuration
   - Click "Next" and then "Create Resources"
   - Your app will be built and deployed automatically

#### Manual Configuration (if not using .do-app.yaml)

If you prefer to configure manually:

**Backend Service:**
- **Source Directory**: `backend`
- **Build Command**: `pip install -r requirements.txt`
- **Run Command**: `uvicorn main:app --host 0.0.0.0 --port 8080`
- **HTTP Port**: `8080`
- **Environment**: Python 3.12

**Environment Variables:**
- `PORT`: `8080`
- `PYTHONUNBUFFERED`: `1`

#### Database Considerations

> **⚠️ Important**: The current setup uses SQLite which is **not recommended for production** on DigitalOcean App Platform because:
> - Data will be lost on each deployment
> - SQLite doesn't work well with multiple instances
>
> **Recommended**: Migrate to DigitalOcean Managed PostgreSQL Database
> 1. Create a managed PostgreSQL database in DigitalOcean
> 2. Update `main.py` to use PostgreSQL instead of SQLite
> 3. Add `psycopg2-binary` to `requirements.txt`
> 4. Set `DATABASE_URL` environment variable

#### Using doctl CLI

Test your build locally before deploying:

```bash
# Install doctl
# Windows (using Chocolatey)
choco install doctl

# macOS
brew install doctl

# Authenticate
doctl auth init

# Test build locally (from project root)
doctl apps create --spec .do-app.yaml
```

---

### Other Deployment Options

#### Backend (FastAPI)
- **Railway**: Connect GitHub repo, Railway auto-detects FastAPI
- **Render**: Use `gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app`
- **AWS/Google Cloud/Azure**: Deploy using Docker or platform-specific services

#### Dashboard (Next.js)
- **Vercel** (Recommended): Connect GitHub repo, auto-deploys
- **Netlify**: Connect repo, configure build command: `npm run build`
- **AWS Amplify**: Connect repo, configure build settings
- **Cloudflare Pages**: Connect repo, auto-detects Next.js

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
