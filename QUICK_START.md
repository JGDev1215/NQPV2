# Quick Start - Get NQP Running in 5 Minutes

## The Problem
The app needs Supabase database credentials to start. Without them, it crashes immediately.

## The Solution (5 minutes)

### Step 1: Get Free Supabase Account (2 minutes)

1. Go to: **https://supabase.com/dashboard/sign-in**
2. Click "Sign up" (it's free!)
3. Sign up with GitHub, Google, or email
4. You'll be redirected to the dashboard

### Step 2: Create New Project (2 minutes)

1. Click **"New project"** button
2. Fill in:
   - **Name:** `nqp-dev` (or any name you like)
   - **Database Password:** Create a strong password (save this!)
   - **Region:** Choose closest to you
   - **Pricing Plan:** Free (default)
3. Click **"Create new project"**
4. Wait 1-2 minutes while it sets up (grab a coffee ☕)

### Step 3: Get Your Credentials (30 seconds)

Once project is ready:

1. Look for the **"Connect"** button in your project dashboard
2. OR go to: **Settings** (gear icon) → **API**
3. You'll see:
   - **Project URL** (looks like: `https://xxxxx.supabase.co`)
   - **anon public** key (long string starting with `eyJ...`)
4. Copy both of these!

### Step 4: Update Your .env File (30 seconds)

Open the `.env` file in your NQP directory and update these two lines:

```bash
# Replace these placeholder values:
SUPABASE_URL=https://xxxxx.supabase.co           # ← Paste your Project URL here
SUPABASE_KEY=eyJxxxxxxxxxxxxxxxxxxxxxxx          # ← Paste your anon public key here
```

**Example of what it should look like:**
```bash
SUPABASE_URL=https://abcdefghijk.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprIiwicm9sZSI6ImFub24iLCJpYXQiOjE2MzAwMDAwMDAsImV4cCI6MTk0NTU3NjAwMH0.xxxxxxxxxxxxxxxxxxxxxxxxx
```

### Step 5: Run the App! (30 seconds)

```bash
# In your terminal, from the NQP directory:
source venv/bin/activate
python3 app.py
```

You should see:
```
================================================================================
NQP APPLICATION READY
================================================================================
 * Running on http://0.0.0.0:5000
```

### Step 6: Open in Browser

Go to: **http://localhost:5000/api**

You should see the NQP dashboard! 🎉

---

## Available URLs

Once the app is running, you can access:

- **Dashboard:** http://localhost:5000/api
- **Market Data API:** http://localhost:5000/api/data
- **Health Check:** http://localhost:5000/api/health
- **Scheduler Status:** http://localhost:5000/api/scheduler/status
- **Predictions:** http://localhost:5000/api/predictions/NQ=F

---

## 🐛 Troubleshooting

### Still getting "Invalid URL" error?

**Check your .env file:**
```bash
cat .env | grep SUPABASE
```

Make sure:
- ✅ URL starts with `https://`
- ✅ URL ends with `.supabase.co`
- ✅ Key starts with `eyJ`
- ❌ No quotes around the values
- ❌ No placeholder text like "your-project-url-here"

### App crashes with database errors?

The app will automatically create the database tables on first run. If you see errors:

1. Check your Supabase project is active (not paused)
2. Try running the database initialization:
   ```bash
   source venv/bin/activate
   python3 nasdaq_predictor/database/init_db.py
   ```

### Port 5000 already in use?

Change the port in your `.env`:
```bash
PORT=8080  # Use a different port
```

Then access the app at: http://localhost:8080/api

---

## Next Steps

Once the app is running:

1. ✅ Test the API endpoints
2. ✅ View market predictions in the dashboard
3. ✅ Check the modularization documentation:
   - Read `START_HERE.md`
   - Review `MODULARIZATION_ANALYSIS.md`
   - Follow `MODULARIZATION_ROADMAP.md`

---

## Quick Commands

```bash
# Start the app
source venv/bin/activate
python3 app.py

# Stop the app
Ctrl+C

# View app logs
tail -f app.log

# Check if app is running
curl http://localhost:5000/api/health
```

---

That's it! You should be up and running in 5 minutes. 🚀
