import PyPDF2
from PyPDF2.pdf import PageObject
from PyPDF2.xmp import XmpInformation
from pathlib import Path
from scrapdf.exceptions import (
    FileNotSupportedError,
    DecryptionFailedError,
)
from scrapdf.extraction.interfaces import PageText
from typing import Iterable, Any
import abc


class IPdfFileTextExtractor(abc.ABC):
    """
    Abstract Base class for different conversion
    strategies
    """

    @abc.abstractproperty
    def metadata(self) -> Any:
        """
        Access to the PDF document metadata
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_text(self) -> Iterable[PageText]:
        """
        Get text for each page in the document
        """
        raise NotImplementedError()


class TextPdfExtractor(object):
    """
    Converts a non-scanned (typed) PDF document to text
    """

    def __init__(self, pdf_file: Path, password: str = None) -> None:
        if "pdf" not in pdf_file.suffix:
            raise FileNotSupportedError()
        if not pdf_file.exists():
            raise FileNotFoundError()
        self.pdf = PyPDF2.PdfFileReader(str(pdf_file))
        if self.pdf.isEncrypted:
            if password is None:
                raise DecryptionFailedError("File is encrypted, but no password given")
            decryption_result = self.pdf.decrypt(password)
            if decryption_result == 0:
                raise DecryptionFailedError("Password is not correct")

    @property
    def metadata(self) -> XmpInformation:
        return self.pdf.xmpMetadata()

    def get_text(self) -> Iterable[PageText]:
        for i, page in enumerate(self.pdf.pages):
            page: PageObject
            yield PageText(page=(i + 1), text=page.extractText())
