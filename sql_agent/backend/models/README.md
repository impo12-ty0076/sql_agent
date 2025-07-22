# Data Models

This directory contains the data models for the SQL DB LLM Agent system.

## User Models (`user.py`)

The user models define the structure for user data, preferences, and permissions:

- `UserBase`: Base model with common user fields
- `UserCreate`: Model for creating new users
- `UserLogin`: Model for user login credentials
- `UserPreferences`: User preferences including theme and results per page
- `DatabasePermission`: Permissions for a specific database
- `UserPermissions`: Collection of database permissions for a user
- `User`: Complete user model with all fields
- `UserResponse`: User model for API responses (without sensitive data)
- `UserUpdate`: Model for updating user information
- `TokenData`: Model for JWT token data
- `Token`: Model for authentication token response

## Authentication Models (`auth.py`)

The authentication models handle login, session management, and security:

- `AuthMethod`: Supported authentication methods
- `LoginRequest`: Model for login requests
- `LoginResponse`: Model for login responses
- `RefreshTokenRequest`: Model for token refresh requests
- `LogoutRequest`: Model for logout requests
- `SessionInfo`: Information about user sessions
- `MFASetupResponse`: Response for MFA setup
- `MFAVerifyRequest`: Request for MFA verification
- `PasswordResetRequest`: Request for password reset
- `PasswordResetConfirmRequest`: Confirmation for password reset
- `SecurityAuditLog`: Logging for security events

## Role-Based Access Control Models (`rbac.py`)

The RBAC models provide fine-grained access control:

- `Permission`: System permissions enum
- `ResourceType`: Types of resources that can have permissions
- `PolicyEffect`: Policy effect types (allow/deny)
- `ResourcePolicy`: Policy for a specific resource
- `Role`: Role definition with associated permissions
- `RoleAssignment`: Association between a user and a role
- `AccessControlList`: Access control list for a specific resource
- `PermissionCheck`: Model for permission check requests

## Database Models (`database.py`)

The database models define the structure for database connections and schema information:

- `DBType`: Supported database types (MS-SQL, SAP HANA)
- `ConnectionConfig`: Database connection configuration
- `Column`: Database column definition
- `ForeignKey`: Foreign key relationship between tables
- `Table`: Database table definition
- `Schema`: Database schema containing tables
- `DatabaseSchema`: Complete database schema information
- `Database`: Database connection information and metadata

## Query and Result Models (`query.py`)

The query and result models define the structure for queries, results, and reports:

- `QueryStatus`: Status of a query execution (pending, executing, completed, failed, cancelled)
- `VisualizationType`: Types of visualizations supported in reports
- `ResultColumn`: Column definition in query results
- `Query`: Model representing a user query, including both natural language and SQL forms
- `QueryCreate`: Model for creating a new query
- `QueryUpdate`: Model for updating an existing query
- `QueryResult`: Model representing the result of a query execution
- `QueryResultCreate`: Model for creating a new query result
- `Visualization`: Model representing a data visualization in a report
- `Report`: Model representing an analysis report generated from query results
- `ReportCreate`: Model for creating a new report
- `QueryHistory`: Model representing a saved query in the user's history
- `SharedQuery`: Model representing a query shared with other users

## Usage

These models are used throughout the application for:

1. User registration and authentication
2. Managing user preferences and permissions
3. Controlling access to databases and features
4. Securing API endpoints
5. Auditing security events
6. Database connection and schema management
7. Query execution and result processing
8. Report generation and visualization
9. Query history and sharing

## Implementation Notes

- All models use Pydantic for validation
- Enums are used for fields with fixed values
- Sensitive data like passwords are never returned in responses
- JWT tokens are used for authentication
- Role-based access control is implemented for fine-grained permissions
- Validators ensure data integrity and consistency