export interface Photo {
  id: string;
  file_path: string;
  original_filename: string;
  photo_label: string | null;
  annotated_file_path: string | null;
}

export interface Issue {
  id: string;
  issue_type: string;
  severity_level: number;
  position_desc: string;
  source: string;
  confidence_score: number | null;
  bbox_x: number | null;
  bbox_y: number | null;
  bbox_w: number | null;
  bbox_h: number | null;
}

export interface Inspection {
  id: string;
  status: string;
  issues: Issue[];
}

export interface OrderItem {
  id: string;
  garment_type: string;
  color: string | null;
  brand: string | null;
  photos: Photo[];
  inspection: Inspection | null;
}

export interface ConfirmationData {
  token: string;
  status: string;
  customer_name: string | null;
  order: {
    id: string;
    note: string | null;
    created_at: string;
    customer: { name: string; phone: string | null };
    items: OrderItem[];
  };
}
