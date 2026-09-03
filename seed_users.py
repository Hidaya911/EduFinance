import os
import sys

# Ensure project path is accessible
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edufinance.settings')

import django
django.setup()

from django.contrib.auth.models import User, Group

roles = [
    "Super Administrator",
    "School Administrator",
    "Accountant",
    "Cashier",
    "Auditor"
]

# Ensure groups exist
for r in roles:
    Group.objects.get_or_create(name=r)

# Excluded lina.khoury as she is already created in DB
mock_users = [
   
    {
        "username": "ziad.nassar",
        "email": "ziad.nassar@edufinance.edu",
        "first_name": "Ziad",
        "last_name": "Nassar",
        "password": "Password123!",
        "role": "Auditor",
        "is_superuser": False,
        "is_staff": False
    }
]

# Get the implicit M2M intermediate through model (auth_user_groups)
UserGroupThrough = User.groups.through

for data in mock_users:
    user = User.objects.filter(username=data["username"]).first()
    
    if not user:
        # Create user
        user = User.objects.create_user(
            username=data["username"],
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            is_staff=data["is_staff"],
            is_superuser=data["is_superuser"]
        )
        
        group = Group.objects.get(name=data["role"])
        
        # Manually create through instance to bypass M2M integer validation
        UserGroupThrough.objects.create(user=user, group=group)
        
        print(f"Created user: {user.username} ({data['role']})")
    else:
        print(f"Skipped existing user: {user.username}")

print("Seeding complete!")