from abc import ABC, abstractmethod
from typing import List, Any, Optional
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.utils import get_column_letter

from warfare_simulation.export.styles import HEADER_FONT, HEADER_FILL, CENTER_ALIGN

class SheetGenerator(ABC):
    @property
    @abstractmethod
    def sheet_name(self) -> str:
        pass

    @abstractmethod
    def generate(self, workbook: Workbook) -> Worksheet:
        pass

    def _write_table(self, ws: Worksheet, headers: List[str], data: List[List[Any]], column_widths: Optional[List[int]] = None):
        """Helper method to stamp headers, apply styles, and write data rows."""
        ws.append(headers)
        
        # Style headers
        for col_num, cell in enumerate(ws[1], 1):
            cell.font = HEADER_FONT
            cell.fill = HEADER_FILL
            cell.alignment = CENTER_ALIGN
            
            # Apply custom column widths if provided, else default to 18
            width = column_widths[col_num - 1] if column_widths and col_num <= len(column_widths) else 18
            ws.column_dimensions[get_column_letter(col_num)].width = width
            
        # Write all data rows
        for row in data:
            ws.append(row)