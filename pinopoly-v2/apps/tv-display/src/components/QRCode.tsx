import { useEffect, useRef } from 'react';

interface QRCodeProps {
  url: string;
  size?: number;
}

export function QRCode({ url, size = 200 }: QRCodeProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    // Simple QR code placeholder - in production, use a library like 'qrcode'
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // For now, display a placeholder pattern
    // In production, integrate with qrcode library
    const moduleSize = Math.floor(size / 25);

    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, size, size);

    ctx.fillStyle = 'black';

    // Generate simple pattern based on URL hash
    const hash = simpleHash(url);
    for (let y = 0; y < 25; y++) {
      for (let x = 0; x < 25; x++) {
        // Keep finder patterns in corners
        if (isFinderPattern(x, y)) {
          ctx.fillRect(x * moduleSize, y * moduleSize, moduleSize, moduleSize);
        } else if (shouldFillModule(x, y, hash)) {
          ctx.fillRect(x * moduleSize, y * moduleSize, moduleSize, moduleSize);
        }
      }
    }
  }, [url, size]);

  return (
    <canvas
      ref={canvasRef}
      width={size}
      height={size}
      className="rounded"
    />
  );
}

function simpleHash(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return Math.abs(hash);
}

function isFinderPattern(x: number, y: number): boolean {
  // Top-left finder
  if (x < 7 && y < 7) {
    if (x === 0 || x === 6 || y === 0 || y === 6) return true;
    if (x >= 2 && x <= 4 && y >= 2 && y <= 4) return true;
    return false;
  }

  // Top-right finder
  if (x >= 18 && y < 7) {
    const nx = x - 18;
    if (nx === 0 || nx === 6 || y === 0 || y === 6) return true;
    if (nx >= 2 && nx <= 4 && y >= 2 && y <= 4) return true;
    return false;
  }

  // Bottom-left finder
  if (x < 7 && y >= 18) {
    const ny = y - 18;
    if (x === 0 || x === 6 || ny === 0 || ny === 6) return true;
    if (x >= 2 && x <= 4 && ny >= 2 && ny <= 4) return true;
    return false;
  }

  return false;
}

function shouldFillModule(x: number, y: number, hash: number): boolean {
  // Skip quiet zone around finders
  if ((x < 9 && y < 9) || (x >= 16 && y < 9) || (x < 9 && y >= 16)) {
    return false;
  }

  // Use hash to determine pattern
  const index = y * 25 + x;
  return ((hash >> (index % 30)) & 1) === 1;
}
