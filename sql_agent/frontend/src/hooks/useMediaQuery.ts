import { useEffect, useState } from 'react';

/**
 * Custom hook for responsive design using media queries
 * @param query The media query string
 */
function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia(query);

    // Set initial value
    setMatches(mediaQuery.matches);

    // Create event listener
    const handler = (event: MediaQueryListEvent) => setMatches(event.matches);

    // Add event listener
    mediaQuery.addEventListener('change', handler);

    // Remove event listener on cleanup
    return () => mediaQuery.removeEventListener('change', handler);
  }, [query]);

  return matches;
}

// Predefined media queries for common breakpoints
export const useIsMobile = () => useMediaQuery('(max-width: 600px)');
export const useIsTablet = () => useMediaQuery('(min-width: 601px) and (max-width: 960px)');
export const useIsDesktop = () => useMediaQuery('(min-width: 961px)');

export default useMediaQuery;
