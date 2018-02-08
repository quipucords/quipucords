import * as aboutTypes from './aboutConstants';
import * as credentialsTypes from './credentialsConstants';
import * as factsTypes from './factsConstants';
import * as navigationBarTypes from './navigationBarConstants';
import * as reportsTypes from './reportsConstants';
import * as scansTypes from './scansConstants';
import * as sourcesTypes from './sourcesConstants';
import * as toastNotificationTypes from './toasNotificationConstants';
import * as viewTypes from './viewConstants';
import * as viewToolbarTypes from './viewToolbarConstants';
import * as confirmationModalTypes from './confirmationModalConstants';

const reduxTypes = {
  about: aboutTypes,
  credentials: credentialsTypes,
  facts: factsTypes,
  navigation: navigationBarTypes,
  reports: reportsTypes,
  scans: scansTypes,
  sources: sourcesTypes,
  toastNotifications: toastNotificationTypes,
  view: viewTypes,
  viewToolbar: viewToolbarTypes,
  confirmationModal: confirmationModalTypes
};

export {
  reduxTypes,
  aboutTypes,
  credentialsTypes,
  factsTypes,
  navigationBarTypes,
  reportsTypes,
  scansTypes,
  sourcesTypes,
  toastNotificationTypes,
  viewTypes,
  viewToolbarTypes,
  confirmationModalTypes
};

export default reduxTypes;
