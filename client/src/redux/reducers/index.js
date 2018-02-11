import { combineReducers } from 'redux';

import aboutReducer from './aboutReducer';
import addSourceWizardReducer from './addSourceWizardReducer';
import credentialsReducer from './credentialsReducer';
import factsReducer from './factsReducer';
import navigationBarReducer from './navigationBarReducer';
import reportsReducer from './reportsReducer';
import sourcesReducer from './sourcesReducer';
import scansReducer from './scansReducer';
import toastNotificationsReducer from './toastNotificationsReducer';
import confirmationModalReducer from './confirmationModalReducer';
import viewOptionsReducer from './viewOptionsReducer';
import userReducer from './userReducer';

const reducers = {
  about: aboutReducer,
  addSourceWizard: addSourceWizardReducer,
  credentials: credentialsReducer,
  facts: factsReducer,
  navigationBar: navigationBarReducer,
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
