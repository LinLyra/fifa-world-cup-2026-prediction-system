import { useCallback, useEffect, useRef, useState } from "react";

const MIN_SCALE = 0.35;
const MAX_SCALE = 1.35;
const DEFAULT_SCALE = 0.8;

type Props = {
  children: React.ReactNode;
  height?: number;
  onReady?: () => void;
};

export default function BracketZoomCanvas({ children, height = 560, onReady }: Props) {
  const canvasRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const spacerRef = useRef<HTMLDivElement>(null);
  const scaleRef = useRef(DEFAULT_SCALE);
  const [scale, setScale] = useState(DEFAULT_SCALE);
  const [pctInput, setPctInput] = useState(Math.round(DEFAULT_SCALE * 100));
  const dragRef = useRef({ active: false, sx: 0, sy: 0, sl: 0, st: 0 });

  const applyScale = useCallback((next: number) => {
    const s = Math.max(MIN_SCALE, Math.min(MAX_SCALE, next));
    scaleRef.current = s;
    setScale(s);
    setPctInput(Math.round(s * 100));
    const stage = stageRef.current;
    const spacer = spacerRef.current;
    if (stage) stage.style.transform = `scale(${s})`;
    if (spacer && stage) {
      spacer.style.width = `${Math.ceil(stage.offsetWidth * s)}px`;
      spacer.style.height = `${Math.ceil(stage.offsetHeight * s)}px`;
    }
  }, []);

  const zoomAt = useCallback((clientX: number, clientY: number, delta: number) => {
    const canvas = canvasRef.current;
    const stage = stageRef.current;
    if (!canvas || !stage) return;
    const rect = canvas.getBoundingClientRect();
    const mx = clientX - rect.left + canvas.scrollLeft;
    const my = clientY - rect.top + canvas.scrollTop;
    const oldScale = scaleRef.current;
    const newScale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, oldScale + delta));
    if (newScale === oldScale) return;
    const ratio = newScale / oldScale;
    applyScale(newScale);
    canvas.scrollLeft = Math.max(0, mx * ratio - (clientX - rect.left));
    canvas.scrollTop = Math.max(0, my * ratio - (clientY - rect.top));
  }, [applyScale]);

  const viewportCenter = () => {
    const canvas = canvasRef.current;
    if (!canvas) return [0, 0] as const;
    const rect = canvas.getBoundingClientRect();
    return [rect.left + rect.width / 2, rect.top + rect.height / 2] as const;
  };

  const fitView = useCallback(() => {
    const canvas = canvasRef.current;
    const stage = stageRef.current;
    const spacer = spacerRef.current;
    if (!canvas || !stage || !spacer) return;
    const cw = canvas.clientWidth;
    const ch = canvas.clientHeight;
    stage.style.transform = "scale(1)";
    spacer.style.width = `${stage.offsetWidth}px`;
    spacer.style.height = `${stage.offsetHeight}px`;
    const sw = stage.offsetWidth;
    const sh = stage.offsetHeight;
    let next = Math.min(cw / sw, ch / sh, 0.95);
    next = Math.max(MIN_SCALE, next);
    applyScale(next);
    canvas.scrollLeft = Math.max(0, (spacer.offsetWidth - cw) / 2);
    canvas.scrollTop = Math.max(0, (spacer.offsetHeight - ch) / 2);
  }, [applyScale]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      e.stopPropagation();
      const delta = e.deltaY < 0 ? 0.06 : -0.06;
      zoomAt(e.clientX, e.clientY, delta);
    };

    canvas.addEventListener("wheel", onWheel, { passive: false });

    const onMove = (e: MouseEvent) => {
      if (!dragRef.current.active) return;
      canvas.scrollLeft = dragRef.current.sl - (e.clientX - dragRef.current.sx);
      canvas.scrollTop = dragRef.current.st - (e.clientY - dragRef.current.sy);
    };
    const onUp = () => {
      dragRef.current.active = false;
      canvas.classList.remove("dragging");
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);

    const t = window.setTimeout(() => {
      fitView();
      onReady?.();
    }, 120);

    return () => {
      canvas.removeEventListener("wheel", onWheel);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
      window.clearTimeout(t);
    };
  }, [fitView, onReady, zoomAt]);

  useEffect(() => {
    const stage = stageRef.current;
    const spacer = spacerRef.current;
    if (stage) stage.style.transform = `scale(${scale})`;
    if (spacer && stage) {
      spacer.style.width = `${Math.ceil(stage.offsetWidth * scale)}px`;
      spacer.style.height = `${Math.ceil(stage.offsetHeight * scale)}px`;
      const canvas = canvasRef.current;
      if (canvas) {
        const cw = canvas.clientWidth;
        const ch = canvas.clientHeight;
        canvas.scrollLeft = Math.max(0, (spacer.offsetWidth - cw) / 2);
        canvas.scrollTop = Math.max(0, (spacer.offsetHeight - ch) / 2);
      }
    }
  }, [scale, children]);

  const setScalePercent = (pct: number) => {
    const target = Math.max(MIN_SCALE, Math.min(MAX_SCALE, pct / 100));
    const [cx, cy] = viewportCenter();
    zoomAt(cx, cy, target - scaleRef.current);
  };

  return (
    <div className="bracket-zoom-root">
      <div className="bracket-zoom-toolbar">
        <button
          type="button"
          onClick={() => {
            const [cx, cy] = viewportCenter();
            zoomAt(cx, cy, -0.08);
          }}
          title="Zoom out"
        >
          −
        </button>
        <input
          type="number"
          className="bracket-zoom-pct"
          min={35}
          max={135}
          value={pctInput}
          onChange={(e) => setPctInput(parseInt(e.target.value, 10) || 80)}
          onKeyDown={(e) => {
            if (e.key === "Enter") setScalePercent(pctInput);
          }}
          onBlur={() => setScalePercent(pctInput)}
          title="Zoom %"
        />
        <span className="text-xs text-slate-400">%</span>
        <button
          type="button"
          onClick={() => {
            const [cx, cy] = viewportCenter();
            zoomAt(cx, cy, 0.08);
          }}
          title="Zoom in"
        >
          +
        </button>
        <button type="button" onClick={fitView} title="Fit to view">
          Fit
        </button>
        <span className="text-xs text-slate-500">Wheel = zoom · Drag = pan · Fit = center</span>
      </div>

      <div
        ref={canvasRef}
        className="bracket-zoom-canvas"
        style={{ height }}
        onMouseDown={(e) => {
          if (e.button !== 0) return;
          const canvas = canvasRef.current;
          if (!canvas) return;
          dragRef.current = {
            active: true,
            sx: e.clientX,
            sy: e.clientY,
            sl: canvas.scrollLeft,
            st: canvas.scrollTop,
          };
          canvas.classList.add("dragging");
          e.preventDefault();
        }}
      >
        <div ref={spacerRef} className="bracket-zoom-spacer">
          <div ref={stageRef} className="bracket-zoom-stage">
            <div className="bracket-zoom-inner">{children}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
