import React from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';

interface PermissionGuardProps {
  /**
   * The children to render if the user has the required permissions
   */
  children: React.ReactNode;

  /**
   * Required role to view the content
   */
  requiredRole?: 'user' | 'admin';

  /**
   * Fallback component to render if the user doesn't have the required permissions
   */
  fallback?: React.ReactNode;

  /**
   * Whether to render nothing if the user doesn't have the required permissions
   */
  renderNothing?: boolean;
}

/**
 * A component that conditionally renders its children based on user permissions
 */
const PermissionGuard: React.FC<PermissionGuardProps> = ({
  children,
  requiredRole = 'user',
  fallback = null,
  renderNothing = false,
}) => {
  const { isAuthenticated, user } = useSelector((state: RootState) => state.auth);

  // Check if the user is authenticated
  if (!isAuthenticated || !user) {
    return renderNothing ? null : <>{fallback}</>;
  }

  // Check if the user has the required role
  const hasRequiredRole =
    requiredRole === 'user' || (requiredRole === 'admin' && user.role === 'admin');

  if (!hasRequiredRole) {
    return renderNothing ? null : <>{fallback}</>;
  }

  // User has the required permissions, render the children
  return <>{children}</>;
};

export default PermissionGuard;
