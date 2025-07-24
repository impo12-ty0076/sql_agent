/**
 * Format a date string to a localized date format
 */
export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString();
};

/**
 * Format a date string to a localized date and time format
 */
export const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleString();
};

/**
 * Format a number to a localized string with thousands separators
 */
export const formatNumber = (num: number): string => {
  return num.toLocaleString();
};

/**
 * Format bytes to a human-readable string (KB, MB, GB, etc.)
 */
export const formatBytes = (bytes: number, decimals = 2): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

/**
 * Format milliseconds to a human-readable duration string
 */
export const formatDuration = (ms: number): string => {
  if (ms < 1000) {
    return `${ms}ms`;
  }

  const seconds = Math.floor(ms / 1000);
  if (seconds < 60) {
    return `${seconds}s`;
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  if (minutes < 60) {
    return `${minutes}m ${remainingSeconds}s`;
  }

  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return `${hours}h ${remainingMinutes}m ${remainingSeconds}s`;
};

/**
 * Truncate a string to a maximum length and add ellipsis if needed
 */
export const truncateString = (str: string, maxLength: number): string => {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength) + '...';
};

/**
 * Convert a camelCase string to Title Case
 */
export const camelToTitleCase = (camelCase: string): string => {
  return camelCase.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase());
};

/**
 * Format SQL query with proper indentation
 * This is a simple formatter and might not handle all SQL syntax correctly
 */
export const formatSqlQuery = (sql: string): string => {
  // This is a very basic formatter
  // For production, consider using a dedicated SQL formatter library
  return sql
    .replace(/\s+/g, ' ')
    .replace(/\s*,\s*/g, ', ')
    .replace(/\s*;\s*/g, ';\n')
    .replace(/\s*(\()\s*/g, ' $1')
    .replace(/\s*(\))\s*/g, '$1 ')
    .replace(
      /\b(SELECT|FROM|WHERE|GROUP BY|HAVING|ORDER BY|LIMIT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|TRUNCATE)\b/gi,
      '\n$1'
    )
    .replace(/\b(INNER|LEFT|RIGHT|OUTER|CROSS|JOIN|ON|AND|OR)\b/gi, '\n  $1');
};
