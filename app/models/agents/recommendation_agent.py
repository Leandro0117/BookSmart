from app.models.ontology import ontology_manager
from app.services.semantic_query import semantic_query_service
import logging

class RecommendationAgent:
    """
    Agente de recomendación inteligente - Usa ontología para generar recomendaciones personalizadas
    """
    
    def __init__(self):
        self.ontology = ontology_manager
        self.semantic_query = semantic_query_service
        print("✅ RecommendationAgent inicializado - Listo para recomendaciones inteligentes")
    
    def generate_recommendations(self, user_insights, user_reading_history=None):
        """
        Genera recomendaciones basadas en los insights del usuario y la ontología
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
            
            # Eliminar duplicados y limitar resultados
            unique_recommendations = self._remove_duplicates(recommendations)
            
            print(f"🎯 Recomendaciones generadas: {len(unique_recommendations)} libros (filtrados de {len(recommendations)})")
            return unique_recommendations[:10]  # Máximo 10 recomendaciones
            
        except Exception as e:
            print(f"❌ Error generando recomendaciones: {e}")
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
                
            recommendations.append({
                'book': book,
                'reason': f"Te gusta {favorite_author}",
                'confidence': 0.9,
                'strategy': 'favorite_author'
            })
        
        return recommendations
    
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
                
            recommendations.append({
                'book': book,
                'reason': f"Te gusta el género {preferred_genre}",
                'confidence': 0.8,
                'strategy': 'preferred_genre'
            })
        
        return recommendations
    
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
                    recommendations.append({
                        'book': book,
                        'reason': f"Similar a {author_name}",
                        'confidence': 0.7,
                        'strategy': 'author_exploration'
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
                
            recommendations.append({
                'book': book,
                'reason': "Obra importante con adaptaciones",
                'confidence': 0.6,
                'strategy': 'fast_reader'
            })
        
        return recommendations[:3]  # Devolver máximo 3
    
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
                    
                recommendations.append({
                    'book': book,
                    'reason': "Literatura contemporánea para explorar",
                    'confidence': 0.5,
                    'strategy': 'exploration'
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
                'confidence': 0.5,
                'strategy': 'default'
            })
            
            if len(recommendations) >= 5:  # Solo 5 recomendaciones por defecto
                break
        
        return recommendations
    
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

# Instancia global del agente de recomendación
recommendation_agent = RecommendationAgent()