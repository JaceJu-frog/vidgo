from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import re
from .models import User


@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    """User registration endpoint"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        email = data.get('email', '')
        premium_authority = data.get('premium_authority', False)
        
        if not username or not password:
            return JsonResponse({'error': 'Username and password are required'}, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
        
        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            premium_authority=premium_authority,
            hidden_categories=[]
        )
        
        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'premium_authority': user.premium_authority,
                'hidden_categories': user.hidden_categories
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def check_root_exists(request):
    """Check if root user exists"""
    root_exists = User.objects.filter(is_root=True).exists()
    return JsonResponse({
        'root_exists': root_exists,
        'message': 'Use command: python manage.py reset_root_password' if root_exists else 'Root user needs to be created'
    })


def validate_password(password):
    """Validate password requirements: numbers, lowercase, uppercase"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    return True, "Valid password"


@csrf_exempt
@require_http_methods(["POST"])
def register_root(request):
    """Register root user - only works if no root exists"""
    try:
        if User.objects.filter(is_root=True).exists():
            return JsonResponse({'error': 'Root user already exists'}, status=400)
        
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        email = data.get('email', '')
        
        if not username or not password:
            return JsonResponse({'error': 'Username and password are required'}, status=400)
        
        # Validate password requirements
        is_valid, message = validate_password(password)
        if not is_valid:
            return JsonResponse({'error': message}, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
        
        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            is_root=True,
            premium_authority=True,
            is_staff=True,
            is_superuser=True,
            hidden_categories=[]
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Root user created successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_root': user.is_root,
                'premium_authority': user.premium_authority
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_user(request):
    """Create normal user - only for root users"""
    if not request.user.is_authenticated or not request.user.is_root:
        return JsonResponse({'error': 'Only root users can create users'}, status=403)
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        email = data.get('email', '')
        premium_authority = data.get('premium_authority', False)
        hidden_categories = data.get('hidden_categories', [])
        
        if not username or not password:
            return JsonResponse({'error': 'Username and password are required'}, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
        
        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            premium_authority=premium_authority,
            hidden_categories=hidden_categories,
            is_root=False
        )
        
        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'premium_authority': user.premium_authority,
                'hidden_categories': user.hidden_categories
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def list_users(request):
    """List all users - only for root users"""
    if not request.user.is_authenticated or not request.user.is_root:
        return JsonResponse({'error': 'Only root users can list users'}, status=403)
    
    users = User.objects.all().values(
        'id', 'username', 'email', 'premium_authority', 
        'hidden_categories', 'is_root', 'is_active', 'created_at'
    )
    
    return JsonResponse({
        'success': True,
        'users': list(users)
    })


@csrf_exempt
@require_http_methods(["POST"])
def update_user(request, user_id):
    """Update user - only for root users"""
    if not request.user.is_authenticated or not request.user.is_root:
        return JsonResponse({'error': 'Only root users can update users'}, status=403)
    
    try:
        user = User.objects.get(id=user_id)
        data = json.loads(request.body)
        
        # Don't allow modifying root status
        if 'premium_authority' in data:
            user.premium_authority = data['premium_authority']
        
        if 'hidden_categories' in data:
            user.hidden_categories = data['hidden_categories']
        
        if 'email' in data:
            user.email = data['email']
        
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        user.save()
        
        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'premium_authority': user.premium_authority,
                'hidden_categories': user.hidden_categories,
                'is_active': user.is_active
            }
        })
        
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def user_login(request):
    """User login endpoint"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({'error': 'Username and password are required'}, status=400)
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return JsonResponse({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'premium_authority': user.premium_authority,
                    'hidden_categories': user.hidden_categories,
                    'is_root': user.is_root,
                    'is_active': user.is_active
                }
            })
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def check_root_exists(request):
    """Check if root user exists"""
    root_exists = User.objects.filter(is_root=True).exists()
    return JsonResponse({
        'root_exists': root_exists,
        'message': 'Use command: python manage.py reset_root_password' if root_exists else 'Root user needs to be created'
    })


def validate_password(password):
    """Validate password requirements: numbers, lowercase, uppercase"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    return True, "Valid password"


