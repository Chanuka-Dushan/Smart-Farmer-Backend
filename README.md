# Smart Farmer - Full Stack Application

A comprehensive agricultural management platform with AI-powered spare parts lifecycle prediction, seller marketplace, and mobile app user management. Built with **FastAPI** backend, **Next.js** admin dashboard, and **TensorFlow** machine learning capabilities.

## 🌟 Features

### Core Functionality
- **AI-Powered Spare Parts Analysis** - TensorFlow-based visual inspection for tractor parts condition assessment
- **Lifecycle Prediction** - Predicts remaining operational hours for agricultural spare parts
- **Seller Marketplace** - Connect farmers with verified spare parts sellers
- **Mobile User Management** - Complete user authentication and profile management
- **Admin Dashboard** - Modern Next.js dashboard for platform management
- **Push Notifications** - Firebase Cloud Messaging integration for real-time alerts
- **Payment Processing** - Stripe integration for secure transactions
- **Cloud Storage** - DigitalOcean Spaces for image and file storage

### AI/ML Capabilities
- MobileNetV2-based image classification
- Transfer learning with custom training pipeline
- Real-time prediction API
- Model evaluation and metrics tracking
- Automated data augmentation

## System Architecture Diagram

<img width="1677" height="803" alt="image" src="https://github.com/user-attachments/assets/5ae42a6f-0d4e-4588-aa19-1994326380c6" />


## 📁 Project Structure

