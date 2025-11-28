from app import create_app
from config import Config

def main():
    """
    Función principal que inicia la aplicación BookSmart
    """
    # Asegurar que los directorios existan
    Config.ensure_directories_exist()
    
    # Crear aplicación Flask
    app = create_app()
    
    print("🚀 INICIANDO BOOKSMART - SISTEMA INTELIGENTE")
    print("📍 Inicio: http://localhost:5000/")
    print("📍 Búsqueda: http://localhost:5000/search") 
    print("📍 Recomendaciones: http://localhost:5000/recommendations")
    print("📍 Perfil: http://localhost:5000/profile")
    print("📍 Register: http://localhost:5000/auth/register")
    print("📍 Login: http://localhost:5000/auth/login") 
    
    # Ejecutar aplicación
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()