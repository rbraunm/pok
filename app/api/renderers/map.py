from __future__ import annotations

from typing import List, Tuple, Dict, Any, Optional, Callable
from PIL import Image, ImageDraw, ImageFont
import re, io, hashlib, threading

from applogging import get_logger
logger = get_logger(__name__)

# -------------------- Defaults --------------------

DEFAULT_PADDING_PX = 40
DEFAULT_LINE_WIDTH_PX = 3
DEFAULT_OVERLAY_DOT_RADIUS_PX = 6
DEFAULT_ARROW_SIZE_PX = 5            # small down-facing triangle
DEFAULT_FONT_PATH = "DejaVuSans-Bold.ttf"
DEFAULT_FONT_SIZE_PT = 18

# Orientation validated for EQ maps:
#   game (x,y) -> map (-y, -x)
#   flipX=False, flipY=True
DEFAULT_FLIP_X = False
DEFAULT_FLIP_Y = True

# -------------------- Internal state --------------------

_num_re = re.compile(r"-?\d+\.?\d*")

# Cache: ref_map_path -> (minX, maxX, minY, maxY)
_bounds_cache: Dict[str, Tuple[float, float, float, float]] = {}
_bounds_lock = threading.RLock()

# Lazy-loaded font
_font: Optional[ImageFont.FreeTypeFont] = None
_font_lock = threading.RLock()

# -------------------- Font & misc helpers --------------------

def _get_font() -> ImageFont.FreeTypeFont:
    global _font
    with _font_lock:
        if _font is not None:
            return _font
        try:
            _font = ImageFont.truetype(DEFAULT_FONT_PATH, DEFAULT_FONT_SIZE_PT)
        except Exception:
            _font = ImageFont.load_default()
        return _font

def _clamp01(t: float) -> float:
    return 0.0 if t < 0 else (1.0 if t > 1 else t)

def color_from_value(value: float, vmin: float, vmax: float, *, alpha: int = 220, palette: str = "gyr") -> Tuple[int,int,int,int]:
    """
    Map a numeric value to RGBA. palette="gyr": green→yellow→red.
    """
    if vmax <= vmin:
        vmax = vmin + 1.0
    t = _clamp01((value - vmin) / (vmax - vmin))
    if t <= 0.5:
        u = t / 0.5
        r = int(0 + (230 - 0) * u)
        g = int(180 + (200 - 180) * u)
        b = 0
    else:
        u = (t - 0.5) / 0.5
        r = 230
        g = int(200 + (40 - 200) * u)
        b = int(0 + (30 - 0) * u)
    return (r, g, b, max(0, min(255, alpha)))

def image_to_png_bytes(img: Image.Image) -> bytes:
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()

def make_cache_key(*parts: Any) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p if isinstance(p, (bytes, bytearray)) else str(p).encode("utf-8", "ignore"))
    return h.hexdigest()[:16]

# -------------------- Parsing --------------------

def clean_label(label: str) -> str:
    """Remove a trailing coordinate triplet from the label (e.g., "123` 178` 015" or "(123, 178, 15)")."""
    s = label.strip()
    # Patterns: backtick-separated, comma-separated, or space-separated triplet at end
    patterns = [
        r"\s*\(?\s*[-+]?\d+[`']\s*[-+]?\d+[`']\s*[-+]?\d+\s*\)?\s*$",
        r"\s*\(?\s*[-+]?\d+\s*,\s*[-+]?\d+\s*,\s*[-+]?\d+\s*\)?\s*$",
        r"\s*[-+]?\d+\s+[-+]?\d+\s+[-+]?\d+\s*$",
    ]
    for pat in patterns:
        s = re.sub(pat, "", s)
    return s.strip()

