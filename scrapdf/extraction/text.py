from pdfminer.converter import TextConverter
from pathlib import Path

from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from scrapdf.exceptions import (
    FileNotSupportedError,
)
from scrapdf.extraction.interfaces import PageText
from typing import Iterable, Any, Dict
import abc
from io import StringIO


class IPdfFileTextExtractor(abc.ABC):
    """
    Abstract Base class for different conversion
    strategies
    """

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


class TextPdfExtractor(object):
    """
    Converts a non-scanned (typed) PDF document to text
    """

    def __init__(self, pdf_file: Path, password: str = "") -> None:
        if "pdf" not in pdf_file.suffix:
            raise FileNotSupportedError()
        if not pdf_file.exists():
            raise FileNotFoundError()
        self.pdf_doc = None
        with open(pdf_file, "rb") as f:
            parser = PDFParser(f)
            self.pdf_doc = PDFDocument(parser=parser, password=password)
        self.file_path = pdf_file
        self.__password = password

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback) -> None:
        if not self.pdf_file.closed:
            self.pdf_file.close()

    def __extract_page_text(self, page: PDFPage) -> StringIO:
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
            for i, page in enumerate(PDFPage.get_pages(f, password=self.__password)):
                text = self.__extract_page_text(page)
                yield PageText(page=(i + 1), text=text)

    @property
    def metadata(self) -> Dict[str, str]:
        if len(self.pdf_doc.info) == 1:
            return self.pdf_doc.info[0]
        return None
