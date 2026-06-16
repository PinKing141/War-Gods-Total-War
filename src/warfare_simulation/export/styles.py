from openpyxl.styles import Font, PatternFill, Alignment

# Shared styling constants for the campaign export
HEADER_FONT = Font(bold=True, color="FFFFFF")
HEADER_FILL = PatternFill(start_color="333333", end_color="333333", fill_type="solid")
CENTER_ALIGN = Alignment(horizontal="center", vertical="center")