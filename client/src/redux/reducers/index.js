import { combineReducers } from 'redux';

import addSourceWizardReducer from './addSourceWizardReducer';
import credentialsReducer from './credentialsReducer';
import factsReducer from './factsReducer';
import reportsReducer from './reportsReducer';
import sourcesReducer from './sourcesReducer';
import scansReducer from './scansReducer';
import toastNotificationsReducer from './toastNotificationsReducer';
import confirmationModalReducer from './confirmationModalReducer';
import viewOptionsReducer from './viewOptionsReducer';
import userReducer from './userReducer';

const reducers = {
  addSourceWizard: addSourceWizardReducer,
  credentials: credentialsReducer,
  facts: factsReducer,
  reports: reportsReducer,
  sources: sourcesReducer,
  scans: scansReducer,
  toastNotifications: toastNotificationsReducer,
  confirmationModal: confirmationModalReducer,
  viewOptions: viewOptionsReducer,
  user: userReducer
};

const reduxReducers = combineReducers(reducers);

export { reduxReducers, reducers };

export default reduxReducers;
