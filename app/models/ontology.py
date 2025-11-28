from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef
from rdflib.plugins.stores.sparqlstore import SPARQLStore
import os
from config import Config

class OntologyManager:
    """
    Gestor de la ontología BookSmart - Conecta agentes con datos semánticos
    """
    
    def __init__(self):
        self.graph = Graph()
        self.BS = Namespace("http://www.booksmart.org/ontology#")
        self.RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
        self.OWL = Namespace("http://www.w3.org/2002/07/owl#")
        
        # Bind namespaces
        self.graph.bind("bs", self.BS)
        self.graph.bind("rdfs", self.RDFS)
        self.graph.bind("owl", self.OWL)
        
        self.load_ontology()
        print("✅ OntologyManager inicializado - Listo para razonamiento semántico")
    
    def load_ontology(self):
        """Carga la ontología OWL y los datos literarios"""
        try:
            # 1. Cargar ontología OWL (esquema)
            if os.path.exists(Config.ONTOLOGY_FILE):
                self.graph.parse(Config.ONTOLOGY_FILE, format="turtle")
                print("✅ Ontología OWL cargada correctamente")
            
            # 2. Cargar datos literarios (instancias)
            if os.path.exists(Config.LITERARY_DATA_FILE):
                self.graph.parse(Config.LITERARY_DATA_FILE, format="turtle")
                book_count = len(list(self.graph.subjects(RDF.type, self.BS.Book)))
                print(f"✅ Datos literarios cargados: {book_count} libros")
                
        except Exception as e:
            print(f"❌ Error cargando ontología: {e}")
            import traceback
            traceback.print_exc()
    
    def find_similar_books(self, book_uri, max_results=5):
        """
        Encuentra libros similares basado en la ontología
        Usa relaciones semánticas: mismo autor, mismo género, temas comunes
        """
        try:
            query = """
            PREFIX bs: <http://www.booksmart.org/ontology#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT DISTINCT ?similarBook ?title ?authorName ?genre ?similarityReason
            WHERE {
                # Libro original
                <%s> bs:hasAuthor ?originalAuthor ;
                     bs:hasGenre ?originalGenre .
                
                # Libros similares (excluyendo el original)
                ?similarBook a bs:Book ;
                            rdfs:label ?title ;
                            bs:hasAuthor ?author ;
                            bs:hasGenre ?genre .
                
                ?author rdfs:label ?authorName .
                
                FILTER (?similarBook != <%s>)
                
                # Criterios de similitud
                {
                    # Mismo autor
                    ?similarBook bs:hasAuthor ?originalAuthor .
                    BIND("Mismo autor" AS ?similarityReason)
                } UNION {
                    # Mismo género  
                    ?similarBook bs:hasGenre ?originalGenre .
                    BIND("Mismo género" AS ?similarityReason)
                } UNION {
                    # Mismo movimiento literario
                    ?originalAuthor bs:literaryMovement ?movement .
                    ?author bs:literaryMovement ?movement .
                    BIND("Mismo movimiento literario" AS ?similarityReason)
                }
            }
            ORDER BY ?title
            LIMIT %d
            """ % (book_uri, book_uri, max_results)
            
            results = self.graph.query(query)
            similar_books = []
            
            for row in results:
                similar_books.append({
                    'uri': str(row.similarBook),
                    'title': str(row.title),
                    'author': str(row.authorName),
                    'genre': str(row.genre),
                    'similarity_reason': str(row.similarityReason)
                })
            
            print(f"🔍 Encontrados {len(similar_books)} libros similares para {book_uri}")
            return similar_books
            
        except Exception as e:
            print(f"❌ Error buscando libros similares: {e}")
            return []
    
    def get_author_recommendations(self, author_uri, user_uri, max_results=3):
        """
        Recomienda autores similares basado en la ontología
        """
        try:
            query = """
            PREFIX bs: <http://www.booksmart.org/ontology#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT DISTINCT ?similarAuthor ?authorName ?reason
            WHERE {
                # Autor original
                <%s> bs:literaryMovement ?movement ;
                     bs:countryOfOrigin ?country .
                
                # Autores similares
                ?similarAuthor a bs:Author ;
                              rdfs:label ?authorName .
                
                FILTER (?similarAuthor != <%s>)
                
                # Criterios de similitud
                {
                    # Mismo movimiento literario
                    ?similarAuthor bs:literaryMovement ?movement .
                    BIND("Mismo movimiento literario" AS ?reason)
                } UNION {
                    # Mismo país de origen
                    ?similarAuthor bs:countryOfOrigin ?country .
                    BIND("Mismo país de origen" AS ?reason)
                } UNION {
                    # Influencias literarias
                    { <%s> bs:influencedBy ?similarAuthor }
                    UNION
                    { ?similarAuthor bs:influencedBy <%s> }
                    BIND("Influencia literaria" AS ?reason)
                }
            }
            LIMIT %d
            """ % (author_uri, author_uri, author_uri, author_uri, max_results)
            
            results = self.graph.query(query)
            recommendations = []
            
            for row in results:
                recommendations.append({
                    'author_uri': str(row.similarAuthor),
                    'author_name': str(row.authorName),
                    'reason': str(row.reason)
                })
            
            return recommendations
            
        except Exception as e:
            print(f"❌ Error en recomendaciones de autor: {e}")
            return []
    
    def infer_user_preferences(self, user_uri):
        """
        Infiere preferencias del usuario basado en su historial de lectura
        y la ontología
        """
        try:
            # Cargar historial del usuario
            from app.services.reading_tracker import reading_tracker
            reading_history = reading_tracker.get_user_reading_history(user_uri)
            
            if not reading_history:
                return {
                    'status': 'no_history',
                    'message': 'Usuario sin historial de lectura'
                }
            
            preferences = {
                'favorite_authors': [],
                'preferred_genres': [],
                'literary_movements': [],
                'reading_patterns': [],
                'exploration_level': 'beginner'
            }
            
            # Analizar cada libro leído
            for book in reading_history:
                book_uri = book['book_uri']
                
                # Consultar información semántica del libro
                book_info = self.get_book_semantic_info(book_uri)
                if book_info:
                    preferences = self._update_preferences(preferences, book_info)
            
            return preferences
            
        except Exception as e:
            print(f"❌ Error inferiendo preferencias: {e}")
            return {}
    
    def get_book_semantic_info(self, book_uri):
        """
        Obtiene información semántica completa de un libro
        """
        try:
            query = """
            PREFIX bs: <http://www.booksmart.org/ontology#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT ?title ?author ?authorName ?genre ?movement ?country
            WHERE {
                <%s> a bs:Book ;
                     rdfs:label ?title ;
                     bs:hasAuthor ?author ;
                     bs:hasGenre ?genre .
                
                ?author rdfs:label ?authorName .
                
                OPTIONAL { ?author bs:literaryMovement ?movement . }
                OPTIONAL { ?author bs:countryOfOrigin ?country . }
            }
            """ % book_uri
            
            results = list(self.graph.query(query))
            if results:
                row = results[0]
                return {
                    'title': str(row.title),
                    'author_uri': str(row.author),
                    'author_name': str(row.authorName),
                    'genre': str(row.genre),
                    'literary_movement': str(row.movement) if row.movement else None,
                    'country': str(row.country) if row.country else None
                }
            return None
            
        except Exception as e:
            print(f"❌ Error obteniendo info semántica: {e}")
            return None
    
    def _update_preferences(self, preferences, book_info):
        """
        Actualiza las preferencias con nueva información de libro
        """
        # Actualizar autores favoritos
        author_data = {
            'uri': book_info['author_uri'],
            'name': book_info['author_name'],
            'count': 1
        }
        
        # Buscar si el autor ya está en la lista
        existing_author = next((a for a in preferences['favorite_authors'] 
                              if a['uri'] == author_data['uri']), None)
        
        if existing_author:
            existing_author['count'] += 1
        else:
            preferences['favorite_authors'].append(author_data)
        
        # Actualizar géneros preferidos
        genre_data = {
            'name': book_info['genre'],
            'count': 1
        }
        
        existing_genre = next((g for g in preferences['preferred_genres'] 
                             if g['name'] == genre_data['name']), None)
        
        if existing_genre:
            existing_genre['count'] += 1
        else:
            preferences['preferred_genres'].append(genre_data)
        
        # Actualizar movimientos literarios
        if book_info['literary_movement']:
            movement_data = {
                'name': book_info['literary_movement'],
                'count': 1
            }
            
            existing_movement = next((m for m in preferences['literary_movements'] 
                                   if m['name'] == movement_data['name']), None)
            
            if existing_movement:
                existing_movement['count'] += 1
            else:
                preferences['literary_movements'].append(movement_data)
        
        return preferences

# Instancia global del gestor de ontología
ontology_manager = OntologyManager()