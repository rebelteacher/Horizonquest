import { useEffect, useState, useCallback } from "react";
import { ChevronLeft, ChevronRight, Maximize2, X, Download } from "lucide-react";

export const SlideCarousel = ({ images = [], title = "Teaching slides", deckUrl }) => {
  const [i, setI] = useState(0);
  const [full, setFull] = useState(false);
  const total = images.length;

  const go = useCallback((d) => setI((p) => Math.min(total - 1, Math.max(0, p + d))), [total]);

  useEffect(() => { setI(0); }, [images]);
  useEffect(() => {
    // Preload neighbouring slides so navigation feels instant.
    [i + 1, i - 1].forEach((n) => {
      if (n >= 0 && n < total) { const img = new Image(); img.src = images[n]; }
    });
  }, [i, images, total]);
  useEffect(() => {
    if (!full) return;
    const onKey = (e) => {
      if (e.key === "ArrowRight") go(1);
      else if (e.key === "ArrowLeft") go(-1);
      else if (e.key === "Escape") setFull(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [full, go]);

  if (!total) return null;

  const Stage = ({ big }) => (
    <div className={`relative w-full ${big ? "h-full" : "aspect-video"} bg-black rounded-lg overflow-hidden select-none`} data-testid="slide-carousel-stage">
      <img src={images[i]} alt={`${title} — slide ${i + 1}`} className="w-full h-full object-contain" draggable={false} data-testid="slide-carousel-image" />
      {i > 0 && (
        <button data-testid="slide-prev-btn" onClick={() => go(-1)} aria-label="Previous slide"
          className="absolute left-2 top-1/2 -translate-y-1/2 w-9 h-9 rounded-full bg-black/50 hover:bg-black/70 text-white flex items-center justify-center backdrop-blur transition-colors">
          <ChevronLeft className="w-5 h-5" />
        </button>
      )}
      {i < total - 1 && (
        <button data-testid="slide-next-btn" onClick={() => go(1)} aria-label="Next slide"
          className="absolute right-2 top-1/2 -translate-y-1/2 w-9 h-9 rounded-full bg-black/50 hover:bg-black/70 text-white flex items-center justify-center backdrop-blur transition-colors">
          <ChevronRight className="w-5 h-5" />
        </button>
      )}
      <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex items-center gap-2 px-3 py-1 rounded-full bg-black/50 backdrop-blur">
        <span className="font-mono-data text-xs text-white" data-testid="slide-counter">{i + 1} / {total}</span>
      </div>
      <div className="absolute top-2 right-2 flex items-center gap-1.5">
        {deckUrl && (
          <a href={deckUrl} download data-testid="slide-download-btn" title="Download deck (.pptx)"
            className="w-8 h-8 rounded-full bg-black/50 hover:bg-black/70 text-white flex items-center justify-center backdrop-blur transition-colors">
            <Download className="w-4 h-4" />
          </a>
        )}
        <button data-testid={big ? "slide-exit-fullscreen-btn" : "slide-fullscreen-btn"} onClick={() => setFull(!big)} title={big ? "Exit" : "Fullscreen"}
          className="w-8 h-8 rounded-full bg-black/50 hover:bg-black/70 text-white flex items-center justify-center backdrop-blur transition-colors">
          {big ? <X className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
        </button>
      </div>
    </div>
  );

  return (
    <>
      <Stage big={false} />
      {full && (
        <div className="fixed inset-0 z-[100] bg-black/95 flex items-center justify-center p-4 sm:p-10" data-testid="slide-fullscreen-overlay" onClick={(e) => { if (e.target === e.currentTarget) setFull(false); }}>
          <div className="w-full max-w-6xl aspect-video"><Stage big /></div>
        </div>
      )}
    </>
  );
};