@csrf_exempt
@require_http_methods(["POST"])
def register_root(request):
    """Register root user - only works if no root exists"""
    try:
        if User.objects.filter(is_root=True).exists():
            return JsonResponse({'error': 'Root user already exists'}, status=400)
        
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        email = data.get('email', '')
        
        if not username or not password:
            return JsonResponse({'error': 'Username and password are required'}, status=400)
        
        # Validate password requirements
        is_valid, message = validate_password(password)
        if not is_valid:
            return JsonResponse({'error': message}, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
        
        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            is_root=True,
            premium_authority=True,
            is_staff=True,
            is_superuser=True,
            hidden_categories=[]
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Root user created successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_root': user.is_root,
                'premium_authority': user.premium_authority
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_user(request):
    """Create normal user - only for root users"""
    if not request.user.is_authenticated or not request.user.is_root:
        return JsonResponse({'error': 'Only root users can create users'}, status=403)
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        email = data.get('email', '')
        premium_authority = data.get('premium_authority', False)
        hidden_categories = data.get('hidden_categories', [])
        
        if not username or not password:
            return JsonResponse({'error': 'Username and password are required'}, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
        
        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            premium_authority=premium_authority,
            hidden_categories=hidden_categories,
            is_root=False
        )
        
        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'premium_authority': user.premium_authority,
                'hidden_categories': user.hidden_categories
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def list_users(request):
    """List all users - only for root users"""
    if not request.user.is_authenticated or not request.user.is_root:
        return JsonResponse({'error': 'Only root users can list users'}, status=403)
    
    users = User.objects.all().values(
        'id', 'username', 'email', 'premium_authority', 
        'hidden_categories', 'is_root', 'is_active', 'created_at'
    )
    
    return JsonResponse({
        'success': True,
        'users': list(users)
    })


@csrf_exempt
@require_http_methods(["POST"])
def update_user(request, user_id):
    """Update user - only for root users"""
    if not request.user.is_authenticated or not request.user.is_root:
        return JsonResponse({'error': 'Only root users can update users'}, status=403)
    
    try:
        user = User.objects.get(id=user_id)
        data = json.loads(request.body)
        
        # Don't allow modifying root status
        if 'premium_authority' in data:
            user.premium_authority = data['premium_authority']
        
        if 'hidden_categories' in data:
            user.hidden_categories = data['hidden_categories']
        
        if 'email' in data:
            user.email = data['email']
        
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        user.save()
        
        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'premium_authority': user.premium_authority,
                'hidden_categories': user.hidden_categories,
                'is_active': user.is_active
            }
        })
        
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def user_logout(request):
    """User logout endpoint"""
    logout(request)
    return JsonResponse({'success': True, 'message': 'Logged out successfully'})


@require_http_methods(["GET"])
def user_profile(request):
    """Get current user profile"""
    if request.user.is_authenticated:
        return JsonResponse({
            'success': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'premium_authority': request.user.premium_authority,
                'hidden_categories': request.user.hidden_categories,
                'is_root': request.user.is_root,
                'is_active': request.user.is_active
            }
        })
    else:
        return JsonResponse({'error': 'Not authenticated'}, status=401)


@csrf_exempt
@require_http_methods(["POST"])
def update_hidden_categories(request):
    """Update user's hidden categories"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    try:
        data = json.loads(request.body)
        action = data.get('action')  # 'hide' or 'unhide'
        category_id = data.get('category_id')
        
        if not action or category_id is None:
            return JsonResponse({'error': 'Action and category_id are required'}, status=400)
        
        if action == 'hide':
            request.user.hide_category(category_id)
        elif action == 'unhide':
            request.user.unhide_category(category_id)
        else:
            return JsonResponse({'error': 'Invalid action. Use "hide" or "unhide"'}, status=400)
        
        return JsonResponse({
            'success': True,
            'hidden_categories': request.user.hidden_categories
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def check_root_exists(request):
    """Check if root user exists"""
    root_exists = User.objects.filter(is_root=True).exists()
    return JsonResponse({
        'root_exists': root_exists,
        'message': 'Use command: python manage.py reset_root_password' if root_exists else 'Root user needs to be created'
    })


def validate_password(password):
    """Validate password requirements: numbers, lowercase, uppercase"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    return True, "Valid password"


