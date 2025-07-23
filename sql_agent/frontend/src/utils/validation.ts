/**
 * Validate an email address
 */
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Validate a password meets minimum requirements
 * - At least 8 characters
 * - Contains at least one uppercase letter
 * - Contains at least one lowercase letter
 * - Contains at least one number
 */
export const isValidPassword = (password: string): boolean => {
  if (password.length < 8) return false;
  
  const hasUppercase = /[A-Z]/.test(password);
  const hasLowercase = /[a-z]/.test(password);
  const hasNumber = /[0-9]/.test(password);
  
  return hasUppercase && hasLowercase && hasNumber;
};

/**
 * Get password strength as a number between 0-4
 * 0: Very weak
 * 1: Weak
 * 2: Medium
 * 3: Strong
 * 4: Very strong
 */
export const getPasswordStrength = (password: string): number => {
  let strength = 0;
  
  if (password.length >= 8) strength += 1;
  if (password.length >= 12) strength += 1;
  if (/[A-Z]/.test(password)) strength += 1;
  if (/[a-z]/.test(password)) strength += 1;
  if (/[0-9]/.test(password)) strength += 1;
  if (/[^A-Za-z0-9]/.test(password)) strength += 1;
  
  return Math.min(4, Math.floor(strength / 1.5));
};

/**
 * Validate a URL
 */
export const isValidUrl = (url: string): boolean => {
  try {
    new URL(url);
    return true;
  } catch (e) {
    return false;
  }
};

/**
 * Validate a database connection string
 * This is a simple validation and might need to be adjusted based on specific DB requirements
 */
export const isValidConnectionString = (connectionString: string): boolean => {
  // Basic check for common database connection string formats
  return (
    connectionString.includes('://') && 
    (
      connectionString.startsWith('postgresql://') ||
      connectionString.startsWith('mysql://') ||
      connectionString.startsWith('sqlite://') ||
      connectionString.startsWith('mssql://') ||
      connectionString.startsWith('oracle://') ||
      connectionString.includes('@') ||
      connectionString.includes('/')
    )
  );
};

/**
 * Validate if a string is a valid SQL query
 * This is a very basic check and should be enhanced for production
 */
export const isValidSqlQuery = (query: string): boolean => {
  // Basic check for common SQL keywords
  const sqlKeywords = [
    'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE',
    'CREATE', 'ALTER', 'DROP', 'TRUNCATE', 'JOIN', 'GROUP BY',
    'ORDER BY', 'HAVING', 'LIMIT'
  ];
  
  const upperQuery = query.toUpperCase();
  return sqlKeywords.some(keyword => upperQuery.includes(keyword));
};