import credentialsSelectors from './credentialsSelectors';
import sourcesSelectors from './sourcesSelectors';

const reduxSelectors = {
  credentials: credentialsSelectors,
  sources: sourcesSelectors
};

export { reduxSelectors as default, reduxSelectors, credentialsSelectors, sourcesSelectors };
