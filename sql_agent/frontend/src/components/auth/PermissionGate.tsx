import React from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';

interface PermissionGateProps {
  /**
   * The children to render if the user has permission
   */
  children: React.ReactNode;

  /**
   * If true, only admins can see the children
   */
  adminOnly?: boolean;

  /**
   * If provided, only users with access to this database can see the children
   */
  requiredDbId?: string;

  /**
   * If true, only authenticated users can see the children
   */
  requireAuth?: boolean;

  /**
   * Optional fallback component to render if permission is denied
   */
  fallback?: React.ReactNode;
}

/**
 * A component that conditionally renders its children based on user permissions
 */
const PermissionGate: React.FC<PermissionGateProps> = ({
  children,
  adminOnly = false,
  requiredDbId,
  requireAuth = true,
  fallback = null,
}) => {
  const { isAuthenticated, user } = useSelector((state: RootState) => state.auth);

  // Check if user is authenticated when required
  if (requireAuth && !isAuthenticated) {
    return <>{fallback}</>;
  }

  // Check if admin role is required
  if (adminOnly && user?.role !== 'admin') {
    return <>{fallback}</>;
  }

  // Check if specific database access is required
  if (requiredDbId && user) {
    const hasDbAccess = user.permissions?.allowedDatabases?.some(db => db.dbId === requiredDbId);

    if (!hasDbAccess) {
      return <>{fallback}</>;
    }
  }

  // All checks passed, render children
  return <>{children}</>;
};

export default PermissionGate;
