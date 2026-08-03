import jsPDF from "jspdf";
import html2canvas from "html2canvas";

async function nodeToCanvas(node) {
  return html2canvas(node, { scale: 2, backgroundColor: "#ffffff", logging: false, useCORS: true });
}

// Export a single DOM node to a portrait A4 PDF (multi-page if tall).
export async function exportNodeToPDF(node, filename = "horizonquest.pdf") {
  const canvas = await nodeToCanvas(node);
  const img = canvas.toDataURL("image/png");
  const pdf = new jsPDF({ orientation: "portrait", unit: "pt", format: "a4" });
  const pw = pdf.internal.pageSize.getWidth();
  const ph = pdf.internal.pageSize.getHeight();
  const iw = pw;
  const ih = (canvas.height * pw) / canvas.width;
  let heightLeft = ih;
  let position = 0;
  pdf.addImage(img, "PNG", 0, position, iw, ih);
  heightLeft -= ph;
  while (heightLeft > 0) {
    position -= ph;
    pdf.addPage();
    pdf.addImage(img, "PNG", 0, position, iw, ih);
    heightLeft -= ph;
  }
  pdf.save(filename);
}

// Export multiple nodes as one landscape page each (used for slides).
export async function exportNodesToPDF(nodes, filename = "slides.pdf") {
  const pdf = new jsPDF({ orientation: "landscape", unit: "pt", format: "a4" });
  const pw = pdf.internal.pageSize.getWidth();
  const ph = pdf.internal.pageSize.getHeight();
  for (let i = 0; i < nodes.length; i++) {
    const canvas = await nodeToCanvas(nodes[i]);
    const img = canvas.toDataURL("image/png");
    const ratio = Math.min(pw / canvas.width, ph / canvas.height);
    const iw = canvas.width * ratio;
    const ih = canvas.height * ratio;
    if (i > 0) pdf.addPage();
    pdf.addImage(img, "PNG", (pw - iw) / 2, (ph - ih) / 2, iw, ih);
  }
  pdf.save(filename);
}
