"""Image quality checking: blur detection and brightness validation."""

from io import BytesIO
from PIL import Image, ImageStat, ImageFilter


def check_image_quality(image_bytes: bytes) -> dict:
    """Check image quality and return results with warnings.

    Returns dict with:
        - ok: bool - whether the image passes all quality checks
        - blur_score: float - higher = sharper (threshold ~100)
        - brightness: float - average brightness 0-255
        - warnings: list[str] - human-readable warnings
    """
    img = Image.open(BytesIO(image_bytes)).convert("RGB")

    # Blur detection via Laplacian-like variance
    gray = img.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edge_stat = ImageStat.Stat(edges)
    blur_score = edge_stat.var[0]

    # Brightness
    stat = ImageStat.Stat(img)
    brightness = sum(stat.mean[:3]) / 3

    warnings = []
    if blur_score < 50:
        warnings.append("图片可能模糊，建议重新拍摄 (Image may be blurry)")
    if brightness < 40:
        warnings.append("图片过暗，建议在光线充足处拍摄 (Image is too dark)")
    if brightness > 240:
        warnings.append("图片过亮/过曝，建议调整光线 (Image is overexposed)")

    width, height = img.size
    if width < 300 or height < 300:
        warnings.append("图片分辨率过低，建议使用更高分辨率 (Resolution too low)")

    return {
        "ok": len(warnings) == 0,
        "blur_score": round(blur_score, 2),
        "brightness": round(brightness, 2),
        "width": width,
        "height": height,
        "warnings": warnings,
    }
