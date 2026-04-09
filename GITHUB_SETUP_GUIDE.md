# GitHub Setup Guide - Step by Step

Follow these steps to create a GitHub repository and push your project.

## Step 1: Create GitHub Repository

1. Go to https://github.com
2. Click the "+" icon in top right → "New repository"
3. Fill in:
   - **Repository name**: `code-plagiarism-detection`
   - **Description**: `A production-ready FastAPI service that detects code plagiarism across 26+ programming languages using Token-based and AST-based analysis.`
   - **Visibility**: Choose "Private" (recommended) or "Public"
   - **DO NOT** check "Initialize with README" (we already have one)
4. Click "Create repository"

## Step 2: Initialize Git in Your Project

Open terminal in your project folder and run:

```bash
git init
```

## Step 3: Add All Files

```bash
git add .
```

This adds all files except those in `.gitignore` (like `.env`, `venv/`, `__pycache__/`)

## Step 4: Make First Commit

```bash
git commit -m "Initial commit: Code plagiarism detection service"
```

## Step 5: Connect to GitHub

Replace `YOUR_USERNAME` and `YOUR_REPO_NAME` with your actual GitHub username and repository name:

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
```

Example:
```bash
git remote add origin https://github.com/john/code-plagiarism-detection.git
```

## Step 6: Push to GitHub

```bash
git branch -M main
git push -u origin main
```

If prompted, enter your GitHub username and password (or personal access token).

## Step 7: Verify Upload

1. Go to your GitHub repository URL
2. You should see all your files uploaded
3. Check that `.env` is NOT visible (it should be ignored)

## Step 8: Give Access to Team Leader

### Option A: Add as Collaborator (Recommended)
1. Go to your repository on GitHub
2. Click "Settings" tab
3. Click "Collaborators" in left sidebar
4. Click "Add people"
5. Enter your team leader's GitHub username or email
6. Select their permission level (usually "Write" or "Admin")
7. Click "Add [username] to this repository"

### Option B: Share Repository Link (if public)
If you made the repository public, just share the URL:
```
https://github.com/YOUR_USERNAME/code-plagiarism-detection
```

## Important Notes

### ⚠️ NEVER Commit .env File!
Your `.env` file contains database credentials. It's already in `.gitignore`, but double-check:

```bash
git status
```

If you see `.env` in the list, DO NOT commit! Remove it:
```bash
git rm --cached .env
```

### Share Database Credentials Separately
Send your team leader the `.env` file content through a secure channel (email, Slack, etc.), NOT through GitHub!

Example `.env` content to share:
```
DATABASE_URL=postgresql://username:password@host:port/database
```

## Troubleshooting

### "Permission denied" error
You may need to set up SSH keys or use a personal access token instead of password.

**Using Personal Access Token:**
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo` (full control)
4. Copy the token
5. Use it as password when pushing

### "Repository not found" error
Check that:
- Repository name is correct
- You have access to the repository
- Remote URL is correct: `git remote -v`

### Files not uploading
Check `.gitignore` - make sure you're not accidentally ignoring important files.

## After Setup

Your team leader can now:
1. Clone the repository: `git clone <repo-url>`
2. Follow `SETUP.md` to install dependencies
3. Create their own `.env` file with database credentials
4. Run the demo: `python demo_showcase.py`
5. Start the API: `uvicorn main:app --reload`

## Need Help?

If you encounter issues:
1. Check GitHub's documentation: https://docs.github.com
2. Ask your team leader
3. Search for the error message online

Good luck! 🚀