@csrf_exempt
@require_http_methods(["POST"])
def register_root(request):
    """Register root user - only works if no root exists"""
    try:
        if User.objects.filter(is_root=True).exists():
            return JsonResponse({'error': 'Root user already exists'}, status=400)
        
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        email = data.get('email', '')
        
        if not username or not password:
            return JsonResponse({'error': 'Username and password are required'}, status=400)
        
        # Validate password requirements
        is_valid, message = validate_password(password)
        if not is_valid:
            return JsonResponse({'error': message}, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
        
        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            is_root=True,
            premium_authority=True,
            is_staff=True,
            is_superuser=True,
            hidden_categories=[]
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Root user created successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_root': user.is_root,
                'premium_authority': user.premium_authority
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_user(request):
    """Create normal user - only for root users"""
    if not request.user.is_authenticated or not request.user.is_root:
        return JsonResponse({'error': 'Only root users can create users'}, status=403)
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        email = data.get('email', '')
        premium_authority = data.get('premium_authority', False)
        hidden_categories = data.get('hidden_categories', [])
        
        if not username or not password:
            return JsonResponse({'error': 'Username and password are required'}, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)
        
        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            premium_authority=premium_authority,
            hidden_categories=hidden_categories,
            is_root=False
        )
        
        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'premium_authority': user.premium_authority,
                'hidden_categories': user.hidden_categories
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def list_users(request):
    """List all users - only for root users"""
    if not request.user.is_authenticated or not request.user.is_root:
        return JsonResponse({'error': 'Only root users can list users'}, status=403)
    
    users = User.objects.all().values(
        'id', 'username', 'email', 'premium_authority', 
        'hidden_categories', 'is_root', 'is_active', 'created_at'
    )
    
    return JsonResponse({
        'success': True,
        'users': list(users)
    })


@csrf_exempt
@require_http_methods(["POST"])
def update_user(request, user_id):
    """Update user - only for root users"""
    if not request.user.is_authenticated or not request.user.is_root:
        return JsonResponse({'error': 'Only root users can update users'}, status=403)
    
    try:
        user = User.objects.get(id=user_id)
        data = json.loads(request.body)
        
        # Don't allow modifying root status
        if 'premium_authority' in data:
            user.premium_authority = data['premium_authority']
        
        if 'hidden_categories' in data:
            user.hidden_categories = data['hidden_categories']
        
        if 'email' in data:
            user.email = data['email']
        
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        user.save()
        
        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'premium_authority': user.premium_authority,
                'hidden_categories': user.hidden_categories,
                'is_active': user.is_active
            }
        })
        
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def user_defined_hidden_categories(request):
    """API endpoint for managing user-defined hidden categories"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    if request.method == 'GET':
        """Get user's hidden categories settings"""
        try:
            user = request.user
            return JsonResponse({
                'success': True,
                'hidden_categories': user.hidden_categories,
                'usr_def_hidden_categories': user.usr_def_hidden_categories,
                'combined_hidden_categories': user.get_combined_hidden_categories()
            }, status=200)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    elif request.method == 'POST':
        """Update user's defined hidden categories"""
        try:
            data = json.loads(request.body)
            user = request.user
            
            # Get the hidden categories list from request
            usr_def_hidden_categories = data.get('usr_def_hidden_categories', [])
            
            # Validate that it's a list of integers
            if not isinstance(usr_def_hidden_categories, list):
                return JsonResponse({
                    'success': False,
                    'error': 'usr_def_hidden_categories must be a list'
                }, status=400)
            
            # Validate all items are integers
            try:
                usr_def_hidden_categories = [int(cat_id) for cat_id in usr_def_hidden_categories]
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': 'All category IDs must be integers'
                }, status=400)
            
            # Update user's hidden categories
            user.usr_def_hidden_categories = usr_def_hidden_categories
            user.save(update_fields=['usr_def_hidden_categories'])
            
            return JsonResponse({
                'success': True,
                'message': 'User hidden categories updated successfully',
                'usr_def_hidden_categories': user.usr_def_hidden_categories,
                'combined_hidden_categories': user.get_combined_hidden_categories()
            }, status=200)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
