# Git & GitHub Quick Reference

## Initialize & Configure Git

### First Time Setup

```bash
# Check if git is installed
git --version

# Configure global settings (one time)
git config --global user.name "Your Full Name"
git config --global user.email "your.email@example.com"

# Verify configuration
git config --list
```

---

## Getting Your Code to GitHub

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. **Repository name**: `voice-agent`
3. **Description**: "Real-Time Multilingual Voice AI Agent for Clinical Appointment Booking"
4. **Public** (so evaluators can access it)
5. **DO NOT** check "Initialize with README" (you already have one)
6. Click **Create Repository**

### Step 2: Initialize Local Git Repository

```bash
# Navigate to your project
cd /path/to/Voice-Agent

# Initialize git (if not already done)
git init

# Check git status
git status
```

### Step 3: Create .gitignore

```bash
# Create .gitignore file
cat > .gitignore << 'EOF'
# Environment
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.pytest_cache/
.mypy_cache/
venv/
env/

# Node
node_modules/
npm-debug.log
yarn-error.log
.next/
out/
.vercel

# IDE
.vscode/
.idea/
.DS_Store
*.swp
*.swo

# Logs
logs/
*.log

# Docker
.dockerignore
postgres_data/
redis_data/
EOF

# Verify .gitignore is created
cat .gitignore
```

### Step 4: Add All Files to Git

```bash
# Stage all files
git add .

# Check what will be committed
git status

# Should see all your files listed as "new file"
```

### Step 5: Create First Commit

```bash
git commit -m "Initial commit: Real-Time Multilingual Voice AI Agent

- FastAPI backend with WebSocket support for real-time voice
- Next.js 15 frontend with React components
- PostgreSQL database with 6 tables and proper indexing
- Redis memory layer for session management
- Real tool calling with GPT-4o-mini orchestration
- Multilingual support: English, Hindi, Tamil
- <450ms latency architecture with component tracking
- Campaign scheduler for appointment reminders
- Docker Compose for full stack deployment
- Comprehensive documentation and testing guides"
```

### Step 6: Connect to GitHub

```bash
# Add remote origin
git remote add origin https://github.com/YOUR_USERNAME/voice-agent.git

# Verify remote is added
git remote -v
# Should show:
# origin  https://github.com/YOUR_USERNAME/voice-agent.git (fetch)
# origin  https://github.com/YOUR_USERNAME/voice-agent.git (push)
```

### Step 7: Push to GitHub

```bash
# Rename branch to main (if on 'master')
git branch -M main

# Push code to GitHub
git push -u origin main

# This will prompt for authentication:
# - GitHub username
# - OR Personal Access Token (PAT)
```

---

## GitHub Authentication Options

### Option A: Personal Access Token (Recommended)

```bash
# Create token at: https://github.com/settings/tokens

# When prompted for password, use the token instead:
# Username: YOUR_USERNAME
# Password: ghp_xxxxxxxxxxxxxxxxxxxx

# To save credentials locally:
git config credential.helper store
git push  # Will store token for future use
```

### Option B: SSH Key Setup

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your.email@example.com"

# Add to SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub: Settings → SSH and GPG keys → New SSH key
# Paste the public key

# Use SSH remote instead
git remote add origin git@github.com:YOUR_USERNAME/voice-agent.git
git push -u origin main
```

---

## Common Git Commands

### Check Status
```bash
git status
# Shows modified, untracked, and staged files
```

### View Commit History
```bash
git log --oneline
# Shows recent commits

git log --oneline -10
# Shows last 10 commits

git log --graph --all --oneline
# Shows commit graph
```

### Make Additional Commits

```bash
# After making changes, add them
git add .
# or specific file:
git add path/to/file.py

# Commit changes
git commit -m "Brief description of changes"

# Push to GitHub
git push origin main
```

### Update from  GitHub

```bash
# Pull latest changes
git pull origin main

# Fetch without merging
git fetch origin
```

### Branch Management

```bash
# Create new branch
git checkout -b feature/new-feature

# Switch to existing branch
git checkout main

# Delete branch
git branch -d feature/new-feature

# List all branches
git branch -a
```

### Undo Changes

```bash
# Discard changes to file
git checkout -- path/to/file.py

# Unstage file
git reset HEAD path/to/file.py

# Revert last commit (keep changes)
git reset --soft HEAD~1

# Revert last commit (discard changes)
git reset --hard HEAD~1
```

---

## Verifying GitHub Push

### Check Repository on GitHub

1. Go to https://github.com/YOUR_USERNAME/voice-agent
2. Verify:
   - ✅ All files are visible
   - ✅ README.md shows at top
   - ✅ Folder structure correct
   - ✅ All documentation present
   - ✅ Backend folder has main.py
   - ✅ Frontend folder has package.json
   - ✅ docker-compose.yml visible
   - ✅ .env.example present (not .env)

### Check Git Status Locally

```bash
# Verify all is pushed
git status
# Should show: "On branch main, nothing to commit, working tree clean"