```
smart_farmer_backend/
│
├── backend/                           # Python/FastAPI Backend
│   ├── main.py                        # Main FastAPI application (3646 lines)
│   ├── config.py                      # Centralized configuration management
│   ├── requirements.txt               # Python dependencies
│   │
│   ├── models/                        # Database & Schema Models
│   │   ├── schemas.py                 # Pydantic validation schemas
│   │   ├── user.py                    # User database models
│   │   └── __init__.py
│   │
│   ├── routes/                        # API Route Modules
│   │   ├── auth_routes.py             # Authentication endpoints
│   │   ├── admin_routes.py            # Admin management APIs
│   │   ├── user_routes.py             # Mobile user endpoints
│   │   └── __init__.py
│   │
│   ├── utils/                         # Utility Modules
│   │   ├── auth.py                    # JWT authentication & password hashing
│   │   ├── database.py                # Database connection utilities
│   │   ├── email_utils.py             # Email functionality
│   │   └── __init__.py
│   │
│   ├── ai_knowledge.py                # AI knowledge base for spare parts
│   ├── ml_utils.py                    # ML model utilities & evaluation
│   ├── fcm_utils.py                   # Firebase Cloud Messaging
│   ├── spaces_utils.py                # DigitalOcean Spaces integration
│   │
│   ├── train_visual_model.py          # ML model training script
│   ├── init_database.py               # Database initialization
│   ├── migrate_db.py                  # Database migration script
│   │
│   ├── dataset/                       # Training Data
│   │   ├── damaged_parts/             # Damaged parts images
│   │   └── good_parts/                # Good condition parts images
│   │
│   ├── models/                        # ML Models Storage
│   │   ├── smart_farmer_vision_v1_0_acc_0_82.h5
│   │   └── training_*/                # Training session logs
│   │
│   ├── uploads/                       # User Uploaded Files
│   │   ├── profile_pictures/
│   │   └── spare-parts/
│   │
│   ├── logs/                          # Application Logs
│   ├── tests/                         # Test Suite
│   │   ├── test_api_endpoints.py
│   │   └── test_ml_components.py
│   │
│   ├── entrypoint.sh                  # Docker entrypoint script
│   └── Dockerfile.backup              # Backup Docker configuration
│
├── dashboard/                         # Next.js Admin Dashboard
│   ├── app/                           # Next.js App Router
│   │   ├── page.tsx                   # Landing page
│   │   ├── layout.tsx                 # Root layout
│   │   ├── globals.css                # Global styles
│   │   ├── admin/                     # Admin dashboard pages
│   │   ├── users/                     # User management
│   │   ├── sellers/                   # Seller management
│   │   ├── products/                  # Product management
│   │   ├── orders/                    # Order tracking
│   │   ├── notifications/             # Notification center
│   │   ├── analytics/                 # Analytics dashboard
│   │   └── settings/                  # Settings pages
│   │
│   ├── components/                    # React Components
│   │   ├── ui/                        # shadcn/ui components
│   │   ├── dashboard-layout.tsx       # Dashboard layout wrapper
│   │   ├── ProtectedRoute.tsx         # Auth guard component
│   │   ├── theme-provider.tsx         # Dark mode provider
│   │   └── theme-toggle.tsx           # Theme switcher
│   │
│   ├── context/
│   │   └── AuthContext.tsx            # Authentication context
│   │
│   ├── hooks/                         # Custom React hooks
│   │   ├── use-mobile.ts
│   │   └── use-toast.ts
│   │
│   ├── lib/
│   │   └── utils.ts                   # Utility functions
│   │
│   ├── public/                        # Static assets
│   ├── package.json                   # Node dependencies
│   ├── next.config.ts                 # Next.js configuration
│   ├── tsconfig.json                  # TypeScript config
│   └── tailwind.config.ts             # Tailwind CSS config
│
├── docker-compose.yml                 # Docker Compose configuration
├── Dockerfile                         # Production Docker image
├── Procfile                           # Deployment configuration
├── main.py                            # Root-level FastAPI entry point
├── requirements.txt                   # Root-level dependencies
└── README.md                          # This file
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+** installed
- **Node.js 18+** and npm installed
- **PostgreSQL** (optional, SQLite used by default)
- **Git** for version control

### Option 1: Local Development Setup

#### Backend Setup (FastAPI)

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

4. **Set up environment variables:**
   Create a `.env` file in the backend directory:
   ```env
   # Database
   DATABASE_URL=sqlite:///./smart_farmer.db
   
   # JWT Configuration
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=43200
   
   # API Keys (Optional)
   GEMINI_API_KEY=your-gemini-api-key
   GROQ_API_KEY=your-groq-api-key
   WEATHER_API_KEY=your-weather-api-key
   
   # DigitalOcean Spaces (Optional)
   SPACES_KEY=your-spaces-key
   SPACES_SECRET=your-spaces-secret
   SPACES_REGION=nyc3
   SPACES_BUCKET=your-bucket-name
   
   # Stripe (Optional)
   STRIPE_SECRET_KEY=your-stripe-secret-key
   STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
   
   # Firebase (Optional - for push notifications)
   # Place firebase-adminsdk.json in backend directory
   ```

5. **Initialize the database:**
   ```bash
   python init_database.py
   ```

6. **Run the FastAPI server:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   
   The backend will be available at:
   - API: `http://localhost:8000`
   - Interactive API Docs: `http://localhost:8000/docs`
   - Alternative Docs: `http://localhost:8000/redoc`

#### Dashboard Setup (Next.js)

1. **Navigate to the dashboard directory:**
   ```bash
   cd dashboard
   ```

2. **Install Node dependencies:**
   ```bash
   npm install
   ```

3. **Configure environment variables:**
   Create a `.env.local` file in the dashboard directory:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Run the development server:**
   ```bash
   npm run dev
   ```
   
   The dashboard will be available at: `http://localhost:3000`

5. **Build for production:**
   ```bash
   npm run build
   npm start
   ```

### Option 2: Docker Deployment

1. **Using Docker Compose (Recommended):**
   ```bash
   docker-compose up --build
   ```
   
   This will start:
   - Backend API on `http://localhost:8080`
   - PostgreSQL database

2. **Using Docker only:**
   ```bash
   docker build -t smart-farmer-backend .
   docker run -p 8080:8080 smart-farmer-backend
   ```

### Option 3: Production Deployment

#### Deploy to DigitalOcean App Platform

1. **Prepare your repository** (GitHub, GitLab, or Bitbucket)

2. **Create a new app** in DigitalOcean App Platform

3. **Configure the app:**
   - **Source:** Link your repository
   - **Build Command:** Automatic detection
   - **Run Command:** Uses the Procfile configuration

4. **Set environment variables** in the App Platform dashboard

