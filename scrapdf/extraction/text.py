from pdfminer.converter import TextConverter
from pathlib import Path

from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from scrapdf.exceptions import (
    FileNotSupportedError,
    ParsingFailedError,
)
from scrapdf.extraction.interfaces import PageText
from scrapdf.extraction.pdf_chars import PdfCharacters
from typing import Iterable, Any, Dict
import abc
from io import StringIO
import pdf2image
import pytesseract
from PIL import Image
import uuid


class IPdfFileTextExtractor(abc.ABC):
    """
    Abstract Base class for different conversion
    strategies
    """

    def __init__(self, pdf_file: Path, password: str = "") -> None:
        if "pdf" not in pdf_file.suffix:
            raise FileNotSupportedError()
        if not pdf_file.exists():
            raise FileNotFoundError()
        self.file_path = pdf_file
        self._password = password

    @abc.abstractmethod
    def __iter__(self) -> Iterable[PageText]:
        """
        Get text for each page in the document
        """
        raise NotImplementedError()

    @abc.abstractproperty
    def metadata(self) -> Any:
        """
        Access to the PDF document metadata
        """
        raise NotImplementedError()


class TextPdfExtractor(IPdfFileTextExtractor):
    """
    Converts a non-scanned (typed) PDF document to text
    """

    def __init__(self, pdf_file: Path, password: str = "") -> None:
        super(TextPdfExtractor, self).__init__(pdf_file, password)
        self.pdf_doc = None
        with open(pdf_file, "rb") as f:
            parser = PDFParser(f)
            self.pdf_doc = PDFDocument(parser=parser, password=password)

    def __extract_page_text(self, page: PDFPage) -> str:
        resource_manager = PDFResourceManager(caching=True)
        with StringIO() as output:
            device = TextConverter(
                resource_manager, output, codec="utf-8", laparams=LAParams()
            )
            interpreter = PDFPageInterpreter(resource_manager, device)
            interpreter.process_page(page)
            return output.getvalue()

    def __iter__(self) -> Iterable[PageText]:
        with open(self.file_path, "rb") as f:
            for i, page in enumerate(PDFPage.get_pages(f, password=self._password)):
                text = self.__extract_page_text(page)
                if text == PdfCharacters.FORM_FEED:
                    raise ParsingFailedError(
                        f"No text found on page {i + 1}. Could this be a scanned PDF?"
                    )
                yield PageText(page=(i + 1), text=text)

    @property
    def metadata(self) -> Dict[str, str]:
        if len(self.pdf_doc.info) == 1:
            return self.pdf_doc.info[0]
        return None


class OcrPdfExtractor(TextPdfExtractor):
    """
    Converts scanned PDF document to text.
    More generic than using a text extraction
    """

    def __init__(self, pdf_file: Path, password: str = "") -> None:
        super(OcrPdfExtractor, self).__init__(pdf_file, password)
        self.output_path = Path(f"temp/{str(uuid.uuid4())}")
        self.output_path.mkdir(exist_ok=True, parents=True)

    def __extract_page_text(self, image: Image) -> str:
        result = pytesseract.image_to_string(image)
        return result

    def __iter__(self) -> Iterable[PageText]:
        images_from_path = pdf2image.convert_from_path(
            pdf_path=self.file_path,
            userpw=self._password if self._password is not None else None,
            output_folder=self.output_path,
        )
        for i, image in enumerate(images_from_path):
            text = self.__extract_page_text(image)
            yield PageText(page=(i + 1), text=text)
