import { combineReducers } from 'redux';

import aboutReducer from './aboutReducer';
import credentialsReducer from './credentialsReducer';
import credentialsToolbarReducer from './credentialsToolbarReducer';
import factsReducer from './factsReducer';
import navigationBarReducer from './navigationBarReducer';
import reportsReducer from './reportsReducer';
import sourcesReducer from './sourcesReducer';
import sourcesToolbarReducer from './sourcesToolbarReducer';
import scansReducer from './scansReducer';
import scansToolbarReducer from './scansToolbarReducer';
import toastNotificationsReducer from './toastNotificationsReducer';

const reducers = {
  about: aboutReducer,
  credentials: credentialsReducer,
  credentialsToolbar: credentialsToolbarReducer,
  facts: factsReducer,
  navigationBar: navigationBarReducer,
  reports: reportsReducer,
  sources: sourcesReducer,
  sourcesToolbar: sourcesToolbarReducer,
  scans: scansReducer,
  scansToolbar: scansToolbarReducer,
  toastNotifications: toastNotificationsReducer
};

const reduxReducers = combineReducers(reducers);

export { reduxReducers, reducers };

export default reduxReducers;
