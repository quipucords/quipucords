import { combineReducers } from 'redux';

import aboutReducer from './aboutReducer';
import credentialsReducer from './credentialsReducer';
import factsReducer from './factsReducer';
import navigationBarReducer from './navigationBarReducer';
import reportsReducer from './reportsReducer';
import sourcesReducer from './sourcesReducer';
import sourcesToolbarReducer from './sourcesToolbarReducer';
import scansReducer from './scansReducer';
import scansToolbarReducer from './scansToolbarReducer';

const reducers = {
  about: aboutReducer,
  credentials: credentialsReducer,
  facts: factsReducer,
  navigationBar: navigationBarReducer,
  reports: reportsReducer,
  sources: sourcesReducer,
  sourcesToolbar: sourcesToolbarReducer,
  scans: scansReducer,
  scansToolbar: scansToolbarReducer
};

const reduxReducers = combineReducers(reducers);

export { reduxReducers, reducers };

export default reduxReducers;
