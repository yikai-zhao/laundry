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

export interface Photo {
  id: string;
  file_path: string;
  original_filename: string;
}

export interface Issue {
  id: string;
  issue_type: string;
  severity_level: number;
  position_desc: string;
  source: string;
  confidence_score: number | null;
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

export interface Confirmation {
  id: string;
  token: string;
  status: string;
  customer_name: string | null;
  confirmed_at: string | null;
  signature: { signature_data: string } | null;
}

export interface Order {
  id: string;
  customer_id: string;
  status: string;
  note: string | null;
  created_at: string;
  customer: Customer;
  items: OrderItem[];
  confirmation: Confirmation | null;
}
