#!/bin/bash

echo "🚀 Setting up Event Booking API..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10+ first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip first."
    exit 1
fi

# Check if virtualenv is installed
if ! command -v virtualenv &> /dev/null; then
    echo "📦 Installing virtualenv..."
    pip3 install virtualenv
fi

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env_template.txt .env
    echo "⚠️  Please update .env file with your actual configuration values!"
    echo "   - Database credentials"
    echo "   - API keys"
    echo "   - Email settings"
fi

# Check if PostgreSQL is running
echo "🔍 Checking PostgreSQL connection..."
if command -v psql &> /dev/null; then
    if pg_isready -h localhost -p 5432 &> /dev/null; then
        echo "✅ PostgreSQL is running"
    else
        echo "⚠️  PostgreSQL is not running. Please start PostgreSQL service."
        echo "   You can use Docker: docker-compose up -d db"
    fi
else
    echo "⚠️  PostgreSQL client not found. Please install PostgreSQL client."
fi

# Check if Redis is running
echo "🔍 Checking Redis connection..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis is running"
    else
        echo "⚠️  Redis is not running. Please start Redis service."
        echo "   You can use Docker: docker-compose up -d redis"
    fi
else
    echo "⚠️  Redis client not found. Please install Redis client."
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Update .env file with your configuration"
echo "2. Start PostgreSQL and Redis services"
echo "3. Run migrations: python manage.py migrate"
echo "4. Create superuser: python manage.py createsuperuser"
echo "5. Populate sample data: python manage.py populate_sample_data"
echo "6. Start the server: python manage.py runserver"
echo ""
echo "🐳 Or use Docker: docker-compose up"
echo ""
echo "📚 API documentation will be available at: http://localhost:8000/api/docs/"
