import os
from datetime import datetime
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS
from config import Config

class ReadingTracker:
    """
    Servicio REAL para gestionar el marcado de libros como leídos
    """
    
    def __init__(self):
        self.BS = Namespace("http://www.booksmart.org/ontology#")
        print("✅ ReadingTracker inicializado - LISTO PARA GUARDAR")
    
    def mark_book_as_read(self, user_uri, book_uri, book_title):
        """
        Marca un libro como leído por un usuario - EVITA DUPLICADOS
        """
        try:
            timestamp = datetime.now().isoformat()
            
            # Crear o cargar el grafo del usuario
            user_filename = user_uri.split('/')[-1] + '.ttl'
            user_filepath = os.path.join(Config.USER_READING_HISTORY_DIR, user_filename)
            
            user_graph = Graph()
            user_graph.bind("bs", self.BS)
            user_graph.bind("rdfs", RDFS)
            
            # Si el archivo existe, cargarlo
            if os.path.exists(user_filepath):
                user_graph.parse(user_filepath, format="turtle")
                print(f"📖 Cargando historial existente de: {user_filename}")
                
                # 🆕 VERIFICAR SI EL LIBRO YA EXISTE
                check_query = """
                PREFIX bs: <http://www.booksmart.org/ontology#>
                ASK WHERE {
                    ?user bs:hasRead ?book .
                    FILTER (?book = ?book_uri)
                }
                """
                book_exists = user_graph.query(check_query, initBindings={
                    'user': URIRef(user_uri),
                    'book_uri': URIRef(book_uri)
                })
                
                if book_exists.askAnswer:
                    print(f"⚠️  Libro ya existe en historial: {book_title}")
                    return False  # 🆕 No permitir duplicados
            
            # Agregar la lectura al grafo (solo si no existe)
            user_uri_ref = URIRef(user_uri)
            book_uri_ref = URIRef(book_uri)
            
            user_graph.add((user_uri_ref, self.BS.hasRead, book_uri_ref))
            user_graph.add((book_uri_ref, self.BS.readAt, Literal(timestamp)))
            user_graph.add((book_uri_ref, RDFS.label, Literal(book_title)))
            
            # Guardar el archivo
            user_graph.serialize(destination=user_filepath, format="turtle")
            
            print(f"✅ LIBRO GUARDADO: '{book_title}' en historial de {user_uri}")
            
            # 🆕 🧠 ACTIVAR AGENTE DE PERFIL DESPUÉS DE GUARDAR
            self._activate_profile_agent(user_uri)
            
            return True
            
        except Exception as e:
            print(f"❌ Error marcando libro como leído: {e}")
            return False
    
    def remove_book_from_history(self, user_uri, book_uri):
        """
        Elimina un libro del historial de lecturas
        """
        try:
            user_filename = user_uri.split('/')[-1] + '.ttl'
            user_filepath = os.path.join(Config.USER_READING_HISTORY_DIR, user_filename)
            
            if not os.path.exists(user_filepath):
                return False
                
            user_graph = Graph()
            user_graph.parse(user_filepath, format="turtle")
            
            # Eliminar tripletas relacionadas al libro
            user_uri_ref = URIRef(user_uri)
            book_uri_ref = URIRef(book_uri)
            
            user_graph.remove((user_uri_ref, self.BS.hasRead, book_uri_ref))
            user_graph.remove((book_uri_ref, self.BS.readAt, None))
            user_graph.remove((book_uri_ref, RDFS.label, None))
            
            # Guardar cambios
            user_graph.serialize(destination=user_filepath, format="turtle")
            
            print(f"🗑️  Libro eliminado del historial: {book_uri}")
            return True
            
        except Exception as e:
            print(f"❌ Error eliminando libro del historial: {e}")
            return False
    
    def get_user_reading_history(self, user_uri):
        """
        Obtiene el historial REAL de lecturas de un usuario
        """
        try:
            user_filename = user_uri.split('/')[-1] + '.ttl'
            user_filepath = os.path.join(Config.USER_READING_HISTORY_DIR, user_filename)
            
            if not os.path.exists(user_filepath):
                print(f"📭 No hay historial para: {user_uri}")
                return []
            
            user_graph = Graph()
            user_graph.parse(user_filepath, format="turtle")
            
            # Consultar libros leídos
            query = """
            PREFIX bs: <http://www.booksmart.org/ontology#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT ?book ?title ?readAt
            WHERE {
                ?user bs:hasRead ?book .
                ?book rdfs:label ?title ;
                      bs:readAt ?readAt .
            }
            ORDER BY DESC(?readAt)
            """
            
            results = user_graph.query(query, initBindings={'user': URIRef(user_uri)})
            
            readings = []
            for row in results:
                readings.append({
                    'book_uri': str(row.book),
                    'title': str(row.title),
                    'read_at': str(row.readAt)
                })
            
            print(f"📚 Historial encontrado: {len(readings)} libros para {user_uri}")
            return readings
            
        except Exception as e:
            print(f"❌ Error obteniendo historial de lecturas: {e}")
            return []
        
    # 🆕 🧠 MÉTODO NUEVO PARA ACTIVAR EL AGENTE
    def _activate_profile_agent(self, user_uri):
        """Activa el agente de perfil después de guardar un libro - MEJORADO"""
        try:
            # Pequeño delay para asegurar que el archivo se guardó
            import time
            time.sleep(1)  # Aumentado a 1 segundo
            
            from app.models.agents.user_profile_agent import user_profile_agent
            
            # Analizar perfil del usuario
            user_insights = user_profile_agent.analyze_user_profile(user_uri)
            
            if user_insights and user_insights["patrones_temporales"]["estado"] != "sin_historial":
                print(f"🧠 AGENTE ACTIVADO: Perfil actualizado para {user_uri}")
                print(f"   - Autor favorito: {user_insights['preferencias_autores']['autor_favorito']}")
                print(f"   - Velocidad: {user_insights['velocidad_lectura']['libros_mes']} libros/mes")
                print(f"   - Nivel: {user_insights['nivel_exploracion']}")
            else:
                print(f"🧠 AGENTE: Usuario {user_uri} sin historial suficiente")
                
        except ImportError as e:
            print(f"⚠️  Agente de perfil no disponible: {e}")
        except Exception as e:
            print(f"❌ Error activando agente de perfil: {e}")
            import traceback
            traceback.print_exc()

# Instancia global del servicio
reading_tracker = ReadingTracker()