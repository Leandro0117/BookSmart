from app.models.ontology import ontology_manager
from app.services.semantic_query import semantic_query_service
import logging
from math import log
from datetime import datetime

class RecommendationAgent:
    """
    Agente de recomendación inteligente - Usa ontología para generar recomendaciones personalizadas
    CON FÓRMULA DE CONFIANZA DINÁMICA IMPLEMENTADA
    """
    
    def __init__(self):
        self.ontology = ontology_manager
        self.semantic_query = semantic_query_service
        # Factores de confianza base por estrategia
        self.confidence_base = {
            'favorite_author': 0.9,
            'preferred_genre': 0.8,
            'author_exploration': 0.7,
            'fast_reader': 0.6,
            'exploration': 0.5,
            'default': 0.5
        }
        print("✅ RecommendationAgent inicializado con cálculo dinámico de confianza")
    
    def generate_recommendations(self, user_insights, user_reading_history=None):
        """
        Genera recomendaciones basadas en los insights del usuario y la ontología
        CON CÁLCULO DE CONFIANZA DINÁMICO
        """
        try:
            if not user_insights or user_insights.get('patrones_temporales', {}).get('estado') == 'sin_historial':
                return self._get_default_recommendations(user_reading_history)
            
            # Obtener libros ya leídos por el usuario
            read_books = self._get_read_books_from_history(user_reading_history)
            print(f"📚 Libros ya leídos por el usuario: {len(read_books)}")
            
            recommendations = []
            
            # ESTRATEGIA 1: Recomendaciones por autor favorito
            favorite_author_recs = self._recommend_by_favorite_author(user_insights, read_books)
            recommendations.extend(favorite_author_recs)
            
            # ESTRATEGIA 2: Recomendaciones por género preferido
            genre_recs = self._recommend_by_preferred_genre(user_insights, read_books)
            recommendations.extend(genre_recs)
            
            # ESTRATEGIA 3: Recomendaciones por patrones detectados
            pattern_recs = self._recommend_by_reading_patterns(user_insights, read_books)
            recommendations.extend(pattern_recs)
            
            # ESTRATEGIA 4: Recomendaciones diversas (exploración)
            exploration_recs = self._recommend_for_exploration(user_insights, read_books)
            recommendations.extend(exploration_recs)
            
            # CALCULAR CONFIANZAS FINALES CON FÓRMULA
            recommendations_with_adjusted_confidence = []
            for rec in recommendations:
                adjusted_rec = self._calculate_adjusted_confidence(rec, user_insights, user_reading_history)
                recommendations_with_adjusted_confidence.append(adjusted_rec)
            
            # Eliminar duplicados y ordenar por confianza
            unique_recommendations = self._remove_duplicates(recommendations_with_adjusted_confidence)
            sorted_recommendations = self._sort_by_confidence(unique_recommendations)
            
            # Mostrar estadísticas de confianza
            self._print_confidence_stats(sorted_recommendations)
            
            print(f"🎯 Recomendaciones generadas: {len(sorted_recommendations)} libros")
            return sorted_recommendations[:10]  # Máximo 10 recomendaciones
            
        except Exception as e:
            print(f"❌ Error generando recomendaciones: {e}")
            import traceback
            traceback.print_exc()
            return self._get_default_recommendations(user_reading_history)
    
    def _get_read_books_from_history(self, user_reading_history):
        """Extrae los URIs de los libros que el usuario ya ha leído"""
        read_books = set()
        
        if user_reading_history:
            for reading_record in user_reading_history:
                if reading_record.get('book_uri'):
                    read_books.add(reading_record['book_uri'])
                # También verificar por título como respaldo
                if reading_record.get('book_title'):
                    read_books.add(reading_record['book_title'].lower())
        
        return read_books
    
    def _is_book_already_read(self, book, read_books):
        """Verifica si un libro ya fue leído por el usuario"""
        book_uri = book.get('uri', '')
        book_title = book.get('title', '').lower()
        
        return (book_uri in read_books or book_title in read_books)
    
    def _recommend_by_favorite_author(self, user_insights, read_books):
        """Recomienda más libros del autor favorito o autores similares"""
        recommendations = []
        
        favorite_author = user_insights.get('preferencias_autores', {}).get('autor_favorito')
        if not favorite_author:
            return recommendations
        
        print(f"🔍 Buscando recomendaciones para autor favorito: {favorite_author}")
        
        # Buscar libros del mismo autor
        author_books = self.semantic_query.search_books_advanced({'author': favorite_author})
        
        for book in author_books:
            # FILTRAR: No recomendar libros ya leídos
            if self._is_book_already_read(book, read_books):
                continue
            
            # Calcular frecuencia de este autor en el historial
            author_frequency = self._calculate_author_frequency(favorite_author, user_insights)
            
            recommendations.append({
                'book': book,
                'reason': f"Te gusta {favorite_author}",
                'confidence': self.confidence_base['favorite_author'],
                'strategy': 'favorite_author',
                'author_frequency': author_frequency,
                'base_confidence': self.confidence_base['favorite_author']
            })
        
        return recommendations
    
    def _calculate_author_frequency(self, author_name, user_insights):
        """Calcula qué tan frecuente es un autor en el historial del usuario"""
        try:
            autores_frecuentes = user_insights.get('preferencias_autores', {}).get('autores_frecuentes', [])
            autores_releidos = user_insights.get('preferencias_autores', {}).get('autores_releidos', [])
            
            # Verificar si el autor está en la lista de frecuentes
            if author_name in autores_frecuentes:
                position = autores_frecuentes.index(author_name)
                # El autor favorito (posición 0) tiene máxima frecuencia
                frequency = 1.0 - (position * 0.1)  # Disminuye con la posición
            else:
                frequency = 0.3  # Frecuencia baja si no está en frecuentes
            
            # Aumentar frecuencia si es releído
            if author_name in autores_releidos:
                frequency += 0.2
            
            return min(frequency, 1.0)
        except:
            return 0.5  # Valor por defecto
    
    def _recommend_by_preferred_genre(self, user_insights, read_books):
        """Recomienda libros del género preferido del usuario"""
        recommendations = []
        
        preferred_genre = user_insights.get('preferencias_generos', {}).get('genero_favorito')
        if not preferred_genre:
            return recommendations
        
        print(f"🔍 Buscando recomendaciones para género favorito: {preferred_genre}")
        
        # Buscar libros del mismo género
        genre_books = self.semantic_query.search_books_advanced({'genre': preferred_genre})
        
        for book in genre_books:
            # FILTRAR: No recomendar libros ya leídos
            if self._is_book_already_read(book, read_books):
                continue
            
            # Calcular peso del género en preferencias
            genre_weight = self._calculate_genre_weight(preferred_genre, user_insights)
            
            recommendations.append({
                'book': book,
                'reason': f"Te gusta el género {preferred_genre}",
                'confidence': self.confidence_base['preferred_genre'],
                'strategy': 'preferred_genre',
                'genre_weight': genre_weight,
                'base_confidence': self.confidence_base['preferred_genre']
            })
        
        return recommendations
    
    def _calculate_genre_weight(self, genre_name, user_insights):
        """Calcula qué tan preferido es un género"""
        try:
            generos_preferidos = user_insights.get('preferencias_generos', {}).get('generos_preferidos', [])
            distribucion = user_insights.get('preferencias_generos', {}).get('distribucion_generos', {})
            
            if genre_name in generos_preferidos:
                position = generos_preferidos.index(genre_name)
                weight = 1.0 - (position * 0.15)  # Disminuye con la posición
            else:
                weight = 0.3
            
            # Ajustar por distribución si está disponible
            if genre_name in distribucion:
                weight *= (1.0 + distribucion[genre_name])  # Aumentar según porcentaje
            
            return min(weight, 1.2)  # Permitir hasta 1.2
        except:
            return 0.5
    
    def _recommend_by_reading_patterns(self, user_insights, read_books):
        """Recomienda basado en patrones de lectura detectados"""
        recommendations = []
        
        # Patrón: Exploración de autores
        if user_insights.get('preferencias_autores', {}).get('autores_releidos'):
            author_pattern_recs = self._recommend_for_author_exploration(user_insights, read_books)
            recommendations.extend(author_pattern_recs)
        
        # Patrón: Velocidad de lectura
        reading_speed = user_insights.get('velocidad_lectura', {}).get('libros_mes', 1)
        if reading_speed > 2:  # Usuario rápido
            speed_recs = self._recommend_for_fast_readers(user_insights, read_books)
            recommendations.extend(speed_recs)
        
        # Patrón: Secuencias literarias detectadas
        if user_insights.get('secuencias_literarias', {}).get('tiene_secuencias'):
            sequence_recs = self._recommend_by_literary_sequences(user_insights, read_books)
            recommendations.extend(sequence_recs)
        
        return recommendations
    
    def _recommend_for_author_exploration(self, user_insights, read_books):
        """Recomienda para usuarios que exploran autores en profundidad"""
        recommendations = []
        
        # Buscar autores similares a los que ya leyó
        read_authors = user_insights.get('preferencias_autores', {}).get('autores_frecuentes', [])
        
        for author_name in read_authors[:2]:  # Tomar máximo 2 autores
            # Buscar libros de autores relacionados semánticamente
            similar_books = self.semantic_query.search_books_advanced({
                'query': author_name,
                'genre': user_insights.get('preferencias_generos', {}).get('genero_favorito', '')
            })
            
            for book in similar_books:
                # FILTRAR: No recomendar libros ya leídos
                if self._is_book_already_read(book, read_books):
                    continue
                    
                if book['author'] != author_name:  # Evitar recomendar el mismo autor
                    # Calcular similitud con autor original
                    author_similarity = 0.7 if book['author'] in read_authors else 0.5
                    
                    recommendations.append({
                        'book': book,
                        'reason': f"Similar a {author_name}",
                        'confidence': self.confidence_base['author_exploration'],
                        'strategy': 'author_exploration',
                        'author_similarity': author_similarity,
                        'base_confidence': self.confidence_base['author_exploration']
                    })
        
        return recommendations
    
    def _recommend_for_fast_readers(self, user_insights, read_books):
        """Recomienda sagas o libros largos para lectores rápidos"""
        recommendations = []
        
        # Buscar libros con adaptaciones (suelen ser obras importantes/largas)
        all_books = self.semantic_query.search_books_advanced({})
        books_with_adaptations = [book for book in all_books if book.get('has_adaptations')]
        
        for book in books_with_adaptations[:5]:  # Tomar más opciones para filtrar
            # FILTRAR: No recomendar libros ya leídos
            if self._is_book_already_read(book, read_books):
                continue
            
            # Calcular factor de importancia basado en adaptaciones
            adaptation_factor = 1.0 + (book.get('adaptation_count', 0) * 0.1)
            
            recommendations.append({
                'book': book,
                'reason': "Obra importante con adaptaciones",
                'confidence': self.confidence_base['fast_reader'],
                'strategy': 'fast_reader',
                'adaptation_factor': adaptation_factor,
                'base_confidence': self.confidence_base['fast_reader']
            })
        
        return recommendations[:3]  # Devolver máximo 3
    
    def _recommend_by_literary_sequences(self, user_insights, read_books):
        """Recomienda basado en secuencias literarias detectadas"""
        recommendations = []
        
        sequences = user_insights.get('secuencias_literarias', {}).get('secuencias', [])
        
        for sequence in sequences[:2]:  # Tomar máximo 2 secuencias
            sequence_type = sequence.get('tipo', '')
            sequence_books = sequence.get('libros', [])
            
            if sequence_type == 'exploracion_autor' and sequence_books:
                # Para secuencias de exploración de autor, recomendar más del mismo autor
                first_book_title = sequence_books[0]
                # Buscar autor del primer libro de la secuencia
                author_books = self.semantic_query.search_books_advanced({'query': first_book_title})
                
                if author_books:
                    author = author_books[0]['author']
                    more_books = self.semantic_query.search_books_advanced({'author': author})
                    
                    for book in more_books[:3]:
                        if not self._is_book_already_read(book, read_books):
                            recommendations.append({
                                'book': book,
                                'reason': f"Continúa tu exploración de {author}",
                                'confidence': 0.75,
                                'strategy': 'sequence_followup',
                                'base_confidence': 0.75
                            })
        
        return recommendations
    
    def _recommend_for_exploration(self, user_insights, read_books):
        """Recomienda libros diversos para fomentar exploración"""
        recommendations = []
        
        # Buscar libros de géneros diversos
        exploration_level = user_insights.get('nivel_exploracion', 'moderado')
        
        if exploration_level in ['alto_explorador', 'moderado']:
            # Recomendar libros de diferentes épocas literarias
            diverse_books = self.semantic_query.search_books_advanced({
                'literary_period': 'Contemporáneo'
            })
            
            for book in diverse_books[:5]:  # Tomar más opciones para filtrar
                # FILTRAR: No recomendar libros ya leídos
                if self._is_book_already_read(book, read_books):
                    continue
                
                # Factor de diversidad basado en nivel de exploración
                diversity_factor = 1.0 if exploration_level == 'alto_explorador' else 0.8
                
                recommendations.append({
                    'book': book,
                    'reason': "Literatura contemporánea para explorar",
                    'confidence': self.confidence_base['exploration'],
                    'strategy': 'exploration',
                    'diversity_factor': diversity_factor,
                    'base_confidence': self.confidence_base['exploration']
                })
        
        return recommendations[:2]  # Devolver máximo 2
    
    def _get_default_recommendations(self, user_reading_history=None):
        """Recomendaciones por defecto cuando no hay suficiente historial"""
        print("🔍 Generando recomendaciones por defecto")
        
        # Obtener libros ya leídos
        read_books = self._get_read_books_from_history(user_reading_history)
        
        default_books = self.semantic_query.search_books_advanced({})
        recommendations = []
        
        for book in default_books:
            # FILTRAR: No recomendar libros ya leídos
            if self._is_book_already_read(book, read_books):
                continue
            
            recommendations.append({
                'book': book,
                'reason': "Libro popular para comenzar",
                'confidence': self.confidence_base['default'],
                'strategy': 'default',
                'base_confidence': self.confidence_base['default']
            })
            
            if len(recommendations) >= 5:  # Solo 5 recomendaciones por defecto
                break
        
        return recommendations
    
    def _calculate_adjusted_confidence(self, recommendation, user_insights, reading_history):
        """
        Calcula la confianza final ajustada usando fórmula dinámica
        Fórmula: ConfianzaFinal = Base × Frecuencia × Exploración × Tiempo × Especial
        """
        try:
            # 1. Confianza base de la estrategia
            base_confidence = recommendation.get('base_confidence', 0.5)
            
            # 2. Factor de frecuencia (cuántas veces aparece el patrón)
            frequency_factor = 1.0
            strategy = recommendation.get('strategy', '')
            
            if strategy == 'favorite_author':
                frequency_factor = recommendation.get('author_frequency', 0.5)
            elif strategy == 'preferred_genre':
                frequency_factor = recommendation.get('genre_weight', 0.5)
            elif strategy == 'author_exploration':
                frequency_factor = recommendation.get('author_similarity', 0.6)
            elif strategy == 'fast_reader':
                frequency_factor = recommendation.get('adaptation_factor', 1.0)
            elif strategy == 'exploration':
                frequency_factor = recommendation.get('diversity_factor', 0.8)
            
            # 3. Factor de exploración del usuario
            exploration_level = user_insights.get('nivel_exploracion', 'moderado')
            exploration_factor = self._get_exploration_factor(exploration_level, strategy)
            
            # 4. Factor temporal (penalizar recomendaciones basadas en patrones antiguos)
            temporal_factor = self._calculate_temporal_factor(reading_history)
            
            # 5. Factor especial para libros con adaptaciones
            special_factor = 1.0
            book = recommendation.get('book', {})
            if book.get('has_adaptations'):
                special_factor = 1.1  # 10% más de confianza para libros con adaptaciones
            
            # APLICAR FÓRMULA
            adjusted_confidence = base_confidence * frequency_factor * exploration_factor * temporal_factor * special_factor
            
            # Limitar entre 0.1 y 1.0
            adjusted_confidence = max(0.1, min(adjusted_confidence, 1.0))
            
            # Redondear a 2 decimales
            adjusted_confidence = round(adjusted_confidence, 2)
            
            # Actualizar la recomendación con la confianza calculada
            recommendation['confidence'] = adjusted_confidence
            recommendation['confidence_factors'] = {
                'base': base_confidence,
                'frequency': frequency_factor,
                'exploration': exploration_factor,
                'temporal': temporal_factor,
                'special': special_factor
            }
            
            return recommendation
            
        except Exception as e:
            print(f"⚠️ Error calculando confianza ajustada: {e}")
            return recommendation
    
    def _get_exploration_factor(self, exploration_level, strategy):
        """Factor basado en nivel de exploración del usuario"""
        exploration_factors = {
            'alto_explorador': {
                'exploration': 1.2,    # Más confianza en recomendaciones exploratorias
                'default': 1.1,
                'other': 1.0
            },
            'moderado_explorador': {
                'exploration': 1.0,
                'default': 1.0,
                'other': 0.9
            },
            'especializado': {
                'exploration': 0.7,    # Menos confianza en exploración
                'default': 0.8,
                'other': 1.0
            },
            'sin_datos': {
                'exploration': 0.8,
                'default': 1.0,
                'other': 0.9
            }
        }
        
        factor_config = exploration_factors.get(exploration_level, exploration_factors['sin_datos'])
        
        if strategy == 'exploration':
            return factor_config['exploration']
        elif strategy == 'default':
            return factor_config['default']
        else:
            return factor_config['other']
    
    def _calculate_temporal_factor(self, reading_history):
        """Factor basado en antigüedad de las lecturas"""
        if not reading_history or len(reading_history) < 2:
            return 1.0  # Sin historial suficiente
        
        try:
            # Obtener la fecha de la última lectura
            latest_readings = sorted(
                reading_history,
                key=lambda x: x.get('read_at', ''),
                reverse=True
            )
            
            if latest_readings:
                # Si hay lecturas recientes (últimos 30 días), factor más alto
                # En un sistema real, aquí se analizarían las fechas
                # Por ahora, simplificamos
                return 1.0
            else:
                return 0.8  # Lecturas antiguas
        
        except:
            return 1.0
    
    def _remove_duplicates(self, recommendations):
        """Elimina recomendaciones duplicadas"""
        seen_uris = set()
        unique_recommendations = []
        
        for rec in recommendations:
            book_uri = rec['book']['uri']
            if book_uri not in seen_uris:
                seen_uris.add(book_uri)
                unique_recommendations.append(rec)
        
        return unique_recommendations
    
    def _sort_by_confidence(self, recommendations):
        """Ordena recomendaciones por confianza (descendente)"""
        return sorted(recommendations, key=lambda x: x['confidence'], reverse=True)
    
    def _print_confidence_stats(self, recommendations):
        """Imprime estadísticas de confianza de las recomendaciones"""
        if not recommendations:
            return
        
        confidences = [r['confidence'] for r in recommendations]
        avg_confidence = sum(confidences) / len(confidences)
        max_confidence = max(confidences)
        min_confidence = min(confidences)
        
        print(f"📊 Estadísticas de confianza:")
        print(f"   • Promedio: {avg_confidence:.2f}")
        print(f"   • Máxima: {max_confidence:.2f}")
        print(f"   • Mínima: {min_confidence:.2f}")
        print(f"   • Rango: {max_confidence - min_confidence:.2f}")
        
        # Mostrar distribución por estrategia
        strategies = {}
        for rec in recommendations:
            strategy = rec.get('strategy', 'unknown')
            strategies[strategy] = strategies.get(strategy, 0) + 1
        
        print(f"   • Distribución por estrategia:")
        for strategy, count in strategies.items():
            print(f"     - {strategy}: {count} recomendaciones")

# Instancia global del agente de recomendación
recommendation_agent = RecommendationAgent()