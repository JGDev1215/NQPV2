# NQP Local Setup Guide

## ✅ What's Already Done

I've set up your local development environment:

1. ✅ Created Python virtual environment (`venv/`)
2. ✅ Installed all dependencies from `requirements.txt`
3. ✅ Created `.env` file with default configuration

## 🔴 What You Need to Do: Get Supabase Credentials

The application requires a Supabase database. Here's how to set it up:

### Option 1: Use Existing Supabase Project (Recommended if you have one)

If you already have a Supabase project for this app:

1. **Go to your Supabase Dashboard:**
   - Visit: https://app.supabase.com

2. **Select your project**

3. **Get your credentials:**
   - Click on "Settings" (gear icon) in the sidebar
   - Click "API" in the settings menu
   - Copy these values:
     - **Project URL** (e.g., `https://xxxxx.supabase.co`)
     - **anon public** key

4. **Update your `.env` file:**
   ```bash
   # Open .env file and replace these lines:
   SUPABASE_URL=https://your-actual-project.supabase.co
   SUPABASE_KEY=your-actual-anon-key-here
   ```

### Option 2: Create New Supabase Project (If you don't have one)

1. **Sign up/Login to Supabase:**
   - Go to: https://app.supabase.com
   - Sign up for free account (if you don't have one)

2. **Create a new project:**
   - Click "New Project"
   - Choose organization
   - Enter project name (e.g., "NQP-Dev")
   - Choose a database password (save this!)
   - Select region (closest to you)
   - Click "Create new project"
   - Wait 1-2 minutes for setup

3. **Get your credentials** (same as Option 1, step 3 above)

4. **Set up the database schema:**
   - The app will create tables automatically on first run
   - Or run the migration script:
     ```bash
     source venv/bin/activate
     python nasdaq_predictor/database/init_db.py
     ```

### Option 3: Run Without Database (Mock Mode - For Testing Only)

If you want to test the app without setting up Supabase:

**Note:** This mode is not fully implemented yet. You'll need to:
1. Skip database operations
2. Use only yfinance data fetching
3. Disable prediction storage

---

## 🚀 How to Run the Application

### Step 1: Activate Virtual Environment

```bash
# From the NQP directory
source venv/bin/activate
```

### Step 2: Verify Environment Variables

```bash
# Check your .env file has valid credentials
cat .env | grep SUPABASE
```

Make sure these are NOT the placeholder values:
- ❌ `SUPABASE_URL=your-project-url-here` (BAD - placeholder)
- ✅ `SUPABASE_URL=https://xxxxx.supabase.co` (GOOD - real URL)

### Step 3: Run the Application

```bash
# Make sure you're in the NQP directory
python3 app.py
```

### Step 4: Access the Application

Once you see:
```
================================================================================
NQP APPLICATION READY
================================================================================
 * Running on http://0.0.0.0:5000
```

Open your browser and go to:
- **API Dashboard:** http://localhost:5000/api
- **Market Data:** http://localhost:5000/api/data
- **Health Check:** http://localhost:5000/api/health
- **Scheduler Status:** http://localhost:5000/api/scheduler/status

---

## 🔧 Configuration Options

### Enable/Disable Background Scheduler

In your `.env` file:

```bash
# Disable scheduler (for development)
SCHEDULER_ENABLED=false

# Enable scheduler (for production)
SCHEDULER_ENABLED=true
```

### Debug Mode

```bash
# Development mode (detailed errors, auto-reload)
FLASK_ENV=development
FLASK_DEBUG=True

# Production mode (secure, no debug info)
FLASK_ENV=production
FLASK_DEBUG=False
```

### Change Port

```bash
# Default port
PORT=5000

# Custom port
PORT=8080
```

---

## 🐛 Troubleshooting

### Error: "Invalid URL"

**Problem:** Supabase credentials not set correctly

**Solution:**
1. Check `.env` file has real credentials (not placeholders)
2. Verify URL format: `https://xxxxx.supabase.co`
3. Verify key is the "anon public" key (not service role key)

### Error: "Module not found"

**Problem:** Virtual environment not activated

**Solution:**
```bash
source venv/bin/activate
python3 app.py
```

### Error: "Port already in use"

**Problem:** Another app is using port 5000

**Solution:**
```bash
# Option 1: Change port in .env
PORT=8080

# Option 2: Kill process using port 5000
lsof -ti:5000 | xargs kill -9
```

### Error: Database connection fails

**Problem:** Supabase project not accessible

**Solution:**
1. Check internet connection
2. Verify Supabase project is not paused (free tier pauses after inactivity)
3. Check credentials are correct
4. Try accessing Supabase dashboard to verify project is running

---

## 📦 Project Structure

```
NQP/
├── venv/                    # Virtual environment (created)
├── .env                     # Environment variables (created)
├── app.py                   # Main application entry point
├── requirements.txt         # Python dependencies
├── nasdaq_predictor/        # Main package
│   ├── api/                # API routes
│   ├── services/           # Business logic
│   ├── database/           # Database layer
│   ├── analysis/           # Prediction logic
│   └── ...
├── templates/              # HTML templates
└── static/                 # CSS, JS files
```

---

## 🧪 Testing the Application

### Test API Endpoints

```bash
# Health check
curl http://localhost:5000/api/health

# Get market data
curl http://localhost:5000/api/data

# Check scheduler status
curl http://localhost:5000/api/scheduler/status
```

### Test with Browser

1. Open http://localhost:5000/api
2. You should see the dashboard with market predictions
3. Data auto-refreshes every 60 seconds

---

## 📝 Next Steps

Once the app is running successfully:

1. **Read the modularization docs:**
   - `START_HERE.md` - Quick overview
   - `MODULARIZATION_ANALYSIS.md` - Current state analysis
   - `MODULARIZATION_ROADMAP.md` - Implementation plan

2. **Start Phase 1 of modularization:**
   - Create `core/` directory structure
   - Implement base abstractions
   - See `MODULARIZATION_ROADMAP.md` for details

3. **Explore the codebase:**
   ```bash
   # View project structure
   tree -L 2 nasdaq_predictor/

   # Run tests (when available)
   pytest

   # Check code quality
   flake8 nasdaq_predictor/
   ```

---

## 🎯 Quick Commands Reference

```bash
# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Run application
python3 app.py

# Run in background
nohup python3 app.py > app.log 2>&1 &

# Stop background app
pkill -f "python3 app.py"

# View logs
tail -f app.log

# Deactivate virtual environment
deactivate
```

---

## 🆘 Still Having Issues?

1. **Check logs:** Look for error messages when starting the app
2. **Verify Python version:** Should be Python 3.13+ (`python3 --version`)
3. **Check dependencies:** Run `pip list` to see installed packages
4. **Review environment:** Run `cat .env` to check configuration

---

## 📞 Common Questions

**Q: Do I need a paid Supabase account?**
A: No, the free tier is sufficient for development and testing.

**Q: Can I use a different database?**
A: The app is currently built for Supabase. Switching databases would require significant refactoring.

**Q: How do I update the app?**
A:
```bash
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
python3 app.py
```

**Q: Can I deploy this locally for production?**
A: Yes, but consider:
- Change `FLASK_DEBUG=False`
- Use `gunicorn` instead of Flask dev server
- Set up proper monitoring
- Use environment secrets management

---

**Setup completed!** Once you add valid Supabase credentials to `.env`, the app will run successfully. 🚀
