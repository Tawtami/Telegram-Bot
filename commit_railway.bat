@echo off
echo Adding Railway configuration files...
git add Procfile runtime.txt start.py railway.json
echo Committing Railway configuration...
git commit -m "🔧 FIX RAILWAY DEPLOYMENT - Added Railway configuration files

📁 Added files:
• Procfile - Specifies how to run the bot
• runtime.txt - Python version specification
• start.py - Railway startup script with error handling
• railway.json - Railway deployment configuration

🚀 This should fix the deployment failures on Railway"
echo Pushing to GitHub...
git push origin main
echo Done!
pause 