def parse_eq_file(path: str) -> Dict[str, Any]:
    """
    Parse a file that may contain BOTH:
      P x,y,z, r,g,b, size, Label_Text
      L x1,y1,z1, x2,y2,z2, r,g,b
    Returns {"points": [...], "segments": [...]} with MAP-space coords.
    """
    points: List[Dict[str, Any]] = []
    segs: List[Tuple[float,float,float,float,Tuple[int,int,int]]] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            s = raw.strip()
            if not s or s[0] in ("#", ";"):
                continue
            tag = s[0].upper()
            if tag == "P":
                nums = [float(n) for n in _num_re.findall(s)]
                if len(nums) < 7:   # correct spec: 7 numbers required
                    continue
                x, y, z, r, g, b, size = nums[:7]
                try:
                    label = s.split(",", 7)[-1].strip()
                except Exception:
                    label = ""
                points.append({
                    "xMap": x, "yMap": y, "z": z,
                    "rgb": (int(r), int(g), int(b)),
                    "size": int(size),
                    "label": clean_label(label.replace("_", " ")),
                })
            elif tag == "L":
                nums = [float(n) for n in _num_re.findall(s)]
                if len(nums) < 9:
                    continue
                x1, y1, _z1, x2, y2, _z2, r, g, b = nums[:9]
                segs.append((x1, y1, x2, y2, (int(r), int(g), int(b))))
    return {"points": points, "segments": segs}

# -------------------- Bounds / transforms --------------------

def _compute_bounds_from_file(path: str) -> Tuple[float,float,float,float]:
    """Bounds derived from L segments in the reference file."""
    minX = float("inf"); maxX = float("-inf")
    minY = float("inf"); maxY = float("-inf")
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            s = raw.strip()
            if not s or not s.startswith("L"):
                continue
            nums = [float(n) for n in _num_re.findall(s)]
            if len(nums) < 6:
                continue
            x1, y1, _z1, x2, y2, _z2 = nums[:6]
            minX = min(minX, x1, x2); maxX = max(maxX, x1, x2)
            minY = min(minY, y1, y2); maxY = max(maxY, y1, y2)
    if minX == float("inf"):
        return (0.0, 1.0, 0.0, 1.0)
    return (minX, maxX, minY, maxY)

def get_bounds(ref_map_path: str) -> Tuple[float,float,float,float]:
    with _bounds_lock:
        b = _bounds_cache.get(ref_map_path)
        if b: return b
        b = _compute_bounds_from_file(ref_map_path)
        _bounds_cache[ref_map_path] = b
        return b

def game_to_map_xy(x_game: float, y_game: float) -> Tuple[float, float]:
    # EverQuest convention: map coords are (-Y_game, -X_game)
    return -y_game, -x_game

def _apply_orientation(x_map: float, y_map: float, bounds: Tuple[float,float,float,float], *, flip_x: bool, flip_y: bool) -> Tuple[float, float]:
    minX, maxX, minY, maxY = bounds
    nx, ny = x_map, y_map
    if flip_x:
        nx = maxX - (x_map - minX)
    if flip_y:
        ny = maxY - (y_map - minY)
    return nx, ny

def _scale_for_size(bounds: Tuple[float,float,float,float], width_px: int, height_px: int, padding_px: int) -> Tuple[float, float, float]:
    minX, maxX, minY, maxY = bounds
    w = maxX - minX; h = maxY - minY
    innerW = max(1.0, width_px - 2 * padding_px)
    innerH = max(1.0, height_px - 2 * padding_px)
    sx = innerW / max(1e-9, w)
    sy = innerH / max(1e-9, h)
    scale = min(sx, sy)
    usedW = w * scale; usedH = h * scale
    xPad = (width_px - usedW) / 2.0
    yPad = (height_px - usedH) / 2.0
    return scale, xPad, yPad

def _to_px(x_map: float, y_map: float, bounds: Tuple[float,float,float,float], *, scale: float, x_pad: float, y_pad: float) -> Tuple[int, int]:
    minX, maxX, minY, maxY = bounds
    px = int(round(x_pad + (x_map - minX) * scale))
    py = int(round(y_pad + (maxY - y_map) * scale))  # image Y grows downward
    return px, py

# -------------------- Low-level renderers --------------------

