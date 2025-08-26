import os
import uuid
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings

try:
    from PIL import Image, ImageOps
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


def generate_image_filename(instance, filename):
    """
    Generate a unique filename for uploaded images.
    """
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('products', 'images', filename)


def validate_image(image_file):
    """
    Validate uploaded image file.
    """
    # Check file size
    max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 5 * 1024 * 1024)  # Default 5MB
    if image_file.size > max_size:
        raise ValueError(f"Image file too large. Maximum size is {max_size / (1024 * 1024):.1f}MB")
    
    # Check file type
    allowed_types = getattr(settings, 'ALLOWED_IMAGE_TYPES', ['image/jpeg', 'image/png', 'image/webp'])
    if image_file.content_type not in allowed_types:
        raise ValueError(f"Invalid image type. Allowed types: {', '.join(allowed_types)}")
    
    # Try to open the image with PIL to verify it's a valid image (if available)
    if PILLOW_AVAILABLE:
        try:
            img = Image.open(image_file)
            img.verify()
        except Exception:
            raise ValueError("Invalid image file")


def process_image(image_file, max_size=None, quality=None):
    """
    Process and optimize an image file.
    
    Args:
        image_file: Django UploadedFile
        max_size: Tuple (width, height) for maximum dimensions
        quality: JPEG quality (1-100)
    
    Returns:
        Processed image as ContentFile
    """
    if not PILLOW_AVAILABLE:
        # If Pillow is not available, return the original file
        return ContentFile(image_file.read())
    
    if quality is None:
        quality = getattr(settings, 'IMAGE_QUALITY', 85)
    
    if max_size is None:
        max_size = getattr(settings, 'LARGE_IMAGE_SIZE', (1200, 1200))
    
    # Open the image
    img = Image.open(image_file)
    
    # Fix orientation based on EXIF data
    img = ImageOps.exif_transpose(img)
    
    # Convert to RGB if necessary (handles RGBA, CMYK, etc.)
    if img.mode in ('RGBA', 'LA', 'P'):
        # Create a white background for transparent images
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Resize image if it's larger than max_size
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # Save the processed image
    output = BytesIO()
    img.save(output, format='JPEG', quality=quality, optimize=True)
    output.seek(0)
    
    return ContentFile(output.getvalue())


def create_thumbnail(image_file, size=None):
    """
    Create a thumbnail from an image file.
    
    Args:
        image_file: Django UploadedFile or image path
        size: Tuple (width, height) for thumbnail size
    
    Returns:
        Thumbnail as ContentFile
    """
    if not PILLOW_AVAILABLE:
        # If Pillow is not available, return None
        return None
    
    if size is None:
        size = getattr(settings, 'THUMBNAIL_SIZE', (300, 300))
    
    # Open the image
    if hasattr(image_file, 'read'):
        img = Image.open(image_file)
    else:
        # Assume it's a file path
        img = Image.open(image_file)
    
    # Fix orientation
    img = ImageOps.exif_transpose(img)
    
    # Convert to RGB if necessary
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Create thumbnail
    img.thumbnail(size, Image.Resampling.LANCZOS)
    
    # Save thumbnail
    output = BytesIO()
    quality = getattr(settings, 'IMAGE_QUALITY', 85)
    img.save(output, format='JPEG', quality=quality, optimize=True)
    output.seek(0)
    
    return ContentFile(output.getvalue())


def delete_image_file(file_path):
    """
    Safely delete an image file from storage.
    """
    if file_path and default_storage.exists(file_path):
        try:
            default_storage.delete(file_path)
        except Exception:
            # Log the error but don't raise - file cleanup shouldn't break the app
            pass


def get_image_dimensions(image_file):
    """
    Get dimensions of an image file.
    
    Returns:
        Tuple (width, height)
    """
    if not PILLOW_AVAILABLE:
        return None, None
        
    img = Image.open(image_file)
    return img.size


def process_uploaded_images(uploaded_images, product):
    """
    Process multiple uploaded images and create ProductImage instances.
    
    Args:
        uploaded_images: List of uploaded file objects
        product: Product instance to associate images with
    
    Returns:
        List of created ProductImage instances
    """
    from .models import ProductImage
    
    created_images = []
    
    for index, image_file in enumerate(uploaded_images):
        try:
            # Validate the image
            validate_image(image_file)
            
            # Process the main image
            processed_image = process_image(image_file)
            
            # Generate filename for processed image
            filename = generate_image_filename(None, image_file.name)
            
            # Save the processed image
            saved_path = default_storage.save(filename, processed_image)
            
            # Create thumbnail
            thumbnail = create_thumbnail(processed_image)
            thumbnail_filename = filename.replace('.', '_thumb.')
            thumbnail_path = default_storage.save(thumbnail_filename, thumbnail) if thumbnail else None
            
            # Get image dimensions
            width, height = get_image_dimensions(processed_image)
            
            # Create ProductImage instance
            product_image = ProductImage.objects.create(
                product=product,
                image=saved_path,
                thumbnail=thumbnail_path,
                width=width,
                height=height,
                file_size=processed_image.size if hasattr(processed_image, 'size') else image_file.size,
                order=index
            )
            
            created_images.append(product_image)
            
        except Exception as e:
            # If one image fails, continue with others but log the error
            print(f"Failed to process image {image_file.name}: {str(e)}")
            continue
    
    return created_images
