export interface User {
  id: string;
  username: string;
  role: string;
  display_name: string;
}

export interface Customer {
  id: string;
  name: string;
  phone: string | null;
  email: string | null;
  created_at: string;
}

export interface PhotoQuality {
  ok: boolean;
  blur_score: number;
  brightness: number;
  width: number;
  height: number;
  warnings: string[];
}

export interface Photo {
  id: string;
  order_item_id: string;
  file_path: string;
  original_filename: string;
  photo_label: string | null;
  annotated_file_path: string | null;
  created_at: string;
  quality?: PhotoQuality;
}

export interface Issue {
  id: string;
  inspection_id: string;
  issue_type: string;
  severity_level: number;
  position_desc: string;
  confidence_score: number | null;
  source: string;
  bbox_x: number | null;
  bbox_y: number | null;
  bbox_w: number | null;
  bbox_h: number | null;
  created_at: string;
  updated_at: string | null;
}

export interface Inspection {
  id: string;
  order_item_id: string;
  status: string;
  issues: Issue[];
  inspector: User | null;
  created_at: string;
  updated_at: string | null;
}

export interface OrderItem {
  id: string;
  order_id: string;
  garment_type: string;
  color: string | null;
  brand: string | null;
  note: string | null;
  unit_price: number;
  service_type: string;
  fabric_type: string | null;
  has_lining: boolean;
  photos: Photo[];
  inspection: Inspection | null;
  created_at: string;
}

export interface Confirmation {
  id: string;
  order_id: string;
  token: string;
  status: string;
  customer_name: string | null;
  created_at: string;
  confirmed_at: string | null;
  signature: { id: string; signature_data: string; created_at: string } | null;
}

export interface Order {
  id: string;
  customer_id: string;
  status: string;
  note: string | null;
  pickup_type: string;
  payment_method: string | null;
  payment_status: string;
  discount_amount: number;
  subtotal: number;
  total_price: number;
  created_at: string;
  updated_at: string | null;
  customer: Customer;
  items: OrderItem[];
  confirmation: Confirmation | null;
}
