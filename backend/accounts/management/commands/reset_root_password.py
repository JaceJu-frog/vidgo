from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from accounts.models import User
from accounts.views import validate_password
import getpass


class Command(BaseCommand):
    help = 'Reset root user password'

    def handle(self, *args, **options):
        try:
            # Find root user
            root_user = User.objects.filter(is_root=True).first()
            
            if not root_user:
                self.stdout.write(
                    self.style.ERROR('No root user found. Create one first with register_root endpoint.')
                )
                return
            
            self.stdout.write(f'Found root user: {root_user.username}')
            
            # Get new password
            while True:
                password = getpass.getpass('Enter new password for root user: ')
                password_confirm = getpass.getpass('Confirm password: ')
                
                if password != password_confirm:
                    self.stdout.write(self.style.ERROR('Passwords do not match. Please try again.'))
                    continue
                
                # Validate password requirements
                is_valid, message = validate_password(password)
                if not is_valid:
                    self.stdout.write(self.style.ERROR(f'Invalid password: {message}'))
                    continue
                
                break
            
            # Update password
            root_user.password = make_password(password)
            root_user.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully reset password for root user: {root_user.username}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error resetting root password: {str(e)}')
            )