5. **Deploy** - The platform will automatically build and deploy

#### Deploy Backend Manually

```bash
cd backend
gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080 main:app
```

#### Deploy Dashboard

```bash
cd dashboard
npm run build
npm start
```

Or deploy to Vercel:
```bash
vercel deploy --prod
```

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy** - SQL ORM for database operations
- **PostgreSQL/SQLite** - Database systems
- **Pydantic** - Data validation using Python type hints
- **JWT** - JSON Web Tokens for authentication
- **Passlib & Bcrypt** - Password hashing
- **TensorFlow** - Machine learning framework
- **Pillow** - Image processing
- **Boto3** - AWS S3/DigitalOcean Spaces SDK
- **Firebase Admin** - Push notifications
- **Stripe** - Payment processing
- **Gunicorn & Uvicorn** - Production ASGI servers

### Frontend (Dashboard)
- **Next.js 16** - React framework with App Router
- **React 19** - UI library
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Re-usable component library
- **Radix UI** - Headless UI primitives
- **Recharts** - Data visualization
- **Lucide React** - Icon library
- **next-themes** - Dark mode support

### Machine Learning
- **TensorFlow/Keras** - Deep learning
- **MobileNetV2** - Base model for transfer learning
- **scikit-learn** - Model evaluation
- **NumPy** - Numerical computing
- **Pandas** - Data manipulation
- **Matplotlib & Seaborn** - Visualization

### DevOps & Cloud
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **DigitalOcean Spaces** - Object storage
- **Firebase Cloud Messaging** - Push notifications
- **Vercel** - Frontend hosting (optional)

## 📊 Database Models

### Core Tables

1. **admins** - Admin users for dashboard
2. **app_users** - Mobile app users (farmers)
3. **sellers** - Spare parts sellers
4. **spare_part_requests** - User requests for parts
5. **spare_part_offers** - Seller offers on requests
6. **payments** - Transaction records
7. **notifications** - Push notification logs

## 🔑 API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/unified-login` - Unified login endpoint
- `POST /login` - Admin login
- `POST /verify-token` - Verify JWT token

### Admin Dashboard
- `POST /api/admin/login` - Admin authentication
- `GET /api/admin/sellers` - List all sellers
- `GET /api/admin/users` - List all users
- `POST /api/notifications/send` - Send push notifications

### Mobile Users
- `POST /api/users/register` - User registration
- `GET /api/users/me` - Get current user profile
- `PUT /api/users/me` - Update user profile
- `PUT /api/users/me/password` - Change password

### Sellers
- `POST /api/sellers/register` - Seller registration
- `POST /api/sellers/login` - Seller authentication
- `GET /api/sellers/me` - Get seller profile
- `PUT /api/sellers/me/location` - Update shop location
- `GET /api/sellers/locations` - Get all seller locations

### Spare Parts & Predictions
- `POST /api/predict-lifecycle` - AI-powered lifecycle prediction
- `POST /api/identify-part` - Upload image and identify spare part type (mobile app)
- `POST /api/spare-parts/requests` - Create part request
- `POST /api/spare-parts/offers` - Create offer on request

### Payments
- `POST /api/payments/create-intent` - Create Stripe payment intent
- `POST /api/payments/confirm` - Confirm payment

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check endpoint

## 🤖 Machine Learning Pipeline

### Training a New Model

1. **Prepare your dataset:**
   ```
   backend/dataset/
   ├── damaged_parts/    # Images of damaged parts
   └── good_parts/       # Images of good condition parts
   ```

2. **Configure training parameters** in `config.py`:
   ```python
   TRAINING_CONFIG = {
       "img_size": (224, 224),
       "batch_size": 16,
       "epochs": 100,
       "learning_rate": 0.0001,
       ...
   }
   ```

3. **Run training:**
   ```bash
   cd backend
   python train_visual_model.py
   ```

4. **Model will be saved in:** `backend/models/training_YYYYMMDD_HHMMSS/`

### Using the Prediction API

