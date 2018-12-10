const path = require('path');
const WriteFilePlugin = require('write-file-webpack-plugin');

/**
 * Extend Create-React-App webpack configuration.
 * @param config
 * @param env
 * @returns {Object}
 */
const webpack = (config, env) => {
  const newConfig = { ...config };

  // extended props
  if (Array.isArray(newConfig.plugins)) {
    newConfig.plugins.push(new WriteFilePlugin());
  }

  if (newConfig.output) {
    newConfig.output.path = path.join(__dirname, './build');
  }

  return newConfig;
};

/**
 * Extend the Create-React-App Jest configuration.
 * @param config
 * @returns {Object}
 */
const jest = config => {
  const newConfig = { ...config };

  // extended props

  return newConfig;
};

/**
 * Extend the Create-React-App webpack dev server configuration during development.
 * @param configFunction
 * @returns {Function}
 */
const devServer = configFunction => (proxy, allowedHost) => {
  const newConfig = configFunction(proxy, allowedHost);

  // extended props

  return newConfig;
};

module.exports = { webpack, jest, devServer };
