import os
from datetime import datetime, timedelta
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS
from collections import Counter
from config import Config

class UserProfileAgent:
    """
    Agente inteligente que analiza patrones de lectura del usuario
    Basado en el concepto: "El usuario solo marca lo que ha leído - el agente deduce por qué"
    """
    
    def __init__(self):
        self.BS = Namespace("http://www.booksmart.org/ontology#")
        self.USER = Namespace("http://www.booksmart.org/users/")
        self.graph = Graph()
        self.graph.bind("bs", self.BS)
        
    def analyze_user_profile(self, user_uri):
        """
        Analiza COMPLETAMENTE el perfil del usuario basado en su historial
        Retorna insights estructurados para el agente de recomendación
        """
        print(f"🧠 AGENTE: Analizando perfil de {user_uri}")
        
        # Cargar historial de lecturas
        reading_history = self._get_reading_history_with_details(user_uri)
        
        if not reading_history:
            print("📭 AGENTE: Sin historial de lecturas")
            return self._get_empty_profile()
        
        # Ejecutar todas las inferencias
        try:
            insights = {
                "preferencias_autores": self._infer_author_preferences(reading_history),
                "preferencias_generos": self._infer_genre_preferences(reading_history),
                "patrones_temporales": self._analyze_temporal_patterns(reading_history),
                "velocidad_lectura": self._calculate_reading_velocity(reading_history),
                "secuencias_literarias": self._detect_literary_sequences(reading_history),
                "nivel_exploracion": self._calculate_exploration_level(reading_history)
            }
            
            # Guardar perfil inferido en RDF
            self._save_semantic_profile(user_uri, insights)
            
            print(f"✅ AGENTE: Perfil analizado - {len(reading_history)} libros procesados")
            return insights
            
        except Exception as e:
            print(f"❌ AGENTE: Error en análisis: {e}")
            return self._get_empty_profile()
    
    def _get_reading_history_with_details(self, user_uri):
        """Obtiene el historial de lectura con detalles semánticos de los libros - CORREGIDO"""
        try:
            # Cargar datos literarios para enriquecer el historial
            literary_graph = Graph()
            if os.path.exists(Config.LITERARY_DATA_FILE):
                literary_graph.parse(Config.LITERARY_DATA_FILE, format="turtle")
                print(f"📖 AGENTE: Datos literarios cargados ({len(literary_graph)} tripletas)")
            
            # Cargar historial del usuario
            user_filename = user_uri.split('/')[-1] + '.ttl'
            user_filepath = os.path.join(Config.USER_READING_HISTORY_DIR, user_filename)
            
            if not os.path.exists(user_filepath):
                print(f"📭 AGENTE: No hay historial para {user_uri}")
                return []
            
            user_graph = Graph()
            user_graph.parse(user_filepath, format="turtle")
            print(f"📚 AGENTE: Historial cargado ({len(user_graph)} tripletas)")
            
            # Consulta básica del historial
            query = """
            PREFIX bs: <http://www.booksmart.org/ontology#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT ?book ?title ?readAt
            WHERE {
                ?user bs:hasRead ?book .
                ?book bs:readAt ?readAt ;
                      rdfs:label ?title .
            }
            ORDER BY DESC(?readAt)
            """
            
            results = user_graph.query(query, initBindings={'user': URIRef(user_uri)})
            
            readings = []
            for row in results:
                book_uri = str(row.book)
                title = str(row.title)
                read_at = str(row.readAt)
                
                # Buscar detalles en datos literarios por separado
                author = self._get_book_author(literary_graph, book_uri)
                genre = self._get_book_genre(literary_graph, book_uri)
                literary_period = self._get_book_literary_period(literary_graph, book_uri)
                country = self._get_book_country(literary_graph, book_uri)
                
                reading_data = {
                    'book_uri': book_uri,
                    'title': title,
                    'read_at': read_at,
                    'author': author,
                    'genre': genre,
                    'literary_period': literary_period,
                    'country': country
                }
                readings.append(reading_data)
            
            print(f"✅ AGENTE: {len(readings)} libros procesados con detalles")
            return readings
            
        except Exception as e:
            print(f"❌ AGENTE: Error obteniendo historial: {e}")
            import traceback
            traceback.print_exc()
            return []

    # MÉTODOS AUXILIARES PARA OBTENER DETALLES
    def _get_book_author(self, literary_graph, book_uri):
        """Obtiene el autor de un libro desde los datos literarios"""
        try:
            query = """
            PREFIX bs: <http://www.booksmart.org/ontology#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT ?authorName
            WHERE {
                ?book bs:hasAuthor ?author .
                ?author rdfs:label ?authorName .
            }
            """
            results = list(literary_graph.query(query, initBindings={'book': URIRef(book_uri)}))
            return str(results[0]['authorName']) if results else "Desconocido"
        except:
            return "Desconocido"

    def _get_book_genre(self, literary_graph, book_uri):
        """Obtiene el género de un libro desde los datos literarios"""
        try:
            query = """
            PREFIX bs: <http://www.booksmart.org/ontology#>
            
            SELECT ?genre
            WHERE {
                ?book bs:hasGenre ?genre .
            }
            """
            results = list(literary_graph.query(query, initBindings={'book': URIRef(book_uri)}))
            return str(results[0]['genre']) if results else "Sin género"
        except:
            return "Sin género"

    def _get_book_literary_period(self, literary_graph, book_uri):
        """Obtiene el periodo literario de un libro"""
        try:
            query = """
            PREFIX bs: <http://www.booksmart.org/ontology#>
            
            SELECT ?literaryPeriod
            WHERE {
                ?book bs:literaryPeriod ?literaryPeriod .
            }
            """
            results = list(literary_graph.query(query, initBindings={'book': URIRef(book_uri)}))
            return str(results[0]['literaryPeriod']) if results else "No especificado"
        except:
            return "No especificado"

    def _get_book_country(self, literary_graph, book_uri):
        """Obtiene el país de origen de un libro"""
        try:
            query = """
            PREFIX bs: <http://www.booksmart.org/ontology#>
            
            SELECT ?country
            WHERE {
                ?book bs:countryOfOrigin ?country .
            }
            """
            results = list(literary_graph.query(query, initBindings={'book': URIRef(book_uri)}))
            return str(results[0]['country']) if results else "No especificado"
        except:
            return "No especificado"
    
    def _infer_author_preferences(self, reading_history):
        """Infiere preferencias de autores basado en frecuencia y patrones"""
        try:
            author_count = Counter([r['author'] for r in reading_history])
            total_books = len(reading_history)
            
            autores_frecuentes = [author for author, count in author_count.most_common(5)]
            autores_releidos = [author for author, count in author_count.items() if count >= 2]
            
            return {
                "autores_frecuentes": autores_frecuentes,
                "autor_favorito": autores_frecuentes[0] if autores_frecuentes else None,
                "autores_releidos": autores_releidos,
                "diversidad_autores": len(author_count),
                "porcentaje_autor_favorito": (author_count[autores_frecuentes[0]] / total_books * 100) if autores_frecuentes else 0
            }
        except Exception as e:
            print(f"❌ AGENTE: Error en inferencia de autores: {e}")
            return {
                "autores_frecuentes": [], 
                "autor_favorito": None, 
                "autores_releidos": [],
                "diversidad_autores": 0,
                "porcentaje_autor_favorito": 0
            }
    
    def _infer_genre_preferences(self, reading_history):
        """Infiere preferencias de géneros literarios"""
        try:
            genre_count = Counter([r['genre'] for r in reading_history])
            total_books = len(reading_history)
            
            generos_frecuentes = [genre for genre, count in genre_count.most_common(3)]
            
            distribucion = {}
            for genre, count in genre_count.most_common():
                distribucion[genre] = count / total_books
            
            return {
                "generos_preferidos": generos_frecuentes,
                "genero_favorito": generos_frecuentes[0] if generos_frecuentes else None,
                "diversidad_generos": len(genre_count),
                "distribucion_generos": distribucion
            }
        except Exception as e:
            print(f"❌ AGENTE: Error en inferencia de géneros: {e}")
            return {
                "generos_preferidos": [], 
                "genero_favorito": None,
                "diversidad_generos": 0,
                "distribucion_generos": {}
            }
    
    def _analyze_temporal_patterns(self, reading_history):
        """Analiza patrones temporales de lectura"""
        try:
            if len(reading_history) < 2:
                return {"estado": "sin_historial"}
            
            # Convertir fechas
            dates = []
            for r in reading_history:
                try:
                    # Limpiar y convertir fecha
                    date_str = r['read_at'].replace('Z', '+00:00')
                    date_obj = datetime.fromisoformat(date_str)
                    dates.append(date_obj)
                except:
                    continue
            
            if len(dates) < 2:
                return {"estado": "datos_insuficientes"}
            
            dates.sort()
            
            # Calcular intervalos
            intervals = []
            for i in range(1, len(dates)):
                interval = (dates[i] - dates[i-1]).days
                intervals.append(interval)
            
            avg_interval = sum(intervals) / len(intervals) if intervals else 0
            
            return {
                "estado": "analizado",
                "total_libros": len(reading_history),
                "periodo_lectura_dias": (dates[-1] - dates[0]).days,
                "intervalo_promedio_dias": round(avg_interval, 1),
                "fecha_primer_libro": dates[0].isoformat(),
                "fecha_ultimo_libro": dates[-1].isoformat(),
                "tendencia": "creciente" if len(reading_history) >= 3 and intervals[-1] < avg_interval else "estable"
            }
        except Exception as e:
            print(f"❌ AGENTE: Error en análisis temporal: {e}")
            return {"estado": "error"}
    
    def _calculate_reading_velocity(self, reading_history):
        """Calcula la velocidad de lectura del usuario"""
        try:
            temporal = self._analyze_temporal_patterns(reading_history)
            
            if temporal["estado"] != "analizado":
                return {
                    "libros_mes": 0, 
                    "estado": temporal["estado"],
                    "ritmo_lectura": "sin datos",
                    "proyeccion_anual": 0
                }
            
            periodo_meses = temporal["periodo_lectura_dias"] / 30.0
            libros_mes = len(reading_history) / periodo_meses if periodo_meses > 0 else len(reading_history)
            
            # Determinar ritmo
            if libros_mes > 2:
                ritmo = "rápido"
            elif libros_mes > 0.5:
                ritmo = "moderado"
            else:
                ritmo = "ocasional"
            
            return {
                "libros_mes": round(libros_mes, 1),
                "estado": "calculado",
                "ritmo_lectura": ritmo,
                "proyeccion_anual": round(libros_mes * 12, 1)
            }
        except Exception as e:
            print(f"❌ AGENTE: Error en cálculo de velocidad: {e}")
            return {
                "libros_mes": 0, 
                "estado": "error",
                "ritmo_lectura": "sin datos",
                "proyeccion_anual": 0
            }
    
    def _detect_literary_sequences(self, reading_history):
        """Detecta secuencias literarias (ej: García Márquez → Autores similares)"""
        try:
            if len(reading_history) < 2:
                return {
                    "secuencias": [], 
                    "tiene_secuencias": False,
                    "secuencia_mas_larga": 0
                }
            
            sequences = []
            current_sequence = [reading_history[0]]
            
            for i in range(1, len(reading_history)):
                current_book = reading_history[i]
                prev_book = reading_history[i-1]
                
                # Detectar si hay relación (mismo autor, mismo género, mismo periodo)
                misma_tendencia = (
                    current_book['author'] == prev_book['author'] or
                    current_book['genre'] == prev_book['genre'] or
                    current_book['literary_period'] == prev_book['literary_period']
                )
                
                if misma_tendencia:
                    current_sequence.append(current_book)
                else:
                    if len(current_sequence) >= 2:
                        sequences.append({
                            'tipo': self._classify_sequence(current_sequence),
                            'libros': [b['title'] for b in current_sequence],
                            'longitud': len(current_sequence)
                        })
                    current_sequence = [current_book]
            
            # Agregar última secuencia
            if len(current_sequence) >= 2:
                sequences.append({
                    'tipo': self._classify_sequence(current_sequence),
                    'libros': [b['title'] for b in current_sequence],
                    'longitud': len(current_sequence)
                })
            
            secuencia_mas_larga = max([s['longitud'] for s in sequences]) if sequences else 0
            
            return {
                "secuencias": sequences,
                "tiene_secuencias": len(sequences) > 0,
                "secuencia_mas_larga": secuencia_mas_larga
            }
        except Exception as e:
            print(f"❌ AGENTE: Error en detección de secuencias: {e}")
            return {
                "secuencias": [], 
                "tiene_secuencias": False,
                "secuencia_mas_larga": 0
            }
    
    def _classify_sequence(self, sequence):
        """Clasifica el tipo de secuencia literaria"""
        try:
            autores = [book['author'] for book in sequence]
            generos = [book['genre'] for book in sequence]
            
            if len(set(autores)) == 1:
                return "exploracion_autor"
            elif len(set(generos)) == 1:
                return "exploracion_genero"
            else:
                return "transicion_literaria"
        except:
            return "secuencia_desconocida"
    
    def _calculate_exploration_level(self, reading_history):
        """Calcula qué tan explorador es el usuario"""
        try:
            autores_unicos = len(set([r['author'] for r in reading_history]))
            generos_unicos = len(set([r['genre'] for r in reading_history]))
            total_libros = len(reading_history)
            
            if total_libros == 0:
                return "sin_datos"
            
            diversidad_autores = autores_unicos / total_libros
            diversidad_generos = generos_unicos / total_libros
            
            if diversidad_autores > 0.7 and diversidad_generos > 0.6:
                return "alto_explorador"
            elif diversidad_autores > 0.4 and diversidad_generos > 0.3:
                return "moderado_explorador"
            else:
                return "especializado"
        except:
            return "sin_datos"
    
    def _save_semantic_profile(self, user_uri, insights):
        """Guarda el perfil inferido en RDF para uso futuro"""
        try:
            profile_file = os.path.join(Config.USER_PREFERENCES_DIR, f"{user_uri.split('/')[-1]}_profile.ttl")
            profile_graph = Graph()
            profile_graph.bind("bs", self.BS)
            profile_graph.bind("user", self.USER)
            
            user_ref = URIRef(user_uri)
            
            # Guardar preferencias de autores
            for autor in insights["preferencias_autores"]["autores_frecuentes"]:
                profile_graph.add((user_ref, self.BS.prefersAuthor, Literal(autor)))
            
            # Guardar preferencias de géneros
            for genero in insights["preferencias_generos"]["generos_preferidos"]:
                profile_graph.add((user_ref, self.BS.prefersGenre, Literal(genero)))
            
            # Guardar métricas
            profile_graph.add((user_ref, self.BS.readingVelocity, 
                             Literal(insights["velocidad_lectura"]["libros_mes"])))
            profile_graph.add((user_ref, self.BS.explorationLevel, 
                             Literal(insights["nivel_exploracion"])))
            
            profile_graph.serialize(destination=profile_file, format="turtle")
            print(f"💾 AGENTE: Perfil semántico guardado en {profile_file}")
            
        except Exception as e:
            print(f"❌ AGENTE: Error guardando perfil: {e}")
    
    def _get_empty_profile(self):
        """Perfil por defecto para usuarios sin historial - CORREGIDO"""
        return {
            "preferencias_autores": {
                "autores_frecuentes": [], 
                "autor_favorito": None, 
                "autores_releidos": [],
                "diversidad_autores": 0,
                "porcentaje_autor_favorito": 0
            },
            "preferencias_generos": {
                "generos_preferidos": [], 
                "genero_favorito": None,
                "diversidad_generos": 0,
                "distribucion_generos": {}
            },
            "patrones_temporales": {"estado": "sin_historial"},
            "velocidad_lectura": {
                "libros_mes": 0, 
                "estado": "sin_historial",
                "ritmo_lectura": "sin datos",
                "proyeccion_anual": 0
            },
            "secuencias_literarias": {
                "secuencias": [], 
                "tiene_secuencias": False,
                "secuencia_mas_larga": 0
            },
            "nivel_exploracion": "sin_datos"
        }

# Instancia global del agente
user_profile_agent = UserProfileAgent()