from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.user import UserManager

# Crear blueprint de autenticación
auth_bp = Blueprint('auth', __name__)
user_manager = UserManager()

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Maneja el registro de nuevos usuarios en BookSmart
    """
    # ✅ CORREGIDO: Si ya está logueado, redirigir a RECOMMENDATIONS
    if 'user_id' in session:
        return redirect(url_for('main.recommendations'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validaciones
        if not username or not password or not confirm_password:
            flash('❌ Por favor completa todos los campos', 'error')
            return render_template('register.html')
        
        if len(username) < 3:
            flash('❌ El usuario debe tener al menos 3 caracteres', 'error')
            return render_template('register.html')
        
        if len(password) < 4:
            flash('❌ La contraseña debe tener al menos 4 caracteres', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('❌ Las contraseñas no coinciden', 'error')
            return render_template('register.html')
        
        # Validar caracteres especiales en username
        if not username.replace('_', '').replace('-', '').isalnum():
            flash('❌ El usuario solo puede contener letras, números, guiones y guiones bajos', 'error')
            return render_template('register.html')
        
        # Registrar usuario
        success, message = user_manager.register_user(username, password)
        if success:
            flash('✅ ¡Cuenta creada exitosamente! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(f'❌ {message}', 'error')
    
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Maneja el login de usuarios en BookSmart
    """
    # ✅ CORREGIDO: Si ya está logueado, redirigir a RECOMMENDATIONS
    if 'user_id' in session:
        return redirect(url_for('main.recommendations'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('❌ Por favor ingresa usuario y contraseña', 'error')
            return render_template('login.html')
        
        # Verificar credenciales
        user_uri = user_manager.verify_user(username, password)
        if user_uri:
            session['user_id'] = user_uri
            session['username'] = username
            flash(f'🎉 ¡Bienvenido a BookSmart, {username}!', 'success')
            # ✅ CORREGIDO: Redirigir a RECOMMENDATIONS, no al index
            return redirect(url_for('main.recommendations'))
        else:
            flash('❌ Usuario o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Cierra la sesión del usuario"""
    session.clear()
    # ✅ CORREGIDO: Mantener redirección al index (home público)
    return redirect(url_for('main.index'))