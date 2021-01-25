import unittest
from pathlib import Path

from pdfminer.pdfdocument import PDFPasswordIncorrect
from scrapdf.extraction.text import OcrPdfExtractor, TextPdfExtractor
from scrapdf.exceptions import FileNotSupportedError, ParsingFailedError
from PyPDF2 import PdfFileWriter, PdfFileReader


class TextPdfExtractorTests(unittest.TestCase):
    """
    Tests for extracting non-scanned documents
    """

    def _create_encrypted_file(self, in_doc: Path) -> Path:
        encrypted_file_path = Path(
            "tests/files/pdf/text/A Block-sorting Lossless Data Compression Algorithm - May 10th, 1994 (SRC-RR-124)_encrypted.pdf"  # noqa E501
        )
        writer = PdfFileWriter()
        reader = PdfFileReader(str(in_doc))
        for page in reader.pages:
            writer.addPage(page)
        writer.encrypt("correctpassword")
        with open(encrypted_file_path, "wb") as f:
            writer.write(f)
        return encrypted_file_path

    def test_wrong_extension(self) -> None:
        doc = Path(
            "tests/files/pdf/text/A Block-sorting Lossless Data Compression Algorithm - May 10th, 1994 (SRC-RR-124).txt"  # noqa E501
        )
        self.assertRaises(FileNotSupportedError, TextPdfExtractor, doc)

    def test_not_found(self) -> None:
        doc = Path(
            "tests/files/pdf/not_here/A Block-sorting Lossless Data Compression Algorithm - May 10th, 1994 (SRC-RR-124).pdf"  # noqa E501
        )
        self.assertRaises(FileNotFoundError, TextPdfExtractor, doc)

    def test_decryption_no_password(self) -> None:
        doc = Path(
            "tests/files/pdf/text/A Block-sorting Lossless Data Compression Algorithm - May 10th, 1994 (SRC-RR-124).pdf"  # noqa E501
        )
        encrypted_doc = self._create_encrypted_file(doc)
        self.assertRaises(PDFPasswordIncorrect, TextPdfExtractor, encrypted_doc)

        encrypted_doc.unlink()

    def test_decryption_wrong_password(self) -> None:
        doc = Path(
            "tests/files/pdf/text/A Block-sorting Lossless Data Compression Algorithm - May 10th, 1994 (SRC-RR-124).pdf"  # noqa E501
        )
        encrypted_doc = self._create_encrypted_file(doc)
        self.assertRaises(
            PDFPasswordIncorrect,
            TextPdfExtractor,
            encrypted_doc,
            "wrongpassword",
        )

        encrypted_doc.unlink()

    def test_decryption_correct_password(self) -> None:
        doc = Path(
            "tests/files/pdf/text/A Block-sorting Lossless Data Compression Algorithm - May 10th, 1994 (SRC-RR-124).pdf"  # noqa E501
        )
        encrypted_doc = self._create_encrypted_file(doc)
        decrypted_pdf = TextPdfExtractor(encrypted_doc, "correctpassword")
        for page in decrypted_pdf:
            self.assertTrue(len(page.text) > 0)

        encrypted_doc.unlink()

    def test_iterate_pages(self) -> None:
        doc = Path(
            "tests/files/pdf/text/A Block-sorting Lossless Data Compression Algorithm - May 10th, 1994 (SRC-RR-124).pdf"  # noqa E501
        )
        pdf = TextPdfExtractor(doc)
        for page in pdf:
            self.assertTrue(len(page.text) > 0)

    def test_metadata(self) -> None:
        doc = Path(
            "tests/files/pdf/text/A Block-sorting Lossless Data Compression Algorithm - May 10th, 1994 (SRC-RR-124).pdf"  # noqa E501
        )
        pdf = TextPdfExtractor(doc)
        self.assertIsNotNone(pdf.metadata)
        self.assertEqual(
            b"A block-sorting lossless data compression algorithm",
            pdf.metadata["Title"],
        )

    def test_scanned_pdf(self) -> None:
        doc = Path("tests/files/pdf/images/PublicWaterMassMailing.pdf")
        pdf = TextPdfExtractor(doc)
        self.assertRaises(ParsingFailedError, list, pdf)


class OcrPdfExtractorTests(unittest.TestCase):
    """
    Tests for scanned documents
    """

    def test_page_text(self) -> None:
        doc = Path("tests/files/pdf/images/PublicWaterMassMailing.pdf")
        pdf = OcrPdfExtractor(doc)
        for page in pdf:
            self.assertTrue(len(page.text) > 0)
