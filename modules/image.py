import aiohttp
import hashlib
import base64
from typing import Dict
from datetime import datetime
from modules.base import BaseModule

class ImageOSINT(BaseModule):
    def __init__(self, session, config, proxy_manager):
        super().__init__(session, config, proxy_manager)
        
    async def scan(self, image_url: str) -> Dict:
        results = {
            'target': image_url,
            'module': 'image',
            'status': 'success',
            'data': {
                'url': image_url,
                'hash': None,
                'hash_md5': None,
                'hash_sha1': None,
                'hash_sha256': None,
                'file_size': 0,
                'format': None,
                'width': None,
                'height': None,
                'exif': None,
                'gps': None,
                'gps_lat': None,
                'gps_lng': None,
                'reverse_search': [],
                'similar_images': [],
                'faces_detected': 0,
                'objects_detected': [],
                'text_detected': None,
                'is_ai_generated': False,
                'confidence': 0
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            async with self.session.get(image_url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    results['data']['file_size'] = len(data)
                    results['data']['hash_md5'] = hashlib.md5(data).hexdigest()
                    results['data']['hash_sha1'] = hashlib.sha1(data).hexdigest()
                    results['data']['hash_sha256'] = hashlib.sha256(data).hexdigest()
                    results['data']['hash'] = results['data']['hash_md5']
                    
                    content_type = resp.headers.get('content-type', '')
                    if 'image' in content_type:
                        results['data']['format'] = content_type.split('/')[-1]
                        
                    # Try to get EXIF
                    exif_data = await self._extract_exif(data)
                    if exif_data:
                        results['data']['exif'] = exif_data
                        if exif_data.get('gps'):
                            results['data']['gps'] = exif_data['gps']
                            results['data']['gps_lat'] = exif_data['gps'].get('lat')
                            results['data']['gps_lng'] = exif_data['gps'].get('lng')
                            
                    # Reverse image search
                    reverse_results = await self._reverse_search(data)
                    results['data']['reverse_search'] = reverse_results
                    
                    # Face detection
                    faces = await self._detect_faces(data)
                    results['data']['faces_detected'] = len(faces)
                    
                    # Object detection
                    objects = await self._detect_objects(data)
                    results['data']['objects_detected'] = objects
                    
                    # Text extraction
                    text = await self._extract_text(data)
                    if text:
                        results['data']['text_detected'] = text
                        
                    # AI detection
                    is_ai, confidence = await self._detect_ai(data)
                    results['data']['is_ai_generated'] = is_ai
                    results['data']['confidence'] = confidence
                        
        except:
            results['status'] = 'error'
            results['data']['error'] = 'Failed to fetch image'
            
        return results
        
    async def _extract_exif(self, data):
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS, GPSTAGS
            import io
            
            img = Image.open(io.BytesIO(data))
            exif = img.getexif()
            
            if not exif:
                return None
                
            exif_data = {}
            gps_data = {}
            
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'GPSInfo':
                    for gps_tag_id, gps_value in value.items():
                        gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_data[gps_tag] = gps_value
                    exif_data['gps'] = self._convert_gps(gps_data)
                else:
                    exif_data[tag] = value
                    
            return exif_data
        except:
            return None
            
    def _convert_gps(self, gps_data):
        try:
            lat = gps_data.get('GPSLatitude')
            lat_ref = gps_data.get('GPSLatitudeRef')
            lng = gps_data.get('GPSLongitude')
            lng_ref = gps_data.get('GPSLongitudeRef')
            
            if not lat or not lng:
                return None
                
            lat_val = self._convert_to_degrees(lat)
            lng_val = self._convert_to_degrees(lng)
            
            if lat_ref and lat_ref == 'S':
                lat_val = -lat_val
            if lng_ref and lng_ref == 'W':
                lng_val = -lng_val
                
            return {'lat': lat_val, 'lng': lng_val}
        except:
            return None
            
    def _convert_to_degrees(self, value):
        d = float(value[0])
        m = float(value[1])
        s = float(value[2])
        return d + (m / 60.0) + (s / 3600.0)
        
    async def _reverse_search(self, data):
        results = []
        try:
            # Google Reverse Image Search
            import base64
            b64 = base64.b64encode(data).decode('utf-8')
            async with self.session.post(
                'https://www.google.com/searchbyimage/upload',
                data={'encoded_image': b64}
            ) as resp:
                if resp.status == 200:
                    results.append({
                        'engine': 'Google',
                        'url': resp.url,
                        'status': 'success'
                    })
        except:
            pass
            
        try:
            # Yandex Reverse Image Search
            async with self.session.post(
                'https://yandex.com/images/search',
                data={'image': base64.b64encode(data).decode('utf-8')}
            ) as resp:
                if resp.status == 200:
                    results.append({
                        'engine': 'Yandex',
                        'url': resp.url,
                        'status': 'success'
                    })
        except:
            pass
            
        return results
        
    async def _detect_faces(self, data):
        try:
            import face_recognition
            import io
            from PIL import Image
            
            img = Image.open(io.BytesIO(data))
            face_locations = face_recognition.face_locations(np.array(img))
            return face_locations
        except:
            return []
            
    async def _detect_objects(self, data):
        try:
            # Simple object detection using color analysis (mock)
            objects = []
            # This would use YOLO or similar in production
            return objects
        except:
            return []
            
    async def _extract_text(self, data):
        try:
            import pytesseract
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(data))
            text = pytesseract.image_to_string(img)
            return text.strip() if text else None
        except:
            return None
            
    async def _detect_ai(self, data):
        try:
            # Simple AI detection (mock)
            # Would use CLIP or similar in production
            return False, 0
        except:
            return False, 0
