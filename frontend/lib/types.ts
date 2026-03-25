// AuthMe matches JWT payload EXACTLY -- flat, no .user wrapper
export interface AuthMe {
  sub: string;
  user_id: string;
  email: string;
  name: string;
  role_id: string;
  role_name: string;
  permissions: string[];
}

export interface User {
  id: string;
  oidc_subject: string;
  email: string;
  display_name: string;
  is_active: boolean;
  role_id: string;
  role_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  is_system: boolean;
  created_at: string;
  updated_at: string;
}

export interface Permission {
  id: string;
  resource: string;
  action: string;
  description: string | null;
}

export interface RoleWithPermissions extends Role {
  permissions: Permission[];
}

// Domain types

export interface RFC {
  id: string;
  rfc_number: number;
  title: string;
  summary: string | null;
  rfc_type: string;
  status: string;
  author_id: string;
  author_name: string | null;
  jira_epic_key: string | null;
  sections: RFCSection[];
  created_at: string;
  updated_at: string;
}

export interface RFCListItem {
  id: string;
  rfc_number: number;
  title: string;
  summary: string | null;
  rfc_type: string;
  status: string;
  author_id: string;
  author_name: string | null;
  jira_epic_key: string | null;
  comment_count: number;
  review_count: number;
  created_at: string;
  updated_at: string;
}

export interface RFCSection {
  id: string;
  rfc_id: string;
  title: string;
  content: string | null;
  section_type: string;
  order: number;
  created_at: string;
  updated_at: string;
}

export interface Comment {
  id: string;
  rfc_id: string;
  section_id: string | null;
  author_id: string;
  author_name: string | null;
  content: string;
  parent_id: string | null;
  quoted_text: string | null;
  anchor_offset: number | null;
  anchor_length: number | null;
  is_resolved: boolean;
  resolved_by: string | null;
  resolved_by_name: string | null;
  resolved_at: string | null;
  replies: Comment[];
  references: Reference[];
  created_at: string;
  updated_at: string;
}

export interface Reference {
  id: string;
  comment_id: string;
  url: string;
  title: string;
  ref_type: string;
  created_at: string;
}

export interface ReviewAssignment {
  id: string;
  rfc_id: string;
  section_id: string | null;
  reviewer_id: string;
  reviewer_name: string | null;
  team: string;
  status: string;
  deadline: string | null;
  jira_task_key: string | null;
  created_at: string;
  updated_at: string;
}

export interface SignOff {
  id: string;
  rfc_id: string;
  signer_id: string;
  signer_name: string | null;
  team: string;
  status: string;
  comment: string | null;
  signed_at: string | null;
  created_at: string;
}

// Settings types

export interface AppSetting {
  id: string;
  key: string;
  value: string | null;
  group_name: string;
  display_name: string;
  description: string | null;
  value_type: string;
  is_sensitive: boolean;
  requires_restart: boolean;
  updated_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface AppSettingAuditLog {
  id: string;
  setting_id: string;
  old_value: string | null;
  new_value: string | null;
  changed_by: string;
  created_at: string;
}

// AI types

export interface AIConversation {
  id: string;
  rfc_id: string;
  rfc_type: string;
  messages_json: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface AIResponse {
  message: string;
  conversation_id: string | null;
  rfc_id: string | null;
  sections_generated: boolean;
  // Interview progress metadata
  topics_covered: string[] | null;
  topics_total: number | null;
  current_topic: string | null;
}
