from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or promote a user to admin"

    def add_arguments(self, parser):
        parser.add_argument("email", type=str)
        parser.add_argument("--password", type=str, default=None)
        parser.add_argument("--username", type=str, default="admin")

    def handle(self, *args, **options):
        User = get_user_model()
        email = options["email"].strip().lower()
        password = options["password"]
        username = options["username"]

        # Try to find by email first, then by username
        user = User.objects.filter(email=email).first() or User.objects.filter(username=username).first()

        if user:
            if password:
                user.set_password(password)
                self.stdout.write(f"🔑 Password updated for {user.email}")
            user.email = email
            user.is_staff = True
            user.is_superuser = True
            user.is_verified = True
            user.is_active = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f"✅ Promoted existing user '{user.email}' to admin!"))
        else:
            if not password:
                self.stdout.write(self.style.ERROR("❌ User not found. Provide --password to create one."))
                return
            user = User(email=email, username=username)
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.is_verified = True
            user.is_active = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f"✅ Created new admin user: {email}"))
