import requests
import logging
import re
from typing import List, Dict, Tuple, Optional
import os
import json
from config import USER_AGENT, MAX_FILE_SIZE

logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.base_url = "https://yts.mx/api/v2"
    
    def search_files(self, url: str, query: str, file_type: Optional[str] = None) -> List[Dict]:
        """
        Search for movies on YTS.mx based on query
        
        Args:
            url: Ignored (always uses YTS.mx API)
            query: Search term for movies
            file_type: Type of file (quality) to filter by ('720p', '1080p', '2160p', or None for all)
            
        Returns:
            List of dictionaries containing movie information
        """
        try:
            logger.info(f"Searching for '{query}' on YTS.mx")
            
            # Set up API request parameters
            params = {
                'query_term': query,
                'limit': 20,
                'sort_by': 'download_count',
                'order_by': 'desc'
            }
            
            # Get data from YTS API
            response = self.session.get(f"{self.base_url}/list_movies.json", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check if the API response is successful
            if data.get('status') != 'ok':
                logger.error(f"YTS API error: {data.get('status_message', 'Unknown error')}")
                return []
                
            # Check if movies were found
            movies_data = data.get('data', {})
            if movies_data.get('movie_count', 0) == 0:
                logger.info(f"No movies found for query: {query}")
                return []
                
            # Process movies
            results = []
            for movie in movies_data.get('movies', []):
                title = movie.get('title_long', 'Unknown Title')
                rating = movie.get('rating', 0)
                year = movie.get('year', 'Unknown')
                
                # Process each torrent (file) for the movie
                for torrent in movie.get('torrents', []):
                    quality = torrent.get('quality', 'Unknown')
                    
                    # Skip if file_type (quality) is specified and doesn't match
                    if file_type and file_type.lower() != quality.lower():
                        continue
                        
                    size = torrent.get('size', 'Unknown size')
                    seeds = torrent.get('seeds', 0)
                    download_url = torrent.get('url', '')
                    
                    # Create a result entry
                    results.append({
                        'title': f"{title} ({year}) - {quality} [Rating: {rating}]",
                        'url': download_url,
                        'size': size,
                        'type': 'video',
                        'seeds': seeds,
                        'movie_id': movie.get('id'),
                        'movie_url': movie.get('url'),
                        'quality': quality,
                        'thumbnail': movie.get('medium_cover_image'),
                        'hash': torrent.get('hash', '')
                    })
            
            # Sort by seeds (most popular first)
            results.sort(key=lambda x: x.get('seeds', 0), reverse=True)
            
            return results[:10]  # Limit to 10 results
            
        except Exception as e:
            logger.error(f"Error searching YTS.mx: {str(e)}")
            return []
    
    def get_movie_details(self, movie_id) -> Dict:
        """
        Get detailed information about a specific movie
        
        Args:
            movie_id: The YTS movie ID (can be int or str)
            
        Returns:
            Dictionary with movie details
        """
        try:
            # Set up API request parameters
            params = {
                'movie_id': str(movie_id),
                'with_images': 'true',
                'with_cast': 'true'
            }
            
            # Get data from YTS API
            response = self.session.get(f"{self.base_url}/movie_details.json", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check if the API response is successful
            if data.get('status') != 'ok':
                logger.error(f"YTS API error: {data.get('status_message', 'Unknown error')}")
                return {}
                
            # Extract movie details
            movie_data = data.get('data', {}).get('movie', {})
            if not movie_data:
                return {}
                
            return movie_data
            
        except Exception as e:
            logger.error(f"Error getting movie details: {str(e)}")
            return {}
    
    def check_file_exists(self, url: str) -> Tuple[bool, Optional[int]]:
        """
        Check if a torrent URL exists
        
        Note: For torrents, we can't easily check size, so we assume it's valid
        if it's from YTS.mx and the URL looks valid
        
        Returns:
            Tuple of (exists: bool, size: Optional[int])
        """
        try:
            # For YTS.mx torrents, we'll check if the URL exists by making a HEAD request
            if url and 'yts' in url.lower() and len(url) > 10:
                # First, check if the URL exists with a HEAD request
                try:
                    response = self.session.head(url, timeout=5)
                    if response.status_code == 200:
                        # URL exists, return a placeholder size
                        return True, 1 * 1024 * 1024  # Assume 1MB (torrent files are small)
                except Exception:
                    # If HEAD request fails, still try to download
                    # YTS URLs sometimes block HEAD requests but allow GET
                    pass
                
                # Even if HEAD fails, still consider the URL valid for YTS.mx
                # We'll handle any errors during actual download
                return True, 1 * 1024 * 1024  # Assume 1MB for torrent file
            
            return False, None
        except Exception as e:
            logger.error(f"Error checking torrent URL: {str(e)}")
            return False, None
    
    def find_direct_download_links(self, movie_id: int, quality: str) -> List[Dict]:
        """
        Find direct download links for a movie
        
        Args:
            movie_id: The YTS movie ID
            quality: Desired quality (e.g., '720p', '1080p')
            
        Returns:
            List of dictionaries containing direct download link information
        """
        try:
            # Get movie details first
            movie_details = self.get_movie_details(movie_id)
            if not movie_details:
                return []
                
            title = movie_details.get('title_long', 'Unknown')
            
            # Process torrents to generate webtor and magnet links
            torrents = movie_details.get('torrents', [])
            results = []
            
            for torrent in torrents:
                torrent_quality = torrent.get('quality', '')
                if quality and quality.lower() != torrent_quality.lower():
                    continue
                    
                torrent_hash = torrent.get('hash', '')
                if not torrent_hash:
                    continue
                
                # Generate webtor.io link for streaming/downloading
                webtor_link = self.get_webtor_link(torrent_hash, title)
                
                # Generate magnet link as backup
                magnet_link = self.get_magnet_link(torrent_hash, title)
                
                # Add webtor.io option
                results.append({
                    'title': f"{title} - {torrent_quality} (Stream/Download)",
                    'url': webtor_link,
                    'type': 'webtor',
                    'quality': torrent_quality,
                    'size': torrent.get('size', 'Unknown'),
                    'magnet': magnet_link  # Include magnet as backup
                })
                
            return results
            
        except Exception as e:
            logger.error(f"Error finding direct download links: {str(e)}")
            return []
    
    def get_magnet_link(self, torrent_hash: str, title: str) -> str:
        """
        Generate a magnet link from a torrent hash
        
        Args:
            torrent_hash: The hash of the torrent
            title: The title of the movie (for naming)
            
        Returns:
            A magnet link that can be opened by torrent clients
        """
        if not torrent_hash:
            return ""
            
        # Base64 encode the title to avoid special characters issues
        import base64
        encoded_title = base64.b64encode(title.encode('utf-8')).decode('utf-8')
        
        # Trackers for YTS.mx
        trackers = [
            "udp://open.demonii.com:1337/announce",
            "udp://tracker.openbittorrent.com:80",
            "udp://tracker.coppersurfer.tk:6969",
            "udp://glotorrents.pw:6969/announce",
            "udp://tracker.opentrackr.org:1337/announce",
            "udp://torrent.gresille.org:80/announce",
            "udp://p4p.arenabg.com:1337",
            "udp://tracker.leechers-paradise.org:6969"
        ]
        
        # Create the tracker parameters
        tracker_params = "&".join([f"tr={tracker}" for tracker in trackers])
        
        # Generate the magnet link
        magnet_link = f"magnet:?xt=urn:btih:{torrent_hash}&dn={encoded_title}&{tracker_params}"
        
        return magnet_link
        
    def get_webtor_link(self, torrent_hash: str, title: str) -> str:
        """
        Generate streaming link from a torrent hash
        
        Args:
            torrent_hash: The hash of the torrent
            title: The title of the movie (for naming)
            
        Returns:
            A streaming link that can be used to watch the movie directly
        """
        if not torrent_hash:
            return ""
        
        # Clean the title for URL safety (replace spaces with dashes, remove special chars)
        import re
        import urllib.parse
        
        # First get the magnet link (needed for multiple streaming services)
        magnet_link = self.get_magnet_link(torrent_hash, title)
        encoded_magnet = urllib.parse.quote_plus(magnet_link)
        
        # Using webtor.io for browser streaming
        streaming_link = f"https://webtor.io/#{encoded_magnet}"
        
        return streaming_link
    
    def get_website_text_content(self, url: str) -> str:
        """
        Get the main text content of a YTS movie page
        """
        try:
            # Extract movie ID from URL
            movie_id = None
            if '/movie/' in url:
                movie_id = url.split('/movie/')[1].split('/')[0]
            
            if not movie_id:
                return "Could not extract movie ID from URL"
                
            # Get movie details
            movie_details = self.get_movie_details(movie_id)
            if not movie_details:
                return "No movie details found"
                
            # Format movie information as text
            title = movie_details.get('title_long', 'Unknown Title')
            year = movie_details.get('year', 'Unknown')
            rating = movie_details.get('rating', 0)
            genres = ', '.join(movie_details.get('genres', ['Unknown']))
            description = movie_details.get('description_full', 'No description available')
            
            text = f"Movie: {title} ({year})\n"
            text += f"Rating: {rating}/10\n"
            text += f"Genres: {genres}\n\n"
            text += f"Description:\n{description}\n\n"
            
            # Add cast information if available
            cast = movie_details.get('cast', [])
            if cast:
                text += "Cast:\n"
                for actor in cast:
                    text += f"- {actor.get('name', 'Unknown Actor')}\n"
            
            return text
        except Exception as e:
            logger.error(f"Error extracting movie info: {str(e)}")
            return f"Error extracting movie information: {str(e)}"