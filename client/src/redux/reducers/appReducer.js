import { combineReducers } from 'redux';

import navigationBarReducer from './navigationBarReducer';
import credentialsReducer from './credentialsReducer';
import sourcesReducer from './sourcesReducer';
import sourcesToolbarReducer from './sourcesToolbarReducer';
import scansReducer from './scansReducer';
import scansToolbarReducer from './scansToolbarReducer';

const appReducer = combineReducers({
  navigationBar: navigationBarReducer,
  credentials: credentialsReducer,
  sources: sourcesReducer,
  sourcesToolbar: sourcesToolbarReducer,
  scans: scansReducer,
  scansToolbar: scansToolbarReducer
});

export default appReducer;
