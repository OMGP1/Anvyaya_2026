"""Named local accounts. Password material never enters API responses or audit payloads."""
import hashlib
import hmac
import re
import secrets

ITERATIONS = 600_000


def password_hash(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITERATIONS)
    return f'pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}'


def password_matches(password, encoded):
    if not isinstance(password, str) or len(password) > 128:
        return False
    try:
        algorithm, iterations, salt, expected = encoded.split('$')
        if algorithm != 'pbkdf2_sha256':
            return False
        actual = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(iterations))
        return hmac.compare_digest(actual.hex(), expected)
    except (ValueError, TypeError):
        return False


def public(user):
    return {k: v for k, v in user.items() if k != 'password_hash'}


def principal(core, user):
    return {**core.ROLES[user['role']], 'role': user['role'], 'user_id': user['id'],
            'username': user['username'], 'name': user['name'], 'scope': user['scope'],
            'must_change_password': user.get('must_change_password', False), 'demo': False}


def find(core, conn, username):
    if not isinstance(username, str):
        return None
    return next((u for u in core.rows(conn, 'users') if u['username'] == username.strip().lower()), None)


def validate_password(core, data):
    password = data.get('password')
    if not isinstance(password, str) or not 12 <= len(password) <= 128 or password.isspace():
        raise core.ApiError(400, 'Use a password of 12 to 128 characters.')
    return password


def assignments(core, conn, data, role):
    scope = data.get('scope')
    if role == 'admin' and scope is None:
        return None
    if not isinstance(scope, list) or not all(isinstance(s, str) for s in scope):
        raise core.ApiError(400, 'Provide study assignments as a list; only administrators can have institution-wide access.')
    valid = {s['id'] for s in core.rows(conn, 'studies')}
    if len(scope) != len(set(scope)) or not set(scope) <= valid:
        raise core.ApiError(400, 'Study assignments contain duplicates or unknown studies.')
    if role == 'admin':
        raise core.ApiError(400, 'Administrators use institution-wide scope.')
    return scope


def create(core, conn, data, actor):
    username = core.text_field(data, 'username', 80).lower()
    if not re.fullmatch(r'[a-z0-9][a-z0-9._@+-]{2,79}', username):
        raise core.ApiError(400, 'Username must have 3–80 letters, digits or . _ @ + - characters.')
    if find(core, conn, username):
        raise core.ApiError(409, 'That username is already in use.')
    role = core.choice(data, 'role', list(core.ROLES))
    user = {'id': 'USR-' + secrets.token_hex(6).upper(), 'username': username,
            'name': core.text_field(data, 'name', 120), 'role': role,
            'scope': assignments(core, conn, data, role), 'active': True,
            'password_hash': password_hash(validate_password(core, data)), 'auth_version': 1,
            'must_change_password': True, 'revision': 1, 'created_at': core.stamp()}
    core.save(conn, 'users', user)
    core.audit(conn, actor, 'ACCOUNT_CREATED', user['id'], after=public(user), reason='Named account provisioned; password change required at first sign-in')
    return public(user)


def mutate(core, conn, actor, path, data):
    if path == '/api/users':
        core.authorized(actor, 'users')
        return {'record': create(core, conn, data, actor)}
    match = re.fullmatch(r'/api/users/(USR-[A-F0-9]+)/(access|reset|revoke)', path)
    if not match:
        return None
    core.authorized(actor, 'users')
    user = core.get(conn, 'users', match[1])
    if core.number(data, 'revision', 1, 1_000_000) != user['revision']:
        raise core.ApiError(409, 'Account changed. Refresh and review the latest version.')
    reason = core.text_field(data, 'reason', 500)
    before = public(user)
    action = match[2]
    if action == 'access':
        role = core.choice(data, 'role', list(core.ROLES))
        active = data.get('active')
        if not isinstance(active, bool):
            raise core.ApiError(400, 'Account active state must be true or false.')
        if core.actor_id(actor) == user['id'] and (not active or role != 'admin'):
            raise core.ApiError(409, 'Use a different administrator to change your own administrative access.')
        if user['active'] and user['role'] == 'admin' and (not active or role != 'admin'):
            others = [u for u in core.rows(conn, 'users') if u['id'] != user['id'] and u['active'] and u['role'] == 'admin']
            if not others:
                raise core.ApiError(409, 'Keep at least one active named administrator.')
        user.update(role=role, active=active, scope=assignments(core, conn, data, role))
    elif action == 'reset':
        user.update(password_hash=password_hash(validate_password(core, data)), must_change_password=True)
    user.update(auth_version=user['auth_version'] + 1, revision=user['revision'] + 1, updated_at=core.stamp())
    core.save(conn, 'users', user)
    core.audit(conn, actor, 'ACCOUNT_' + action.upper(), user['id'], before=before, after=public(user), reason=reason)
    return {'record': public(user)}
