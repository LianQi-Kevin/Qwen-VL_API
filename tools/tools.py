import base64


def img_to_base64(img_path: str) -> str:
    """Convert the image to base64."""
    with open(img_path, 'rb') as f:
        img = f.read()
    return base64.b64encode(img).decode()


def base64_to_img(b64: str, img_path: str) -> None:
    """Save the base64 image to the img_path."""
    with open(img_path, 'wb') as f:
        f.write(base64.b64decode(b64))
    return None
