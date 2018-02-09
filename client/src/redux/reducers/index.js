import { combineReducers } from 'redux';

import aboutReducer from './aboutReducer';
import credentialsReducer from './credentialsReducer';
import factsReducer from './factsReducer';
import navigationBarReducer from './navigationBarReducer';
import reportsReducer from './reportsReducer';
import sourcesReducer from './sourcesReducer';
import scansReducer from './scansReducer';
import toastNotificationsReducer from './toastNotificationsReducer';
import confirmationModalReducer from './confirmationModalReducer';
import viewOptionsReducer from './viewOptionsReducer';

const reducers = {
  about: aboutReducer,
  credentials: credentialsReducer,
  facts: factsReducer,
  navigationBar: navigationBarReducer,
  reports: reportsReducer,
  sources: sourcesReducer,
  scans: scansReducer,
  toastNotifications: toastNotificationsReducer,
  confirmationModal: confirmationModalReducer,
  viewOptions: viewOptionsReducer
};

const reduxReducers = combineReducers(reducers);

export { reduxReducers, reducers };

export default reduxReducers;
