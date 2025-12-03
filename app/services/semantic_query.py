import os
from rdflib import Graph, Namespace, RDF, RDFS, Literal, URIRef
from rdflib.plugins.stores.sparqlstore import SPARQLStore
from config import Config

class SemanticQueryService:
    """
    Servicio para consultas SPARQL a la ontología de BookSmart
    Sin filtros de adaptaciones pero con info en descripción
    """
    
    def __init__(self):
        self.BS = Namespace("http://www.booksmart.org/ontology#")
        self.RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
        self.DCT = Namespace("http://purl.org/dc/terms/")
        
        self.graph = Graph()
        self.load_ontology()
        
        self.graph.bind("bs", self.BS)
        self.graph.bind("rdfs", self.RDFS)
        self.graph.bind("dct", self.DCT)
    
    def load_ontology(self):
        """Carga la ontología y datos literarios"""
        try:
            # Cargar ontología principal
            if os.path.exists(Config.ONTOLOGY_FILE):
                self.graph.parse(Config.ONTOLOGY_FILE, format="turtle")
                print("✅ Ontología principal cargada")
            
            # Cargar datos literarios
            if os.path.exists(Config.LITERARY_DATA_FILE):
                self.graph.parse(Config.LITERARY_DATA_FILE, format="turtle")
                book_count = len(list(self.graph.subjects(RDF.type, self.BS.Book)))
                print(f"✅ Datos literarios cargados: {book_count} libros encontrados")
            else:
                print(f"❌ Archivo no encontrado: {Config.LITERARY_DATA_FILE}")
                
        except Exception as e:
            print(f"❌ Error cargando ontología: {e}")
            import traceback
            traceback.print_exc()
    
    def search_books_advanced(self, search_params):
        """
        Búsqueda avanzada - Sin filtros de adaptaciones pero con info en resultados
        """
        print(f"🔍 SEMANTIC_QUERY: Iniciando búsqueda con params: {search_params}")
        
        # Solo estos filtros (sin adaptaciones)
        has_search_criteria = any([
            search_params.get('query'),
            search_params.get('genre'),
            search_params.get('author'),
            search_params.get('publisher'),
            search_params.get('year'),
            search_params.get('language'),
            search_params.get('country'),
            search_params.get('edition'),
            search_params.get('literary_period')
        ])
        
        if not has_search_criteria:
            print("🔍 SEMANTIC_QUERY: Sin criterios de búsqueda - devolviendo vacío")
            return []
        
        # Construir filtros (sin adaptaciones)
        filters = []
        
        if search_params.get('query'):
            query_value = search_params['query']
            filters.append(f'''
                (regex(str(?title), "{query_value}", "i") ||
                regex(str(?authorName), "{query_value}", "i") ||
                regex(str(?description), "{query_value}", "i"))
            ''')
        
        if search_params.get('genre'):
            genre_value = search_params['genre']
            filters.append(f'regex(str(?genre), "{genre_value}", "i")')
        
        if search_params.get('author'):
            author_value = search_params['author']
            filters.append(f'regex(str(?authorName), "{author_value}", "i")')
        
        if search_params.get('publisher'):
            publisher_value = search_params['publisher']
            filters.append(f'regex(str(?publisherName), "{publisher_value}", "i")')
        
        if search_params.get('year'):
            year_value = search_params['year']
            filters.append(f'str(?year) = "{year_value}"')
        
        if search_params.get('language'):
            language_value = search_params['language']
            filters.append(f'regex(str(?language), "{language_value}", "i")')
        
        if search_params.get('country'):
            country_value = search_params['country']
            filters.append(f'regex(str(?country), "{country_value}", "i")')
        
        if search_params.get('edition'):
            edition_value = search_params['edition']
            filters.append(f'regex(str(?edition), "{edition_value}", "i")')
        
        if search_params.get('literary_period'):
            period_value = search_params['literary_period']
            filters.append(f'regex(str(?literaryPeriod), "{period_value}", "i")')
        
        filter_clause = "FILTER (" + " && ".join(filters) + ")" if filters else ""
        
        # CONSULTA SIMPLE - Solo datos básicos
        query = f"""
        PREFIX bs: <http://www.booksmart.org/ontology#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dct: <http://purl.org/dc/terms/>
        
        SELECT DISTINCT ?book ?title ?authorName ?genre ?description ?year
            ?language ?country ?publisherName ?edition ?literaryPeriod
        WHERE {{
            ?book a bs:Book ;
                rdfs:label ?title ;
                bs:hasAuthor ?author ;
                bs:hasGenre ?genre .
                
            ?author rdfs:label ?authorName .
            
            OPTIONAL {{ ?book dct:description ?description . }}
            OPTIONAL {{ ?book bs:publicationYear ?year . }}
            OPTIONAL {{ ?book bs:originalLanguage ?language . }}
            OPTIONAL {{ ?book bs:countryOfOrigin ?country . }}
            OPTIONAL {{ ?book bs:editionInfo ?edition . }}
            OPTIONAL {{ ?book bs:literaryPeriod ?literaryPeriod . }}
            OPTIONAL {{ 
                ?book bs:publishedBy ?publisher .
                ?publisher rdfs:label ?publisherName .
            }}
            
            {filter_clause}
        }}
        ORDER BY ?title
        LIMIT 100
        """
        
        print(f"🔍 SEMANTIC_QUERY: Consulta ejecutándose...")
        
        try:
            results = self.graph.query(query)
            results_list = list(results)
            print(f"🔍 SEMANTIC_QUERY: Consulta devolvió: {len(results_list)} resultados")
            
            books = []
            for i, row in enumerate(results_list):
                try:
                    book_uri = str(row.book) if row.book else ""
                    
                    # OBTENER INFO DE ADAPTACIONES PARA ESTE LIBRO
                    adaptations_info = self._get_book_adaptations(book_uri)
                    
                    book_data = {
                        'uri': book_uri,
                        'title': str(row.title) if row.title else "Sin título",
                        'author': str(row.authorName) if row.authorName else "Autor desconocido",
                        'genre': str(row.genre) if row.genre else "Sin género",
                        'description': str(row.description) if row.description else "",
                        'year': str(row.year) if row.year else "Desconocido",
                        'language': str(row.language) if row.language else "No especificado",
                        'country': str(row.country) if row.country else "No especificado",
                        'publisher': str(row.publisherName) if row.publisherName else "No especificado",
                        'edition': str(row.edition) if row.edition else "No especificado",
                        'literary_period': str(row.literaryPeriod) if row.literaryPeriod else "No especificado",
                        'themes': [],
                        # INFORMACIÓN DE ADAPTACIONES
                        'adaptation_count': adaptations_info['adaptation_count'],
                        'adaptation_types': adaptations_info['adaptation_types'],
                        'adaptation_details': adaptations_info['adaptation_details'],
                        'has_adaptations': adaptations_info['has_adaptations']
                    }
                    
                    if book_data['title'] != "Sin título":
                        books.append(book_data)
                        print(f"✅ Libro {i+1}: {book_data['title']}")
                        if book_data['has_adaptations']:
                            print(f"   🎬 Tiene {book_data['adaptation_count']} adaptación(es)")
                        
                except Exception as row_error:
                    print(f"❌ Error procesando fila {i}: {row_error}")
                    continue
            
            print(f"🔍 SEMANTIC_QUERY: Total libros procesados: {len(books)}")
            return books
            
        except Exception as e:
            print(f"❌ Error en consulta SPARQL: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _get_book_adaptations(self, book_uri):
        """Obtiene información de adaptaciones para un libro específico"""
        try:
            query = """
            PREFIX bs: <http://www.booksmart.org/ontology#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT ?adaptationType ?adaptationLabel ?adaptationYear
            WHERE {
                ?book bs:hasAdaptation ?adaptation .
                ?adaptation bs:adaptationType ?adaptationType ;
                           rdfs:label ?adaptationLabel .
                OPTIONAL { ?adaptation bs:year ?adaptationYear . }
            }
            ORDER BY ?adaptationYear
            """
            
            results = list(self.graph.query(query, initBindings={'book': URIRef(book_uri)}))
            
            adaptation_count = len(results)
            adaptation_types = []
            adaptation_details = []
            
            for row in results:
                adaptation_type = str(row.adaptationType) if row.adaptationType else "Desconocido"
                adaptation_label = str(row.adaptationLabel) if row.adaptationLabel else ""
                adaptation_year = str(row.adaptationYear) if row.adaptationYear else ""
                
                if adaptation_type not in adaptation_types:
                    adaptation_types.append(adaptation_type)
                
                # Crear descripción detallada
                detail = f"{adaptation_type}"
                if adaptation_year:
                    detail += f" ({adaptation_year})"
                if adaptation_label:
                    detail += f": {adaptation_label}"
                    
                adaptation_details.append(detail)
            
            return {
                'adaptation_count': adaptation_count,
                'adaptation_types': adaptation_types,
                'adaptation_details': adaptation_details,
                'has_adaptations': adaptation_count > 0
            }
            
        except Exception as e:
            print(f"❌ Error obteniendo adaptaciones para {book_uri}: {e}")
            return {
                'adaptation_count': 0,
                'adaptation_types': [],
                'adaptation_details': [],
                'has_adaptations': False
            }
    
    def get_filter_options(self):
        """
        Obtiene todas las opciones disponibles para los filtros
        SIN FILTROS DE ADAPTACIONES
        """
        return {
            'genres': self._get_distinct_values("bs:hasGenre"),
            'authors': self._get_distinct_values("bs:hasAuthor", "rdfs:label"),
            'publishers': self._get_distinct_values("bs:publishedBy", "rdfs:label"),
            'languages': self._get_distinct_values("bs:originalLanguage"),
            'countries': self._get_distinct_values("bs:countryOfOrigin"),
            'editions': self._get_distinct_values("bs:editionInfo"),
            'literary_periods': self._get_distinct_values("bs:literaryPeriod"),
            'years': self._get_publication_years()
        }
    
    def _get_distinct_values(self, predicate, object_predicate=None):
        """Obtiene valores distintos para un predicado"""
        if object_predicate:
            query = f"""
            PREFIX bs: <http://www.booksmart.org/ontology#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT DISTINCT ?value
            WHERE {{
                ?book {predicate} ?obj .
                ?obj {object_predicate} ?value .
            }}
            ORDER BY ?value
            """
        else:
            query = f"""
            PREFIX bs: <http://www.booksmart.org/ontology#>
            
            SELECT DISTINCT ?value
            WHERE {{
                ?book {predicate} ?value .
            }}
            ORDER BY ?value
            """
        
        try:
            results = self.graph.query(query)
            return [str(row.value) for row in results if str(row.value)]
        except Exception as e:
            print(f"❌ Error obteniendo valores para {predicate}: {e}")
            return []
    
    def _get_publication_years(self):
        """Obtiene años de publicación disponibles"""
        query = """
        PREFIX bs: <http://www.booksmart.org/ontology#>
        
        SELECT DISTINCT ?year
        WHERE {
            ?book bs:publicationYear ?year .
        }
        ORDER BY ?year
        """
        
        try:
            results = self.graph.query(query)
            return [str(row.year) for row in results if str(row.year)]
        except Exception as e:
            print(f"❌ Error obteniendo años de publicación: {e}")
            return []

# Instancia global del servicio
semantic_query_service = SemanticQueryService()