# Verify remote
git remote -v
# Should show origin with correct URL

# Check branch info
git branch -a
# Should show main branch
```

---

## Adding More Files Later

```bash
# Make changes or add new files

# Stage all changes
git add .

# Commit with descriptive message
git commit -m "Add feature: describe what changed"

# Push to GitHub
git push origin main
```

---

## Before Final Submission

### Clean Git Commit History

```bash
# View commits
git log --oneline -10

# Ensure final commit message is descriptive
git commit --amend -m "Updated commit message"

# Check that .env is NOT in git
git status | grep .env
# Should show: .env (not in repo)
```

### Verify No Secrets in Git

```bash
# Search for common secret patterns
git log -p | grep -i "apikey\|api_key\|secret\|password"
# Should return nothing

# Verify .env not committed
git ls-files | grep .env
# Should return nothing (or only .env.example)
```

### Check Repository Size

```bash
# Check total size
du -sh .git
# Should be < 100MB

# Find large files
git rev-list --all --objects | sort -k2 | tail -10
```

---

## GitHub Repository Settings

### After Pushing, Configure Repository

1. Go to https://github.com/YOUR_USERNAME/voice-agent/settings

2. **General** → Make sure "Default branch" is **main**

3. **Code security and analysis**:
   - Enable "Dependabot alerts"
   - Enable "Dependabot security updates"

4. **About section** (click gear icon):
   - **Description**: "Real-Time Multilingual Voice AI Agent for Clinical Appointment Booking"
   - **Website**: (optional)
   - **Topics**: Add these tags:
     - `voice-ai`
     - `healthcare`
     - `fastapi`
     - `nextjs`
     - `multilingual`
     - `real-time`
     - `appointment-booking`
     - `websocket`
     - `postgresql`
     - `redis`

5. **Visibility** → Public (already set during creation)

---

## Getting Repository URL for Submission

```bash
# Your repository URL is:
https://github.com/YOUR_USERNAME/voice-agent

# For git operations:
git@github.com:YOUR_USERNAME/voice-agent.git

# Get current remote URL
git remote get-url origin
```

---

## Troubleshooting Git Issues

### "fatal: not a git repository"

```bash
# You're not in the right directory
cd /path/to/Voice-Agent

# Or reinitialize
git init
```

### "Permission denied (publickey)"

```bash
# SSH key issue, use HTTPS instead
git remote set-url origin https://github.com/YOUR_USERNAME/voice-agent.git

# Try push again
git push -u origin main
```

### "Updates were rejected because the tip of your current branch is behind"

```bash
# Pull latest changes first
git pull origin main

# Then push
git push origin main
```

### "Changes not showing on GitHub"

```bash
# Verify remote is correct
git remote -v

# Verify push succeeded
git log --oneline -1
# Note the commit hash

# Check on GitHub if that commit exists
```

### "Accidentally committed .env file"

```bash
# Remove from  git (but keep local copy)
git rm --cached .env

# Add to .gitignore
echo ".env" >> .gitignore

# Commit the fix
git add .gitignore
git commit -m "Remove .env from  git tracking"

# Rewrite history to remove it completely (advanced)
git filter-branch --tree-filter 'rm -f .env' HEAD
git push -f origin main  # Force push (careful!)
```

---

## Final Checklist Before Submission

```bash
# 1. Verify everything is committed
git status
# Should show: "working tree clean"

# 2. Check remote URL
git remote -v
# Should show correct GitHub URL

# 3. Verify all files are on GitHub
git ls-files | head -20
# Should see all your main files

# 4. Check that secrets are not in history
git log -p | grep -i "api_key"
# Should show nothing

# 5. Verify .env is not tracked
git ls-files | grep "\.env$"
# Should return empty

# 6. Count total files
git ls-files | wc -l
# Should be 30+ files

# 7. Check repository size
du -sh .git
# Should be reasonable

# 8. Final verification
echo "Git status: $(git status --porcelain | wc -l) uncommitted changes"
echo "Remote: $(git remote get-url origin)"
echo "Branch: $(git branch --show-current)"
```

---

## Submitting

Once GitHub is ready:

1. **Get Repository URL**:
   ```
   https://github.com/YOUR_USERNAME/voice-agent
   ```

2. **Record Loom video** (3 minutes) showing:
   - System startup
   - Voice demo
   - Latency metrics
   - Code walkthrough

3. **Submit to evaluators**:
   - GitHub Repository URL
   - Loom Video Link
   - Cover letter (optional)

---

## Additional Resources

- **Git Documentation**: https://git-scm.com/docs
- **GitHub Help**: https://docs.github.com
- **Pro Git Book**: https://git-scm.com/book/en/v2 (free)
- **GitHub Quickstart**: https://docs.github.com/en/get-started/quickstart

---

**Your submission is ready! Good luck! 🚀**
