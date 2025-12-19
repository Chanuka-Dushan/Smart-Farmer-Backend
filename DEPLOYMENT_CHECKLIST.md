# 🚀 Digital Ocean Deployment Checklist

## Pre-Deployment Checklist

- [x] ✅ Fixed requirements.txt (added psycopg2-binary)
- [x] ✅ Updated Python version to 3.11.7
- [x] ✅ Updated build command in .do-app.yaml
- [x] ✅ Added CORS middleware to main.py
- [x] ✅ Created Procfile for alternative deployment
- [x] ✅ Updated .gitignore

## Deployment Steps

- [ ] **Step 1**: Commit all changes
  ```bash
  git add .
  git commit -m "Fix: Digital Ocean deployment configuration"
  ```

- [ ] **Step 2**: Push to GitHub
  ```bash
  git push origin main
  ```

- [ ] **Step 3**: Add PostgreSQL Database in Digital Ocean
  - Go to your app in Digital Ocean dashboard
  - Click "Create" → "Database"
  - Select PostgreSQL
  - Choose a plan (Dev Database is free)
  - Wait for database to be created and attached

- [ ] **Step 4**: Deploy Application
  - Auto-deploy should trigger automatically
  - OR manually click "Deploy" in Digital Ocean dashboard

- [ ] **Step 5**: Monitor Build Logs
  - Watch for successful build completion
  - Check for any error messages

- [ ] **Step 6**: Test Deployment
  ```bash
  # Replace with your actual app URL
  curl https://your-app-name.ondigitalocean.app/
  ```
  - Should return: `{"message": "Smart Farmer Backend is Running!"}`

- [ ] **Step 7**: Test API Endpoints
  - Visit: `https://your-app-name.ondigitalocean.app/docs`
  - Test `/register` endpoint
  - Test `/login` endpoint

## Post-Deployment Tasks

- [ ] Update CORS origins in main.py to your frontend domain (security)
- [ ] Implement password hashing (currently plain text - NOT SECURE!)
- [ ] Set up monitoring and alerts
- [ ] Configure custom domain (optional)
- [ ] Add SSL certificate (usually automatic with Digital Ocean)

## Troubleshooting

If build fails:
1. Check build logs in Digital Ocean dashboard
2. Verify all files are committed and pushed
3. Ensure database is properly attached
4. Review DEPLOYMENT.md for detailed troubleshooting

## Important Notes

⚠️ **Security Warning**: The current implementation stores passwords in plain text. This is NOT secure for production. Implement proper password hashing before going live!

✅ **Database**: Make sure to add a PostgreSQL database in Digital Ocean. The app is configured to use it automatically.

✅ **Environment Variables**: Digital Ocean will automatically set `DATABASE_URL` when you attach a database.

---

**Current Status**: ✅ All fixes applied - Ready to deploy!

**Next Action**: Commit and push changes to GitHub, then deploy in Digital Ocean.
