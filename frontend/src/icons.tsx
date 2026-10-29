// Thin line icons (inline SVG, 24x24 grid, stroke = currentColor) used instead of emoji.
import type { ReactNode } from "react";

/** Wrap path elements in a consistent stroked SVG. */
function Svg({ children, size = 22 }: { children: ReactNode; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.4}
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{children}</svg>
  );
}

export const HomeIcon = () => <Svg><path d="M3 10.5 12 3l9 7.5" /><path d="M5.5 9v11h13V9" /><path d="M10 20v-6h4v6" /></Svg>;
export const CameraIcon = () => <Svg><path d="M4 7.5h3.2L9 5h6l1.8 2.5H20v11.5H4z" /><circle cx="12" cy="13" r="3.6" /></Svg>;
export const TrophyIcon = () => <Svg><path d="M8 4h8v5a4 4 0 0 1-8 0z" /><path d="M8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4" /><path d="M12 13v4M9 20h6M10 17h4" /></Svg>;
export const MapIcon = () => <Svg><path d="M9 4 3.5 6v14L9 18l6 2 5.5-2V4L15 6z" /><path d="M9 4v14M15 6v14" /></Svg>;
export const GearIcon = () => <Svg size={20}><path d="M4 7h10M18 7h2M4 17h4M12 17h8" /><circle cx="16" cy="7" r="2" /><circle cx="10" cy="17" r="2" /></Svg>;
export const LeafIcon = () => <Svg size={26}><path d="M5 19c0-8 5-13 14-14-1 9-6 14-14 14z" /><path d="M5 19 13 11" /></Svg>;
export const RecycleIcon = () => <Svg size={26}><path d="M4.5 7h15M9.5 7V4.5h5V7" /><path d="M6.5 7l1 13h9l1-13" /><path d="M10 11v5.5M14 11v5.5" /></Svg>;
export const SparkleIcon = () => <Svg size={26}><path d="M12 3v5M12 16v5M3 12h5M16 12h5" /><path d="M7 7l2 2M15 15l2 2M17 7l-2 2M9 15l-2 2" /></Svg>;
export const AlertIcon = () => <Svg size={26}><path d="M12 3.5 21.5 20h-19z" /><path d="M12 10v4.5M12 17.2v.3" /></Svg>;
export const ArrowIcon = () => <Svg size={18}><path d="M5 12h14M13 6l6 6-6 6" /></Svg>;
