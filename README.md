# 🤖 Advanced Math Course Registration Bot - 2025 Edition

A professional Telegram bot for educational course registration, built with modern Python and comprehensive features for 2025.

## 🚀 Features

### Core Functionality
- **Complete Registration System** - Multi-step registration with comprehensive data collection
- **User Data Management** - Secure storage and constant updates
- **Admin Panel** - Full administrative control with user management
- **Course Management** - Free and paid course registration
- **Payment Processing** - Manual payment confirmation system
- **Data Export** - Comprehensive user data export functionality

### Advanced Features
- **Multi-language Support** - Persian and English
- **Smart Reply Suggestions** - Context-aware responses
- **Gamification System** - Points, badges, and achievements
- **Professional UI/UX** - Rich interactive menus and adaptive interfaces
- **Scalable Architecture** - Redis caching, PostgreSQL support, message queues
- **Security Features** - Data encryption, secure storage, admin authentication

## 📋 Requirements

- Python 3.8+
- Telegram Bot Token
- Redis (optional, for caching)
- PostgreSQL (optional, for database)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Tawtami/Telegram-Bot.git
   cd Telegram-Bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env_template.txt .env
   # Edit .env with your bot token and other settings
   ```

4. **Run the bot**
   ```bash
   python hosted_bot.py
   ```

## 🔧 Configuration

Edit `config.py` to customize:
- Bot settings and features
- Course information
- Admin user IDs
- Database connections
- Security settings

## 📊 User Data System

The bot includes a comprehensive user data management system:

- **Data Collection**: Name, phone, grade, field, parent phone
- **Secure Storage**: JSON files with encryption
- **Admin Access**: View and export user data
- **Constant Updates**: Automatic data synchronization
- **Backup System**: Automatic backup creation

### Admin Commands
- `/admin` - Access admin panel
- `/export` - Export user data
- `/stats` - View bot statistics

## 🚀 Deployment

### Railway Deployment
1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically

### Manual Deployment
1. Upload files to your server
2. Install dependencies
3. Set environment variables
4. Run with `python hosted_bot.py`

## 📁 Project Structure

```
├── hosted_bot.py              # Main bot application
├── config.py                  # Configuration settings
├── requirements.txt           # Python dependencies
├── Procfile                  # Railway deployment
├── runtime.txt               # Python version
├── .gitignore               # Git ignore rules
├── data/                    # User data storage
│   ├── students.json        # User data
│   └── students_backup.json # Backup data
├── logs/                    # Log files
└── docs/                    # Documentation
    ├── FINAL_SUMMARY_2025.md
    ├── USER_DATA_SYSTEM_SUMMARY.md
    ├── RAILWAY_SETUP.md
    ├── HOSTING_GUIDE.md
    ├── GITHUB_COMMANDS.md
    └── SECURITY_GUIDE.md
```

## 🔒 Security

- Environment variables for sensitive data
- Data encryption for phone numbers
- Admin authentication
- Secure file handling
- Input validation

## 📈 Analytics & Monitoring

- User registration tracking
- Course enrollment statistics
- Payment processing logs
- Error monitoring and logging
- Performance metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Check the documentation in the `docs/` folder
- Review the configuration in `config.py`
- Check logs in the `logs/` directory

## 🎯 Roadmap

- [ ] Voice message support
- [ ] Advanced analytics dashboard
- [ ] Multi-currency payment support
- [ ] Integration with learning management systems
- [ ] Mobile app companion
- [ ] Advanced AI features (when requested)

---

**Built with ❤️ for educational excellence in 2025** 