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
      webpackConfig.resolve.extensionAlias[".js"] = [
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
      ];

      // Add resolver for MUI packages
      webpackConfig.resolve.alias = {
        ...webpackConfig.resolve.alias,
        "@mui/material": "@mui/material/index.js",
        "@mui/system": "@mui/system/index.js",
        "@mui/base": "@mui/base/index.js",
      };

      return webpackConfig;
    },
  },
};
