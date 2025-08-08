#!/usr/bin/env python
import asyncio
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User

async def create_admin():
    db = SessionLocal()
    admin = User(
        email="admin@hypothesisai.com",
        hashed_password=get_password_hash("admin123"),
        full_name="Admin User",
        is_active=True,
        is_superuser=True,
        role="admin"
    )
    db.add(admin)
    db.commit()
    print("Admin user created successfully!")
    print("Email: admin@hypothesisai.com")
    print("Password: admin123")
    db.close()

if __name__ == "__main__":
    asyncio.run(create_admin())
