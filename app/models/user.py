from rdflib import Graph, Namespace, Literal, URIRef
from werkzeug.security import generate_password_hash, check_password_hash
import os
from config import Config

class UserManager:
    """
    Gestiona usuarios usando RDF para BookSmart
    Crea:
    - users.ttl: Archivo maestro con credenciales
    - usuario.ttl: Archivo individual con perfil semántico
    """
    
    def __init__(self):
        self.users_file = Config.USERS_FILE
        self.users_graph = Graph()
        self.load_users()
    
    def load_users(self):
        """Carga los usuarios registrados desde el archivo RDF maestro"""
        if os.path.exists(self.users_file):
            print(f"📖 Cargando usuarios desde: {self.users_file}")
            self.users_graph.parse(self.users_file, format="turtle")
            
            # Bind namespaces
            self.users_graph.bind("bs", URIRef("http://www.booksmart.org/ontology/"))
            self.users_graph.bind("user", URIRef("http://www.booksmart.org/users/"))
        else:
            print(" Creando nuevo archivo de usuarios...")
            self.setup_base_ontology()
    
    def setup_base_ontology(self):
        """Configura los namespaces básicos para los usuarios"""
        # Bind namespaces
        self.users_graph.bind("bs", URIRef("http://www.booksmart.org/ontology/"))
        self.users_graph.bind("user", URIRef("http://www.booksmart.org/users/"))
        
        # Crear usuario demo
        self.create_demo_user()
        
        # Guardar archivo maestro
        self.users_graph.serialize(destination=self.users_file, format="turtle")
        print(f"✅ Archivo maestro de usuarios creado: {self.users_file}")
    
    def create_demo_user(self):
        """Crea un usuario de demostración para pruebas"""
        user_uri = URIRef("http://www.booksmart.org/users/demo")
        username_prop = URIRef("http://www.booksmart.org/ontology/username")
        password_prop = URIRef("http://www.booksmart.org/ontology/passwordHash")
        
        # Hash de "demo123"
        demo_hash = generate_password_hash("demo123")
        
        self.users_graph.add((user_uri, username_prop, Literal("demo")))
        self.users_graph.add((user_uri, password_prop, Literal(demo_hash)))
        
        # Crear archivo individual del usuario demo
        self.create_user_profile("demo")
        
        print("👤 Usuario demo creado: demo / demo123")
    
    def create_user_profile(self, username):
        """Crea un archivo RDF individual para el perfil del usuario"""
        profile_file = os.path.join(Config.USER_PROFILES_DIR, f"{username}.ttl")
        profile_graph = Graph()
        
        # Configurar namespaces
        profile_graph.bind("bs", URIRef("http://www.booksmart.org/ontology/"))
        profile_graph.bind("user", URIRef("http://www.booksmart.org/users/"))
        
        # Usuario básico
        user_uri = URIRef(f"http://www.booksmart.org/users/{username}")
        username_prop = URIRef("http://www.booksmart.org/ontology/username")
        
        profile_graph.add((user_uri, username_prop, Literal(username)))
        
        # Guardar perfil individual
        profile_graph.serialize(destination=profile_file, format="turtle")
        print(f"✅ Perfil individual creado: {profile_file}")
    
    def user_exists(self, username):
        """Verifica si un usuario ya existe en el sistema"""
        query = """
        PREFIX bs: <http://www.booksmart.org/ontology/>
        ASK {
            ?user bs:username "%s" .
        }
        """ % username
        return bool(self.users_graph.query(query))
    
    def register_user(self, username, password):
        """Registra un nuevo usuario en el sistema RDF"""
        if self.user_exists(username):
            return False, "El usuario ya existe"
        
        # Validaciones básicas
        if len(username) < 3:
            return False, "El usuario debe tener al menos 3 caracteres"
        
        if len(password) < 4:
            return False, "La contraseña debe tener al menos 4 caracteres"
        
        # Crear URIs
        user_uri = URIRef(f"http://www.booksmart.org/users/{username}")
        username_prop = URIRef("http://www.booksmart.org/ontology/username")
        password_prop = URIRef("http://www.booksmart.org/ontology/passwordHash")
        
        # Añadir usuario al grafo MAESTRO
        self.users_graph.add((user_uri, username_prop, Literal(username)))
        self.users_graph.add((user_uri, password_prop, Literal(generate_password_hash(password))))
        
        # Guardar cambios en archivo maestro
        self.users_graph.serialize(destination=self.users_file, format="turtle")
        
        # Crear archivo individual del usuario
        self.create_user_profile(username)
        
        print(f"✅ Nuevo usuario registrado: {username}")
        return True, "Usuario registrado exitosamente"
    
    def verify_user(self, username, password):
        """Verifica las credenciales de un usuario"""
        query = """
        PREFIX bs: <http://www.booksmart.org/ontology/>
        SELECT ?user ?pwdHash WHERE {
            ?user bs:username "%s" ;
                  bs:passwordHash ?pwdHash .
        }
        """ % username
        
        result = list(self.users_graph.query(query))
        if result and check_password_hash(str(result[0]['pwdHash']), password):
            user_uri = str(result[0]['user'])
            print(f"🔐 Login exitoso: {username}")
            return user_uri
        else:
            print(f"❌ Login fallido: {username}")
            return None