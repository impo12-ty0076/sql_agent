module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      // Add resolver fallbacks for Material UI imports
      if (!webpackConfig.resolve) {
        webpackConfig.resolve = {};
      }
      
      if (!webpackConfig.resolve.fallback) {
        webpackConfig.resolve.fallback = {};
      }
      
      // Add resolver for module extensions
      if (!webpackConfig.resolve.extensionAlias) {
        webpackConfig.resolve.extensionAlias = {};
      }
      webpackConfig.resolve.extensionAlias['.js'] = ['.js', '.jsx', '.ts', '.tsx'];
      
      // Enhanced resolver for MUI packages and their submodules
      webpackConfig.resolve.alias = {
        ...webpackConfig.resolve.alias,
        '@mui/material': '@mui/material/index.js',
        '@mui/material/styles': '@mui/material/styles/index.js',
        '@mui/material/Typography': '@mui/material/Typography/index.js',
        '@mui/material/Fade': '@mui/material/Fade/index.js',
        '@mui/material/useMediaQuery': '@mui/material/useMediaQuery/index.js',
        '@mui/system': '@mui/system/index.js',
        '@mui/system/RtlProvider': '@mui/system/RtlProvider/index.js',
        '@mui/base': '@mui/base/index.js',
      };
      
      return webpackConfig;
    },
  },
};