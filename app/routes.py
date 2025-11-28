from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from functools import wraps
from app.services.semantic_query import semantic_query_service
from app.services.reading_tracker import reading_tracker

main_bp = Blueprint('main', __name__)

def login_required(f):
    """
    Decorador para proteger rutas que requieren autenticación
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@main_bp.route('/')
def index():
    """Página de inicio - Acceso público"""
    return render_template('index.html', username=session.get('username'))

@main_bp.route('/profile')
@login_required
def profile():
    """Página de perfil del usuario con historial REAL e insights del agente - MEJORADO"""
    user_uri = session.get('user_id')
    reading_history = reading_tracker.get_user_reading_history(user_uri)
    
    # 🆕 OBTENER INSIGHTS DEL AGENTE CON MEJOR MANEJO DE ERRORES
    user_insights = None
    try:
        from app.models.agents.user_profile_agent import user_profile_agent
        user_insights = user_profile_agent.analyze_user_profile(user_uri)
        
        # 🆕 VERIFICAR ESTRUCTURA DEL DICCIONARIO
        if (user_insights and 
            'patrones_temporales' in user_insights and 
            'estado' in user_insights['patrones_temporales']):
            
            print(f"📊 Insights cargados correctamente para perfil")
            print(f"   - Estado: {user_insights['patrones_temporales']['estado']}")
            if user_insights['patrones_temporales']['estado'] != "sin_historial":
                print(f"   - Autor favorito: {user_insights['preferencias_autores']['autor_favorito']}")
        else:
            print("⚠️  Estructura de insights incorrecta, usando perfil vacío")
            user_insights = None
            
    except ImportError:
        print("⚠️  Agente de perfil no disponible en ruta /profile")
    except KeyError as e:
        print(f"❌ Error de clave en insights: {e}")
        user_insights = None
    except Exception as e:
        print(f"❌ Error cargando insights del agente: {e}")
        import traceback
        traceback.print_exc()
        user_insights = None
    
    return render_template('profile.html', 
                         username=session.get('username'),
                         reading_history=reading_history,
                         user_insights=user_insights)

@main_bp.route('/recommendations')
@login_required
def recommendations():
    """Página de recomendaciones personalizadas - Requiere autenticación"""
    return render_template('recommendations.html', username=session.get('username'))

@main_bp.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    """Búsqueda avanzada de libros con todos los filtros"""
    
    # Obtener opciones de filtros
    filter_options = semantic_query_service.get_filter_options()
    
    # Procesar búsqueda si hay parámetros
    books = []
    search_performed = False
    
    if request.method == 'GET' and any(param in request.args for param in [
        'query', 'genre', 'author', 'publisher', 'year', 'language', 
        'country', 'edition', 'literary_period', 'has_adaptation', 'adaptation_type'
    ]):
        search_performed = True
        
        # Recoger todos los parámetros de búsqueda
        search_params = {
            'query': request.args.get('query', '').strip(),
            'genre': request.args.get('genre', ''),
            'author': request.args.get('author', ''),
            'publisher': request.args.get('publisher', ''),
            'year': request.args.get('year', ''),
            'language': request.args.get('language', ''),
            'country': request.args.get('country', ''),
            'edition': request.args.get('edition', ''),
            'literary_period': request.args.get('literary_period', ''),
            'has_adaptation': request.args.get('has_adaptation', ''),
            'adaptation_type': request.args.get('adaptation_type', '')
        }
        
        # Realizar búsqueda
        books = semantic_query_service.search_books_advanced(search_params)
        
        # Mostrar mensaje si no hay resultados
        if not books and any(search_params.values()):
            flash('❌ No se encontraron libros con los criterios de búsqueda', 'info')
    
    return render_template('search.html', 
                         username=session.get('username'),
                         books=books,
                         filter_options=filter_options,
                         search_performed=search_performed,
                         current_params=request.args)

@main_bp.route('/mark-read', methods=['POST'])
@login_required
def mark_as_read():
    """Marca un libro como leído - IMPLEMENTACIÓN REAL"""
    book_uri = request.form.get('book_uri')
    book_title = request.form.get('book_title')
    user_uri = session.get('user_id')
    
    if book_uri and book_title and user_uri:
        success = reading_tracker.mark_book_as_read(user_uri, book_uri, book_title)
        if success:
            flash(f'✅ "{book_title}" agregado a tu historial de lecturas', 'success')
            
            # DEBUG: Verificar que se guardó
            history = reading_tracker.get_user_reading_history(user_uri)
            print(f"📊 Historial actualizado: {len(history)} libros")
            
        else:
            flash(f'⚠️ "{book_title}" ya está en tu historial', 'warning')
    else:
        flash('❌ Datos incompletos para marcar como leído', 'error')
    
    return redirect(request.referrer or url_for('main.search'))

@main_bp.route('/remove-from-history', methods=['POST'])
@login_required
def remove_from_history():
    """Elimina un libro del historial de lecturas"""
    book_uri = request.form.get('book_uri')
    book_title = request.form.get('book_title')
    user_uri = session.get('user_id')
    
    if book_uri and user_uri:
        success = reading_tracker.remove_book_from_history(user_uri, book_uri)
        if success:
            flash(f'🗑️ "{book_title}" eliminado de tu historial', 'info')
        else:
            flash(f'❌ Error al eliminar "{book_title}"', 'error')
    else:
        flash('❌ Datos incompletos para eliminar', 'error')
    
    return redirect(url_for('main.profile'))