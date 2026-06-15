import sys
from pathlib import Path
path = Path(r'C:\Users\lenovo\Desktop\xeno\Xeno Engineering Internship Assignment - 2026.pdf')
try:
    from PyPDF2 import PdfReader
except Exception as e:
    print('MISSING', e)
    sys.exit(1)
reader = PdfReader(path)
for idx,page in enumerate(reader.pages,1):
    print('--- PAGE %d ---' % idx)
    print(page.extract_text())