import React from 'react';
import type { Issue } from '../types';

// Color mapping per design doc section 6.2
const ISSUE_COLORS: Record<string, string> = {
  stain: 'rgba(255, 0, 0, 0.8)',       // Red
  hole: 'rgba(0, 0, 255, 0.8)',        // Blue
  tear: 'rgba(0, 0, 255, 0.8)',        // Blue
  wear: 'rgba(255, 200, 0, 0.8)',      // Yellow
  wrinkle: 'rgba(255, 165, 0, 0.8)',   // Orange
  fade: 'rgba(128, 0, 128, 0.8)',      // Purple
  missing_button: 'rgba(0, 128, 0, 0.8)', // Green
  zipper: 'rgba(0, 128, 128, 0.8)',    // Teal
  pilling: 'rgba(255, 165, 0, 0.8)',   // Orange
  other: 'rgba(128, 128, 128, 0.8)',   // Gray
};

const ISSUE_LABELS: Record<string, string> = {
  stain: '污渍', hole: '破洞', tear: '撕裂', wear: '磨损',
  wrinkle: '褶皱', fade: '褪色', missing_button: '缺扣',
  zipper: '拉链', pilling: '起球', other: '其他',
};

interface AnnotatedPhotoProps {
  src: string;
  issues: Issue[];
  className?: string;
  onClick?: () => void;
}

const AnnotatedPhoto: React.FC<AnnotatedPhotoProps> = ({ src, issues, className = '', onClick }) => {
  const issuesWithBbox = issues.filter(
    i => i.bbox_x != null && i.bbox_y != null && i.bbox_w != null && i.bbox_h != null
  );

  return (
    <div className={`relative inline-block ${className}`} onClick={onClick} style={{ cursor: onClick ? 'pointer' : 'default' }}>
      <img src={src} alt="garment" className="w-full h-full object-cover" />
      {issuesWithBbox.map((issue) => {
        const color = ISSUE_COLORS[issue.issue_type] || ISSUE_COLORS.other;
        const label = ISSUE_LABELS[issue.issue_type] || issue.issue_type;
        return (
          <div
            key={issue.id}
            style={{
              position: 'absolute',
              left: `${(issue.bbox_x || 0) * 100}%`,
              top: `${(issue.bbox_y || 0) * 100}%`,
              width: `${(issue.bbox_w || 0) * 100}%`,
              height: `${(issue.bbox_h || 0) * 100}%`,
              border: `2px solid ${color}`,
              boxSizing: 'border-box',
              pointerEvents: 'none',
            }}
          >
            <span
              style={{
                position: 'absolute',
                top: '-18px',
                left: '0',
                backgroundColor: color,
                color: '#fff',
                fontSize: '10px',
                padding: '1px 4px',
                borderRadius: '2px',
                whiteSpace: 'nowrap',
              }}
            >
              {label} S{issue.severity_level}
            </span>
          </div>
        );
      })}
    </div>
  );
};

export default AnnotatedPhoto;
