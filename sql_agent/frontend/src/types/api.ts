// API Response Types
export interface TagsResponse {
  tags: string[];
}

export interface ShareLinkResponse {
  share_link: string;
  expires_at?: string;
}

export interface QueryDetailsResponse {
  id: string;
  natural_language?: string;
  generated_sql?: string;
  result?: any;
  created_at: string;
  updated_at: string;
}
