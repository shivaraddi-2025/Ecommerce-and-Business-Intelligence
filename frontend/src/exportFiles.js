const downloadBlob = (blob, filename) => {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};

const normalizeValue = (value) => {
  if (value === null || value === undefined) return '';
  return typeof value === 'object' ? JSON.stringify(value) : String(value);
};

const getHeaders = (rows) => Array.from(rows.reduce((headers, row) => {
  Object.keys(row || {}).forEach((key) => headers.add(key));
  return headers;
}, new Set()));

const downloadExcel = async (rows, filename) => {
  const { default: ExcelJS } = await import('exceljs');
  const workbook = new ExcelJS.Workbook();
  workbook.creator = 'Nexus Commerce BI';
  workbook.created = new Date();
  const worksheet = workbook.addWorksheet('Export');
  const headers = getHeaders(rows);
  worksheet.addRow(headers);
  rows.forEach((row) => worksheet.addRow(headers.map((header) => {
    const value = row?.[header];
    if (value === null || value === undefined) return '';
    if (typeof value === 'object') return JSON.stringify(value);
    if (typeof value === 'string' && /^[=+\-@]/.test(value)) return `'${value}`;
    return value;
  })));
  worksheet.columns.forEach((column) => {
    const header = headers[column.number - 1];
    const sampleLength = Math.max(0, ...rows.slice(0, 100).map((row) => (
      normalizeValue(row?.[header]).length
    )));
    column.width = Math.min(Math.max(12, header.length, sampleLength) + 2, 40);
  });
  worksheet.getRow(1).font = { bold: true };
  worksheet.views = [{ state: 'frozen', ySplit: 1 }];
  const buffer = await workbook.xlsx.writeBuffer();
  downloadBlob(new Blob([buffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  }), filename);
};

const downloadPdf = async (rows, filename, title) => {
  const [{ jsPDF }, { default: autoTable }] = await Promise.all([
    import('jspdf'),
    import('jspdf-autotable'),
  ]);
  const headers = getHeaders(rows);
  const pdf = new jsPDF({ orientation: 'landscape', unit: 'pt', format: 'a4' });
  pdf.setFontSize(16);
  pdf.text(title, 40, 36);
  pdf.setFontSize(9);
  pdf.text(`Generated ${new Date().toLocaleString()} · ${rows.length.toLocaleString('en-US')} rows`, 40, 52);
  autoTable(pdf, {
    startY: 64,
    head: [headers],
    body: rows.map((row) => headers.map((header) => normalizeValue(row?.[header]))),
    styles: { fontSize: 7, cellPadding: 4, overflow: 'linebreak' },
    headStyles: { fillColor: [36, 52, 79] },
    margin: { left: 40, right: 40 },
    horizontalPageBreak: true,
    horizontalPageBreakRepeat: 0,
  });
  downloadBlob(pdf.output('blob'), filename);
};

export const downloadRows = async (rows, filename, format, title) => {
  if (format === 'xlsx') {
    await downloadExcel(rows, filename);
    return;
  }
  if (format === 'pdf') {
    await downloadPdf(rows, filename, title);
    return;
  }
  throw new Error(`Unsupported export format: ${format}`);
};
