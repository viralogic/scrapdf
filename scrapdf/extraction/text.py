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
from typing import Iterator, Any, Dict, Union, Optional
import abc
from io import StringIO
import pdf2image
import pytesseract
from PIL import Image
import tempfile


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
        self.num_pages = 0
        self.file_path = pdf_file
        self._password = password

    @abc.abstractmethod
    def __iter__(self) -> Iterator[PageText]:
        """
        Get text for each page in the document
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def __next__(self) -> PageText:
        """
        Abstract next implementation
        """
        raise NotImplementedError()

    @abc.abstractproperty
    def pages(self) -> Iterator[Any]:
        """
        Pages in the PDF document
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
        self._file_stream = open(pdf_file, "rb")
        parser = PDFParser(self._file_stream)
        self.pdf_doc = PDFDocument(parser=parser, password=password)
        self._pages = None

    @property
    def pages(self) -> Iterator[Any]:
        if self._pages is None:
            self._pages = PDFPage.get_pages(self._file_stream, password=self._password)
        return self._pages

    def __extract_page_text(self, page: PDFPage) -> str:
        resource_manager = PDFResourceManager(caching=True)
        with StringIO() as output:
            device = TextConverter(
                resource_manager, output, codec="utf-8", laparams=LAParams()
            )
            interpreter = PDFPageInterpreter(resource_manager, device)
            interpreter.process_page(page)
            return output.getvalue()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        self._file_stream.close()

    def __iter__(self) -> Iterator[PageText]:
        return self

    def __next__(self) -> PageText:
        self.num_pages += 1
        page = next(self.pages)
        text = self.__extract_page_text(page)
        if text == PdfCharacters.FORM_FEED:
            raise ParsingFailedError(
                f"No text found on page {self.num_pages + 1}. Could this be a scanned PDF?"  # noqa E501
            )
        return PageText(page=self.num_pages, text=text)

    @property
    def metadata(self) -> Optional[Dict[str, str]]:
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
        self.__temp_dir = tempfile.TemporaryDirectory()
        self.output_path = Path(self.__temp_dir.name)

    @property
    def pages(self) -> Iterator[Any]:
        if self._pages is None:
            self._pages = iter(
                pdf2image.convert_from_path(
                    pdf_path=self.file_path,
                    userpw=self._password if self._password is not None else None,
                    output_folder=self.output_path,
                )
            )
        return self._pages

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        super(OcrPdfExtractor, self).__exit__(
            exception_type, exception_value, exception_traceback
        )
        if self.output_path.exists():
            self.__temp_dir.cleanup()

    def __extract_page_text(self, image: Image) -> Union[bytes, str]:
        result = pytesseract.image_to_string(image)
        return result

    def __iter__(self) -> Iterator[PageText]:
        return self

    def __next__(self) -> PageText:
        self.num_pages += 1
        page = next(self.pages)
        text = self.__extract_page_text(page)
        return PageText(page=self.num_pages, text=text)
