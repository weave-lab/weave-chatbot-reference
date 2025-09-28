import re
from typing import List, Optional


class MarkdownChunker:
    """Markdown chunker that splits Markdown text using header-aware chunking."""

    def __init__(self, chunk_size: int = 6000, overlap: int = 200):
        """
        Initialize the Markdown chunker.

        Args:
            chunk_size (int): The maximum size of each text chunk in characters. Defaults to 6000.
            overlap (int): The number of overlapping characters between consecutive chunks. Defaults to 200.
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str) -> List[str]:
        """
        Chunk text into smaller pieces using header-aware chunking for Markdown.

        This method:
        1. First splits by headers (# ## ###) to preserve logical document structure
        2. Handles initial content without headers as a single section
        3. Further chunks large sections if they exceed chunk_size
        4. Maintains context overlap between chunks

        Args:
            text (str): The text to chunk

        Returns:
            List[str]: List of text chunks
        """
        chunks = []

        # Split by headers while preserving the header with its content
        # This regex matches lines starting with 1-6 # symbols
        header_pattern = r"^(#{1,6}\s+.*)$"
        lines = text.split("\n")

        current_section: list[str] = []
        current_header: str | None = None

        for line in lines:
            header_match = re.match(header_pattern, line, re.MULTILINE)

            if header_match:
                # Process the previous section before starting a new one
                if current_section:
                    section_text = "\n".join(current_section).strip()
                    if section_text:
                        section_chunks = self._chunk_section(
                            section_text, current_header
                        )
                        chunks.extend(section_chunks)

                # Start new section with this header
                current_header = line.strip()
                current_section = [line]
            else:
                current_section.append(line)

        # Process the final section
        if current_section:
            section_text = "\n".join(current_section).strip()
            if section_text:
                section_chunks = self._chunk_section(section_text, current_header)
                chunks.extend(section_chunks)

        return chunks

    def _chunk_section(
        self, section_text: str, header: Optional[str] = None
    ) -> List[str]:
        """
        Chunk a single section, respecting the chunk_size limit.
        If a section is too large, it will be split while trying to preserve context.

        Args:
            section_text (str): The text of the section to chunk
            header (str, optional): The header of this section for context

        Returns:
            List[str]: List of chunks for this section
        """
        chunks = []

        # If section is small enough, return as single chunk
        if len(section_text) <= self.chunk_size:
            return [section_text]

        # For large sections, we need to split further
        # Try to split by paragraphs first (double newlines)
        paragraphs = section_text.split("\n\n")

        current_chunk = ""

        for para in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(para) + 2 > self.chunk_size:  # +2 for \n\n
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())

                    # Start new chunk with overlap if there's a previous chunk
                    if header and chunks:
                        # Include header in new chunk for context
                        current_chunk = header + "\n\n"
                    else:
                        current_chunk = ""

                # If single paragraph is too large, split it by sentences or characters
                if len(para) > self.chunk_size:
                    para_chunks = self._split_large_paragraph(para, header)
                    chunks.extend(para_chunks)
                else:
                    current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    current_chunk += para + "\n\n"
                else:
                    current_chunk = para + "\n\n"

        # Add final chunk if it has content
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _split_large_paragraph(
        self, paragraph: str, header: Optional[str] = None
    ) -> List[str]:
        """
        Split a large paragraph that exceeds chunk_size.
        Falls back to character-based chunking with overlap.

        Args:
            paragraph (str): The paragraph to split
            header (str, optional): The header for context

        Returns:
            List[str]: List of chunks for this paragraph
        """
        chunks = []
        start = 0

        while start < len(paragraph):
            end = start + self.chunk_size

            # If we have a header and this isn't the first chunk, include it for context
            chunk_prefix = ""
            if header and start > 0:
                chunk_prefix = header + "\n\n"
                # Adjust end to account for header length
                end = start + self.chunk_size - len(chunk_prefix)

            chunk = paragraph[start:end]

            # Try to end at a sentence boundary if possible
            if end < len(paragraph):
                sentence_endings = [". ", ".\n", "! ", "!\n", "? ", "?\n"]
                for ending in sentence_endings:
                    last_sentence = chunk.rfind(ending)
                    if (
                        last_sentence > len(chunk) * 0.5
                    ):  # Only if it's in the latter half
                        chunk = paragraph[start : start + last_sentence + 1]
                        break

            full_chunk = chunk_prefix + chunk
            chunks.append(full_chunk.strip())

            # Move start position with overlap
            start += len(chunk) - self.overlap

        return chunks
