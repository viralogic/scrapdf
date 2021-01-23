import unittest
from pathlib import Path
from scrapdf.extraction.text import TextPdfExtractor
from scrapdf.exceptions import (
    DecryptionFailedError,
    FileNotSupportedError,
)
from PyPDF2 import PdfFileWriter, PdfFileReader


class TextPdfExtractorTests(unittest.TestCase):
    """
    Tests for extracting non-scanned documents
    """

    def setUp(self) -> None:
        self.encrypted_file_path = Path(
            "tests/files/pdf/text/A Block-sorting Lossless Data Compression Algorithm - May 10th, 1994 (SRC-RR-124)_encrypted.pdf" # noqa E501
        )

    def _create_encrypted_file(self, in_doc: Path) -> Path:
        writer = PdfFileWriter()
        reader = PdfFileReader(str(in_doc))
        for page in reader.pages:
            writer.addPage(page)
        writer.encrypt("correctpassword")
        with open(self.encrypted_file_path, "wb") as f:
            writer.write(f)
        return self.encrypted_file_path

    def test_wrong_extension(self) -> None:
        doc = Path(
            "tests/files/pdf/text/A Block-sorting Lossless Data Compression Algorithm - May 10th, 1994 (SRC-RR-124).txt" # noqa E501
        )
        self.assertRaises(FileNotSupportedError, TextPdfExtractor, doc)

    def test_not_found(self) -> None:
        doc = Path(
            "tests/files/pdf/not_here/A Block-sorting Lossless Data Compression Algorithm - May 10th, 1994 (SRC-RR-124).pdf" # noqa E501
        )
        self.assertRaises(FileNotFoundError, TextPdfExtractor, doc)

    def test_decryption_no_password(self) -> None:
        doc = Path(
            "tests/files/pdf/text/A Block-sorting Lossless Data Compression Algorithm - May 10th, 1994 (SRC-RR-124).pdf" # noqa E501
        )
        encrypted_doc = self._create_encrypted_file(doc)
        self.assertRaises(DecryptionFailedError, TextPdfExtractor, encrypted_doc)

    def test_decryption_wrong_password(self) -> None:
        doc = Path(
            "tests/files/pdf/text/A Block-sorting Lossless Data Compression Algorithm - May 10th, 1994 (SRC-RR-124).pdf" # noqa E501
        )
        encrypted_doc = self._create_encrypted_file(doc)
        self.assertRaises(
            DecryptionFailedError,
            TextPdfExtractor,
            encrypted_doc,
            "wrongpassword",
        )

    def test_decryption_correct_password(self) -> None:
        doc = Path(
            "tests/files/pdf/text/A Block-sorting Lossless Data Compression Algorithm - May 10th, 1994 (SRC-RR-124).pdf" # noqa E501
        )
        encrypted_doc = self._create_encrypted_file(doc)
        decrypted_pdf = TextPdfExtractor(encrypted_doc, "correctpassword")
        self.assertTrue(decrypted_pdf.pdf.numPages > 0)

    def tearDown(self) -> None:
        if self.encrypted_file_path.exists():
            self.encrypted_file_path.unlink()