def _render_lines_layer(
    ref_map_path: str,
    segments: List[Tuple[float,float,float,float,Tuple[int,int,int]]],
    width_px: int, height_px: int,
    *,
    line_width_px: int = DEFAULT_LINE_WIDTH_PX,
    line_alpha: int = 255,
    padding_px: int = DEFAULT_PADDING_PX,
    flip_x: bool = DEFAULT_FLIP_X,
    flip_y: bool = DEFAULT_FLIP_Y
) -> Image.Image:
    bounds = get_bounds(ref_map_path)
    scale, xPad, yPad = _scale_for_size(bounds, width_px, height_px, padding_px)
    img = Image.new("RGBA", (width_px, height_px), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")
    a = max(0, min(255, int(line_alpha)))
    for (x1, y1, x2, y2, rgb) in segments:
        X1, Y1 = _apply_orientation(x1, y1, bounds, flip_x=flip_x, flip_y=flip_y)
        X2, Y2 = _apply_orientation(x2, y2, bounds, flip_x=flip_x, flip_y=flip_y)
        p1 = _to_px(X1, Y1, bounds, scale=scale, x_pad=xPad, y_pad=yPad)
        p2 = _to_px(X2, Y2, bounds, scale=scale, x_pad=xPad, y_pad=yPad)
        draw.line([p1, p2], fill=rgb + (a,), width=line_width_px)
    return img

def _render_points_layer(
    ref_map_path: str,
    points: List[Dict[str, Any]],  # expects MAP-space: {xMap, yMap, z?, rgb?, label?, value?}
    width_px: int, height_px: int,
    *,
    style: str = "generic",              # "generic" | "spawn" | "eq"
    marker_mode: Optional[str] = None,   # None -> from style; else "circle" | "arrow" | "auto"
    dot_radius_px: int = DEFAULT_OVERLAY_DOT_RADIUS_PX,
    arrow_size_px: int = DEFAULT_ARROW_SIZE_PX,
    label_field: Optional[str] = None,
    label_fn: Optional[Callable[[Dict[str, Any]], str]] = None,
    color_mode: str = "fixed",           # "fixed" | "z" | "value" | "perPointRGB"
    fixed_color: Tuple[int,int,int,int] = (30,144,255,220),
    value_field: str = "value",
    value_vmin: float = 0.0,
    value_vmax: float = 100.0,
    color_fn: Callable[[float, float, float], Tuple[int,int,int,int]] = color_from_value,
    value_palette: str = "gyr",
    padding_px: int = DEFAULT_PADDING_PX,
    flip_x: bool = DEFAULT_FLIP_X,
    flip_y: bool = DEFAULT_FLIP_Y
) -> Image.Image:
    bounds = get_bounds(ref_map_path)
    scale, xPad, yPad = _scale_for_size(bounds, width_px, height_px, padding_px)
    img = Image.new("RGBA", (width_px, height_px), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")
    font = _get_font()

    # Defaults from style
    eff_marker = marker_mode
    eff_color_mode = color_mode
    if eff_marker is None:
        if style == "spawn":
            eff_marker = "circle"
        elif style == "eq":
            eff_marker = "auto"     # arrow when labeled
            if eff_color_mode == "fixed":
                eff_color_mode = "perPointRGB"
        else:
            eff_marker = "auto"

    def color_for(pt: Dict[str, Any]) -> Tuple[int,int,int,int]:
        if eff_color_mode == "fixed":
            return fixed_color
        if eff_color_mode == "perPointRGB":
            r, g, b = [int(v) for v in pt.get("rgb", (30, 144, 255))]
            return (r, g, b, 220)
        if eff_color_mode == "z":
            z = float(pt.get("z", 0.0))
            t = _clamp01((z + 300.0) / 600.0)
            r = int(40 + 200 * t); g = int(200 - 180 * t); b = int(40 - 20 * t)
            return (r, g, b, 220)
        v = float(pt.get(value_field, 0.0))
        return color_fn(v, value_vmin, value_vmax) if color_fn else color_from_value(v, value_vmin, value_vmax, alpha=220, palette=value_palette)

    def draw_arrow(px: int, py: int, size: int, fill: Tuple[int,int,int,int]) -> None:
        # Down-facing triangle; the apex (px,py) IS the point
        verts = [(px, py), (px - size, py - 2 * size), (px + size, py - 2 * size)]
        draw.polygon(verts, fill=fill, outline=(0, 0, 0, 200))

    for pt in points:
        xm, ym = float(pt["xMap"]), float(pt["yMap"])
        xm, ym = _apply_orientation(xm, ym, bounds, flip_x=flip_x, flip_y=flip_y)
        px, py = _to_px(xm, ym, bounds, scale=scale, x_pad=xPad, y_pad=yPad)

        c = color_for(pt)
        lab = None
        if label_fn is not None:
            lab = label_fn(pt)
        elif label_field:
            lab = str(pt.get(label_field, "")).strip()
        has_label = bool(lab)

        m = eff_marker
        if m == "auto":
            m = "arrow" if has_label and style in ("eq", "generic") else "circle"

        if m == "circle":
            r = int(dot_radius_px)
            draw.ellipse((px - r - 1, py - r - 1, px + r + 1, py + r + 1),
                         outline=(0, 0, 0, 230), width=2)
            draw.ellipse((px - r, py - r, px + r, py + r),
                         fill=c, outline=(0, 0, 0, 180), width=1)
        else:
            draw_arrow(px, py, int(arrow_size_px), c)

        if has_label:
            # Center text ABOVE the arrow tip
            try:
                bbox = font.getbbox(lab)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
            except Exception:
                # Fallback if PIL variant differs
                tw = draw.textlength(lab, font=font)
                th = DEFAULT_FONT_SIZE_PT
            tx = int(px - tw / 2)
            ty = int(py - 2 * arrow_size_px - 2 - th)
            txt_color = (c[0], c[1], c[2], 255) if style == "eq" else (0, 0, 0, 255)
            draw.text((tx, ty), lab, font=font, fill=txt_color)

    return img


def render_file_layers(
    ref_map_path: str,     # reference file for bounds/orientation
    file_path: str,        # file to interpret (may include P and/or L)
    width_px: int,
    height_px: int,
    *,
    # line options
    line_width_px: int = DEFAULT_LINE_WIDTH_PX,
    line_alpha: int = 255,
    # point options
    style: str = "eq",
    marker_mode: Optional[str] = None,
    dot_radius_px: int = DEFAULT_OVERLAY_DOT_RADIUS_PX,
    arrow_size_px: int = DEFAULT_ARROW_SIZE_PX,
    label_field: str = "label",
    color_mode: str = "perPointRGB",
    fixed_color: Tuple[int,int,int,int] = (30, 144, 255, 220),
    value_field: str = "value",
    value_vmin: float = 0.0,
    value_vmax: float = 100.0,
    color_fn: Callable[[float, float, float], Tuple[int,int,int,int]] = color_from_value,
    value_palette: str = "gyr",
    # common
    padding_px: int = DEFAULT_PADDING_PX,
    flip_x: bool = DEFAULT_FLIP_X,
    flip_y: bool = DEFAULT_FLIP_Y,
    include_empty_layers: bool = False
) -> Dict[str, Optional[Image.Image]]:
    """
    Render ONE file into TWO transparent layers:
      - "lines":  all L records
      - "points": all P records (omitting out-of-bounds if file != ref)
    Returns {"lines": PIL.Image|None, "points": PIL.Image|None}
    """
    parsed = parse_eq_file(file_path)
    out: Dict[str, Optional[Image.Image]] = {"lines": None, "points": None}

    # Lines layer
    if parsed["segments"]:
        out["lines"] = _render_lines_layer(
            ref_map_path, parsed["segments"], width_px, height_px,
            line_width_px=line_width_px, line_alpha=line_alpha,
            padding_px=padding_px, flip_x=flip_x, flip_y=flip_y
        )
    elif include_empty_layers:
        out["lines"] = Image.new("RGBA", (width_px, height_px), (0, 0, 0, 0))

    # Points layer (with out-of-bounds filtering if not the ref file)
    if parsed["points"]:
        bounds = get_bounds(ref_map_path)
        minX, maxX, minY, maxY = bounds
        mapped_pts_all = [
            {"xMap": p["xMap"], "yMap": p["yMap"], "z": p["z"], "rgb": p["rgb"], "label": p["label"]}
            for p in parsed["points"]
        ]
        mapped_pts: List[Dict[str, Any]] = []
        enforce_bounds = (file_path != ref_map_path)
        if enforce_bounds:
            for p in mapped_pts_all:
                x = p["xMap"]; y = p["yMap"]
                if (minX <= x <= maxX) and (minY <= y <= maxY):
                    mapped_pts.append(p)
                else:
                    logger.warning(
                        "Omitting out-of-bounds point: file=%s x=%.2f y=%.2f label=%s (ref bounds x[%.2f,%.2f] y[%.2f,%.2f])",
                        file_path, x, y, p.get("label", ""), minX, maxX, minY, maxY
                    )
        else:
            mapped_pts = mapped_pts_all

        if mapped_pts:
            out["points"] = _render_points_layer(
                ref_map_path, mapped_pts, width_px, height_px,
                style=style, marker_mode=marker_mode,
                dot_radius_px=dot_radius_px, arrow_size_px=arrow_size_px,
                label_field=label_field, label_fn=None,
                color_mode=color_mode, fixed_color=fixed_color,
                value_field=value_field, value_vmin=value_vmin, value_vmax=value_vmax,
                color_fn=lambda v, vmin, vmax: color_fn(v, vmin, vmax), value_palette=value_palette,
                padding_px=padding_px, flip_x=flip_x, flip_y=flip_y
            )
    elif include_empty_layers:
        out["points"] = Image.new("RGBA", (width_px, height_px), (0, 0, 0, 0))

    return out

def render_files_to_layers(
    ref_map_path: str,
    file_paths: List[str],
    width_px: int,
    height_px: int,
    *,
    include_empty_layers: bool = False,
    **layer_kwargs
) -> List[Tuple[str, str, Image.Image]]:
    """
    For N files (each may mix P+L), return up to 2N layers:
      [ (file_path, "lines", img), (file_path, "points", img), ... ]
    Only returns a layer if it exists (unless include_empty_layers=True).
    """
    results: List[Tuple[str, str, Image.Image]] = []
    for f in file_paths:
        layers = render_file_layers(ref_map_path, f, width_px, height_px,
                                    include_empty_layers=include_empty_layers, **layer_kwargs)
        if layers.get("lines") is not None:
            results.append((f, "lines", layers["lines"]))  # type: ignore
        if layers.get("points") is not None:
            results.append((f, "points", layers["points"]))  # type: ignore
    return results

# -------------------- Spawn overlay (game-space → circles + heat) --------------------

def render_spawn_points_overlay(
    ref_map_path: str,               # bounds/orientation reference
    spawns: List[Dict[str, Any]],
    width_px: int, height_px: int,
    *,
    coords_are_game: bool = True,    # DB spawns usually store game coords
    value_field: str = "chance",     # % or 0..1; adjust vmin/vmax
    value_vmin: float = 0.0,
    value_vmax: float = 100.0,
    value_palette: str = "gyr",
    dot_radius_px: int = DEFAULT_OVERLAY_DOT_RADIUS_PX,
    label_mode: str = "index",       # "index" | "npc" | "custom" | "none"
    label_field: str = "label",
    padding_px: int = DEFAULT_PADDING_PX,
    flip_x: bool = DEFAULT_FLIP_X,
    flip_y: bool = DEFAULT_FLIP_Y
) -> Image.Image:
    # Adapt to MAP-space and render with style="spawn" (circles only)
    mapped: List[Dict[str, Any]] = []
    for i, sp in enumerate(spawns, start=1):
        xg, yg = float(sp["x"]), float(sp["y"])
        if coords_are_game:
            xm, ym = game_to_map_xy(xg, yg)
        else:
            xm, ym = xg, yg
        p: Dict[str, Any] = {"xMap": xm, "yMap": ym}
        if "z" in sp: p["z"] = float(sp["z"])
        if value_field in sp: p["value"] = float(sp[value_field])
        if label_mode == "index":
            p["label"] = str(i)
        elif label_mode == "npc":
            p["label"] = str(sp.get("npc_name", i))
        elif label_mode == "custom":
            p["label"] = str(sp.get(label_field, ""))
        mapped.append(p)

    return _render_points_layer(
        ref_map_path, mapped, width_px, height_px,
        style="spawn", marker_mode=None,
        dot_radius_px=dot_radius_px, arrow_size_px=DEFAULT_ARROW_SIZE_PX,
        label_field=None if label_mode == "none" else "label",
        color_mode="value", fixed_color=(30, 144, 255, 220),
        value_field="value", value_vmin=value_vmin, value_vmax=value_vmax,
        color_fn=lambda v, vmin, vmax: color_from_value(v, vmin, vmax, alpha=220, palette=value_palette),
        padding_px=padding_px, flip_x=flip_x, flip_y=flip_y
    )
