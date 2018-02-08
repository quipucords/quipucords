import { combineReducers } from 'redux';

import aboutReducer from './aboutReducer';
import credentialsReducer from './credentialsReducer';
import factsReducer from './factsReducer';
import navigationBarReducer from './navigationBarReducer';
import reportsReducer from './reportsReducer';
import sourcesReducer from './sourcesReducer';
import scansReducer from './scansReducer';
import toastNotificationsReducer from './toastNotificationsReducer';
import toolbarsReducer from './toolbarsReducer';
import confirmationModalReducer from './confirmationModalReducer';

const reducers = {
  about: aboutReducer,
  credentials: credentialsReducer,
  facts: factsReducer,
  navigationBar: navigationBarReducer,
  reports: reportsReducer,
  sources: sourcesReducer,
  scans: scansReducer,
  toastNotifications: toastNotificationsReducer,
  toolbars: toolbarsReducer,
  confirmationModal: confirmationModalReducer
};

const reduxReducers = combineReducers(reducers);

export { reduxReducers, reducers };

export default reduxReducers;
