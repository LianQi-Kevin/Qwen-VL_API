import logging
import os
import re
from base64 import b64decode, b64encode
from uuid import uuid4

from requests import get as requests_get

from routers.files import check_file_exists, FILE_CACHE_DIR


def img_to_base64(img_path: str) -> str:
    """Convert the image to base64."""
    with open(img_path, 'rb') as f:
        return b64encode(f.read()).decode()


def download_img_from_url(url: str, save_dir: str = FILE_CACHE_DIR if FILE_CACHE_DIR else "") -> str:
    """
    Download the image from the url.

    :param url: The image url.
    :param save_dir: The image save directory.
    :return: The image save path.
    """
    match = re.match(r'^data:(?P<mime_type>image/.+);base64,(?P<base64_data>.+)', url)
    if match:
        # base64 data
        img_data = b64decode(match.group('base64_data'))
        extension = match.group('mime_type').split('/')[1]
    elif 'seetacloud.com' in url:
        # todo: 待优化本地匹配逻辑
        # 针对 autodl 的 'seetacloud.com' 进行特殊处理
        # 解析url中的路径部分，匹配file_id
        file_id = url.split('/')[-2]
        check_file_exists(file_id)
        return os.path.join(FILE_CACHE_DIR, file_id)
    else:
        # url
        response = requests_get(url)
        img_data = response.content
        extension = response.headers['content-type'].split('/')[1]

    # save image
    img_path = os.path.join(save_dir, f"image_{uuid4().hex[:8]}.{extension}")
    with open(img_path, 'wb') as f:
        f.write(img_data)
    logging.debug(f"Save Image, path: {img_path}")
    return img_path
