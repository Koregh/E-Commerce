import os
import uuid
from abc import ABC, abstractmethod
from typing import Optional
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from config.settings import settings
from core.exceptions.domain import UploadError


class IFileUploader(ABC):
    @abstractmethod
    def save(self, file: FileStorage) -> Optional[str]: ...

    @abstractmethod
    def delete(self, filename: str) -> None: ...


class LocalFileUploader(IFileUploader):
    """
    Salva arquivos no disco local com nome UUID para evitar
    colisões e path traversal.
    """

    def __init__(self, upload_folder: str, allowed_extensions: frozenset, max_bytes: int):
        self._folder = upload_folder
        self._allowed = allowed_extensions
        self._max_bytes = max_bytes
        os.makedirs(self._folder, exist_ok=True)

    def _is_allowed(self, filename: str) -> bool:
        return (
            "." in filename
            and filename.rsplit(".", 1)[1].lower() in self._allowed
        )

    def save(self, file: FileStorage) -> Optional[str]:
        if not file or not file.filename:
            return None

        if not self._is_allowed(file.filename):
            raise UploadError(
                f"Formato inválido. Permitidos: {', '.join(self._allowed)}"
            )

        # Checa tamanho lendo o stream sem guardar em memória toda
        file.stream.seek(0, 2)  # seek até o fim
        size = file.stream.tell()
        file.stream.seek(0)     # volta ao início

        if size > self._max_bytes:
            raise UploadError(
                f"Arquivo muito grande. Máximo: {settings.MAX_UPLOAD_MB}MB"
            )

        ext = secure_filename(file.filename).rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        file.save(os.path.join(self._folder, filename))
        return filename

    def delete(self, filename: str) -> None:
        path = os.path.join(self._folder, secure_filename(filename))
        if os.path.exists(path):
            os.remove(path)


# Instância padrão
file_uploader: IFileUploader = LocalFileUploader(
    upload_folder=settings.UPLOAD_FOLDER,
    allowed_extensions=settings.ALLOWED_EXTENSIONS,
    max_bytes=settings.max_upload_bytes,
)