```python
import requests

# Predict part condition
response = requests.post(
    "http://localhost:8000/api/predict-lifecycle",
    files={"image": open("part_image.jpg", "rb")},
    data={
        "part_name": "tractor fan belt",
        "usage_hours": 500
    }
)

result = response.json()
print(f"Condition: {result['condition']}")
print(f"Remaining hours: {result['estimated_remaining_hours']}")
```

# Identify Spare Part from Image
```python
import requests

response = requests.post(
    "http://localhost:8000/api/identify-part",
    files={"image": open("part_image.jpg", "rb")}
)

info = response.json()
print(f"Identified part: {info['label']} (confidence {info['confidence']:.2%})")
```

## 🧪 Testing

### Run Backend Tests

```bash
cd backend
pytest tests/ -v
```

### Test Coverage

```bash
pytest tests/ --cov=. --cov-report=html
```

## 📦 Environment Variables Reference

### Required Variables
```env
SECRET_KEY=<random-secret-key>
DATABASE_URL=<database-connection-string>
```

### Optional Services
```env
# AI/ML APIs
GEMINI_API_KEY=<google-gemini-api-key>
GROQ_API_KEY=<groq-api-key>

# Cloud Storage
SPACES_KEY=<digitalocean-spaces-key>
SPACES_SECRET=<digitalocean-spaces-secret>
SPACES_BUCKET=<bucket-name>

# Payment Processing
STRIPE_SECRET_KEY=<stripe-secret>
STRIPE_PUBLISHABLE_KEY=<stripe-public>

# ML Configuration
MODEL_VERSION=v1.0
DISABLE_TENSORFLOW=false
MIN_PREDICTION_CONFIDENCE=0.7
```

## 🔧 Common Commands

### Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload

# Run with custom port
uvicorn main:app --host 0.0.0.0 --port 8080

# Initialize database
python init_database.py

# Train ML model
python train_visual_model.py

# Run tests
pytest tests/
```

### Frontend
```bash
# Install dependencies
npm install

# Development server
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

### Docker
```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in detached mode
docker-compose up -d

# Stop containers
docker-compose down

# View logs
docker-compose logs -f

# Build single container
docker build -t smart-farmer-backend .

# Run single container
docker run -p 8080:8080 smart-farmer-backend
```

## 📝 Initial Setup Checklist

- [ ] Clone the repository
- [ ] Install Python 3.11+ and Node.js 18+
- [ ] Create backend virtual environment
- [ ] Install backend dependencies
- [ ] Create `.env` file with configuration
- [ ] Initialize database
- [ ] Run backend server
- [ ] Install dashboard dependencies
- [ ] Configure dashboard environment variables
- [ ] Run dashboard development server
- [ ] (Optional) Set up Firebase for push notifications
- [ ] (Optional) Configure Stripe for payments
- [ ] (Optional) Set up DigitalOcean Spaces for storage
- [ ] Create admin account using init_database.py
- [ ] Test API endpoints at http://localhost:8000/docs
- [ ] Access dashboard at http://localhost:3000


## 🔐 Security Notes

- Always use strong, unique passwords in production
- Never commit `.env` files to version control
- Keep API keys and secrets secure
- Use HTTPS in production
- Regularly update dependencies
- Enable CORS only for trusted domains
- Implement rate limiting for production APIs

## 📱 Mobile App Integration

This backend supports mobile app integration with:
- JWT-based authentication
- FCM push notifications
- Profile picture uploads
- Social login (Google, Facebook)
- Real-time spare parts marketplace
- Payment processing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software. All rights reserved.

## 👥 Support

For support, email support@smartfarmer.com or open an issue in the repository.

## 🚀 Deployment Platforms

### Recommended Platforms

1. **Backend:**
   - DigitalOcean App Platform
   - Railway
   - Render
   - AWS Elastic Beanstalk
   - Google Cloud Run

2. **Dashboard:**
   - Vercel (Recommended)
   - Netlify
   - DigitalOcean Static Sites

3. **Database:**
   - DigitalOcean Managed PostgreSQL
   - Supabase
   - Railway PostgreSQL
   - AWS RDS

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [TensorFlow Guide](https://www.tensorflow.org/guide)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

---

**Built with ❤️ for Farmers**
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
