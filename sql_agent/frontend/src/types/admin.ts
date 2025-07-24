// Admin types for user and policy management

export interface User {
  id: string;
  username: string;
  email: string;
  role: 'user' | 'admin';
  lastLogin: Date;
  createdAt: Date;
  updatedAt: Date;
  status: 'active' | 'inactive' | 'suspended';
  permissions: UserPermissions;
}

export interface UserPermissions {
  allowedDatabases: DatabasePermission[];
}

export interface DatabasePermission {
  dbId: string;
  dbType: 'mssql' | 'hana';
  allowedSchemas: string[];
  allowedTables: string[];
}

export interface Policy {
  id: string;
  name: string;
  description: string;
  settings: PolicySettings;
  createdAt: Date;
  updatedAt: Date;
  appliedToUsers: number;
}

export interface PolicySettings {
  maxQueriesPerDay: number;
  maxQueryExecutionTime: number; // in seconds
  maxResultSize: number; // in rows
  allowedQueryTypes: string[];
  blockedKeywords: string[];
}

export interface UserFilter {
  role?: 'user' | 'admin';
  status?: 'active' | 'inactive' | 'suspended';
  searchTerm?: string;
}

export interface PolicyFilter {
  searchTerm?: string;
}

export interface Database {
  id: string;
  name: string;
  type: 'mssql' | 'hana';
  host: string;
  schemas: Schema[];
}

export interface Schema {
  name: string;
  tables: Table[];
}

export interface Table {
  name: string;
}
