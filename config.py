import os

class Config:
    """
    Configuración principal de BookSmart
    """
    
    # Directorio base
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Archivos de ontología
    ONTOLOGY_DIR = os.path.join(BASE_DIR, 'data/ontology')
    ONTOLOGY_FILE = os.path.join(ONTOLOGY_DIR, 'booksmart_ontology.ttl')
    LITERARY_DATA_FILE = os.path.join(ONTOLOGY_DIR, 'literary_data.ttl')
    
    # Archivos de usuarios
    USER_PROFILES_DIR = os.path.join(BASE_DIR, 'data/user_profiles')
    USERS_FILE = os.path.join(USER_PROFILES_DIR, 'users.ttl')
    
    # 🆕 NUEVOS DIRECTORIOS
    USER_READING_HISTORY_DIR = os.path.join(USER_PROFILES_DIR, 'user_reading_history')
    USER_PREFERENCES_DIR = os.path.join(USER_PROFILES_DIR, 'user_preferences')
    CACHE_DIR = os.path.join(BASE_DIR, 'data/cache')
    
    # Configuración de Flask
    SECRET_KEY = 'booksmart-dev-key-2024'
    
    @classmethod
    def ensure_directories_exist(cls):
        """Asegura que todos los directorios necesarios existan"""
        os.makedirs(cls.ONTOLOGY_DIR, exist_ok=True)
        os.makedirs(cls.USER_PROFILES_DIR, exist_ok=True)
        # 🆕 CREAR NUEVOS DIRECTORIOS
        os.makedirs(cls.USER_READING_HISTORY_DIR, exist_ok=True)
        os.makedirs(cls.USER_PREFERENCES_DIR, exist_ok=True)
        os.makedirs(cls.CACHE_DIR, exist_ok=True)