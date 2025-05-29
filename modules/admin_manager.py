"""
Admin Manager Module
Handles admin controls, permissions, and system management
"""

import json
import time
from typing import Dict, List, Optional
from modules.google_sheets_manager import GoogleSheetsManager
from modules.game_logging import log_admin_action

# Define roles and their permissions
ADMIN_ROLES = {
    'superadmin': [
        'add_admin', 'remove_admin', 'set_permissions', 'ban', 'unban', 'grant', 'reset_player',
        'broadcast', 'maintenance', 'logs', 'stats', 'search_player', 'admin_help', 'all'
    ],
    'admin': [
        'ban', 'unban', 'grant', 'reset_player', 'broadcast', 'maintenance', 'logs', 'stats', 'search_player', 'admin_help'
    ],
    'moderator': [
        'ban', 'unban', 'grant', 'logs', 'stats', 'search_player', 'admin_help'
    ],
    'support': [
        'logs', 'stats', 'search_player', 'admin_help'
    ]
}

class AdminManager:
    def __init__(self):
        self.sheets = GoogleSheetsManager()
        self.admin_cache = {}  # Cache admin status to reduce sheet reads
        self.cache_timeout = 300  # 5 minutes cache timeout

    def is_admin(self, user_id: str, required_permission: Optional[str] = None) -> bool:
        """Check if a user is an admin, optionally with a required permission"""
        admin = self.get_admin_record(user_id)
        if not admin:
            return False
        if required_permission:
            role = admin.get('role', 'admin')
            permissions = ADMIN_ROLES.get(role, [])
            return required_permission in permissions or 'all' in permissions
        return True

    def get_admin_record(self, user_id: str) -> Optional[Dict]:
        # Check cache first
        if user_id in self.admin_cache:
            if time.time() - self.admin_cache[user_id]['timestamp'] < self.cache_timeout:
                return self.admin_cache[user_id]['record']
        # Check in Administrators sheet
        admins = self.sheets.get_worksheet('Administrators').get_all_records()
        for r in admins:
            if r['user_id'] == user_id:
                self.admin_cache[user_id] = {
                    'record': r,
                    'timestamp': time.time()
                }
                return r
        return None

    def add_admin(self, user_id: str, added_by: str, role: str = 'admin') -> Dict:
        """Add a new admin with a specific role (default: admin)"""
        if not self.is_admin(added_by, 'add_admin'):
            return {'success': False, 'message': 'Only superadmins can add other admins'}
        if self.is_admin(user_id):
            return {'success': False, 'message': 'User is already an admin'}
        if role not in ADMIN_ROLES:
            return {'success': False, 'message': f'Invalid role: {role}'}
        # Add to Administrators sheet
        self.sheets.append_row('Administrators', {
            'user_id': user_id,
            'added_by': added_by,
            'added_at': time.time(),
            'role': role,
            'permissions': json.dumps(ADMIN_ROLES[role])
        })
        # Clear cache
        self.admin_cache.pop(user_id, None)
        # Log action
        log_admin_action(added_by, 'add_admin', {'target_user': user_id, 'role': role})
        return {'success': True}

    def remove_admin(self, user_id: str, removed_by: str) -> Dict:
        """Remove an admin"""
        if not self.is_admin(removed_by, 'remove_admin'):
            return {'success': False, 'message': 'Only superadmins can remove other admins'}
        if not self.is_admin(user_id):
            return {'success': False, 'message': 'User is not an admin'}
        # Remove from Administrators sheet
        admins = self.sheets.get_worksheet('Administrators').get_all_records()
        for i, admin in enumerate(admins):
            if admin['user_id'] == user_id:
                self.sheets.delete_row('Administrators', i + 2)  # +2 for header and 0-index
                break
        # Clear cache
        self.admin_cache.pop(user_id, None)
        # Log action
        log_admin_action(removed_by, 'remove_admin', {'target_user': user_id})
        return {'success': True}

    def get_admin_permissions(self, user_id: str) -> List[str]:
        """Get admin permissions"""
        admin = self.get_admin_record(user_id)
        if not admin:
            return []
        return json.loads(admin.get('permissions', '[]'))

    def set_admin_role(self, user_id: str, role: str, set_by: str) -> Dict:
        """Set admin role and permissions"""
        if not self.is_admin(set_by, 'set_permissions'):
            return {'success': False, 'message': 'Only superadmins can set roles/permissions'}
        if not self.is_admin(user_id):
            return {'success': False, 'message': 'User is not an admin'}
        if role not in ADMIN_ROLES:
            return {'success': False, 'message': f'Invalid role: {role}'}
        # Update role and permissions in Administrators sheet
        admins = self.sheets.get_worksheet('Administrators').get_all_records()
        for i, admin in enumerate(admins):
            if admin['user_id'] == user_id:
                admin['role'] = role
                admin['permissions'] = json.dumps(ADMIN_ROLES[role])
                self.sheets.update_row('Administrators', i + 2, admin)
                break
        # Clear cache
        self.admin_cache.pop(user_id, None)
        # Log action
        log_admin_action(set_by, 'set_permissions', {
            'target_user': user_id,
            'role': role,
            'permissions': ADMIN_ROLES[role]
        })
        return {'success': True}

    def get_all_admins(self) -> List[Dict]:
        """Get list of all admins"""
        admins = self.sheets.get_worksheet('Administrators').get_all_records()
        return admins

    def clear_admin_cache(self):
        """Clear the admin cache"""
        self.admin_cache.clear() 